import streamlit as st
import google.generativeai as genai
import json
import re

# Get API key from Streamlit secrets
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception as e:
    st.error("⚠️ GOOGLE_API_KEY not found in Streamlit secrets! Make sure to add it in the Streamlit Cloud dashboard.")
    st.stop()

# Configure API with error handling
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-1219")  # Keeping the experimental model
except Exception as e:
    st.error(f"⚠️ Error configuring Gemini API: {str(e)}")
    st.stop()

# Streamlit UI
st.title("🤔 Advanced Reasoning Bot")
st.write("This bot uses multiple AI agents to analyze topics in depth with sophisticated reasoning.")

# Input section
topic = st.text_input("What topic should we explore?")
loops = st.slider("How many reasoning iterations per aspect?", min_value=1, max_value=3, value=2)

# Agent Prompts (defined outside the button click for efficiency)
agent1_prompt = """Return ONLY a JSON object analyzing this topic. Do not include any other text or explanation:

Topic: {topic}

Required JSON structure:
{{
    "direct_answer": "A clear, concise answer about {topic}",
    "aspects": {{
        "Question 1?": [
            "Required data point 1",
            "Required data point 2"
        ],
        "Question 2?": [
            "Required data point 1",
            "Required data point 2"
        ],
        "Question 3?": [
            "Required data point 1",
            "Required data point 2"
        ]
    }
}

Using this exact format, create a JSON response for: {topic}

Rules:
1. Output MUST be valid JSON
2. Include exactly 3 questions as aspects
3. Each aspect must have exactly 2 data points
4. Use proper JSON formatting with double quotes
5. No comments or text outside the JSON structure"""

agent2_prompt = """As an Analysis Refiner, your task is to provide detailed information and analysis for one specific aspect in the following framework.

User Input: {topic}

Framework:
{system_prompt}

Current Aspect to Refine: {current_aspect}

Previous Analysis for this Aspect: {previous_analysis}

Based on the suggested data points in the framework, provide detailed information, analysis, and relevant data to answer the current aspect. Build upon the previous analysis, adding more detail, nuance, and supporting evidence. Do NOT repeat information already provided. Focus on adding NEW information and insights."""

agent3_prompt = """As an Expert Response Generator, create a comprehensive, Nobel laureate-level response to the following user input, informed by the detailed analysis provided:

User Input: {topic}

Framework:
{system_prompt}

Detailed Analysis (for each aspect):
{all_aspect_analyses}

Your response should:
1. Provide a clear and authoritative answer to the user's input, directly addressing the question
2. Integrate the key insights and explanations from the analysis of each aspect
3. Demonstrate a deep understanding of the topic
4. Offer nuanced perspectives and potential implications

Write in a sophisticated and insightful manner, as if you were a leading expert in the field."""

agent4_prompt = """As a Concise Overview Generator, provide a simplified, easy-to-understand summary of the following expert response:

User Input: {topic}

Expert Response:
{expert_text}

Your summary should:
1. Capture the main points of the expert response
2. Use clear and simple language
3. Be concise"""

if st.button("Start Analysis"):
    if topic:
        try:
            # Agent 1: Framework Designer
            with st.expander("🎯 Analysis Framework", expanded=True):
                st.write("Agent 1: Designing framework...")
                prompt_response = model.generate_content(
                    agent1_prompt.format(topic=topic),
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        candidate_count=1,
                        stop_sequences=["\n\n"]
                    )
                )

                if hasattr(prompt_response, 'parts'):
                    system_prompt_json = prompt_response.parts[0].text.strip()
                else:
                    system_prompt_json = prompt_response.text.strip()
                
                # Clean up the response
                try:
                    # Find JSON pattern
                    json_pattern = r'\{[^{}]*\}'
                    json_match = re.search(json_pattern, system_prompt_json)
                    
                    if not json_match:
                        st.error("No valid JSON object found in response")
                        st.write("Raw response:", system_prompt_json)
                        st.stop()
                    
                    system_prompt_json = json_match.group()
                    system_prompt = json.loads(system_prompt_json)
                    
                    # Validate JSON structure
                    if not isinstance(system_prompt, dict):
                        st.error("Invalid JSON: Root must be an object")
                        st.stop()
                    if "direct_answer" not in system_prompt or "aspects" not in system_prompt:
                        st.error("Invalid JSON: Missing required fields 'direct_answer' or 'aspects'")
                        st.stop()
                    if not isinstance(system_prompt["aspects"], dict):
                        st.error("Invalid JSON: 'aspects' must be an object")
                        st.stop()
                    if len(system_prompt["aspects"]) != 3:
                        st.error("Invalid JSON: Must have exactly 3 aspects")
                        st.stop()
                    
                    for aspect, data_points in system_prompt["aspects"].items():
                        if not isinstance(data_points, list) or len(data_points) != 2:
                            st.error(f"Invalid JSON: Each aspect must have exactly 2 data points. Error in: {aspect}")
                            st.stop()
                    
                    st.json(system_prompt)
                    
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON syntax: {e}")
                    st.write("Raw response:", system_prompt_json)
                    st.stop()
                except Exception as e:
                    st.error(f"Error processing response: {str(e)}")
                    st.write("Raw response:", system_prompt_json)
                    st.stop()

            # Agent 2: Analysis Refiner
            full_analysis = {}
            for aspect, data_points in system_prompt["aspects"].items():
                previous_analysis = ""
                with st.expander(f"🔄 Refining Aspect: {aspect}", expanded=True):
                    st.write(f"Agent 2: Refining analysis of '{aspect}'...")
                    for i in range(loops):
                        st.write(f"Iteration {i+1}/{loops}")
                        response = model.generate_content(
                            agent2_prompt.format(topic=topic, system_prompt=system_prompt, current_aspect=aspect, previous_analysis=previous_analysis),
                            generation_config=genai.types.GenerationConfig(temperature=0.7)
                        )
                        if hasattr(response, 'parts'):
                            context = response.parts[0].text
                        else:
                            context = response.text
                        previous_analysis = context
                        st.write(context)
                full_analysis[aspect] = previous_analysis

            # Agent 3: Expert Response Generator
            with st.expander("📊 Expert Response", expanded=True):
                st.write("Agent 3: Generating expert response...")
                analysis_text = ""
                for aspect, analysis in full_analysis.items():
                    analysis_text += f"\n\nAnalysis for {aspect}:\n{analysis}"
                response = model.generate_content(
                    agent3_prompt.format(topic=topic, system_prompt=system_prompt, all_aspect_analyses=analysis_text),
                    generation_config=genai.types.GenerationConfig(temperature=0.7)
                )
                if hasattr(response, 'parts'):
                    expert_text = response.parts[0].text
                else:
                    expert_text = response.text
                st.write(expert_text)

            # Agent 4: Concise Overview Generator
            with st.expander("💡 Simple Explanation", expanded=True):
                st.write("Agent 4: Providing simplified overview...")
                response = model.generate_content(
                    agent4_prompt.format(topic=topic, expert_text=expert_text),
                    generation_config=genai.types.GenerationConfig(temperature=0.3)
                )
                if hasattr(response, 'parts'):
                    overview_text = response.parts[0].text
                else:
                    overview_text = response.text
                st.write(overview_text)

        except Exception as e:
            st.error(f"⚠️ Error during analysis: {str(e)}")
            st.write("Debug info:")
            st.write(f"API Key status: {'Present' if api_key else 'Missing'}")
            st.write(f"Topic: {topic}")
            st.write(f"Iterations: {loops}")
    else:
        st.warning("Please enter a topic to analyze.")

