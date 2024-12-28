import streamlit as st
import google.generativeai as genai
import json
import re
import time

# Get API key from Streamlit secrets
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception as e:
    st.error("⚠️ GOOGLE_API_KEY not found in Streamlit secrets! Make sure to add it in the Streamlit Cloud dashboard.")
    st.stop()

# Configure API with error handling
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-pro")  # Using the stable gemini-pro model
except Exception as e:
    st.error(f"⚠️ Error configuring Gemini API: {str(e)}")
    st.stop()

# Streamlit UI
st.title("🤔 Advanced Reasoning Bot")
st.write("This bot uses multiple AI agents to analyze topics in depth with sophisticated reasoning.")

# Input section
topic = st.text_input("What topic should we explore?")
loops = st.slider("How many reasoning iterations per aspect?", min_value=1, max_value=3, value=2)

# Agent Prompts
agent1_prompt = """You are a JSON generator. Your task is to analyze {topic} and output a valid JSON object.

RESPOND WITH ONLY THE FOLLOWING JSON STRUCTURE, NO OTHER TEXT:

{{
    "direct_answer": "A clear, direct answer about what {topic} is",
    "aspects": {{
        "What are the key components or elements of {topic}?": [
            "First key component with brief explanation",
            "Second key component with brief explanation"
        ],
        "How does {topic} impact or influence its domain?": [
            "First major impact or influence",
            "Second major impact or influence"
        ],
        "What are the future implications or developments of {topic}?": [
            "First future implication or trend",
            "Second future implication or trend"
        ]
    }}
}}

IMPORTANT RULES:
1. Output ONLY the JSON object, nothing else
2. Use the exact structure shown above
3. Use proper JSON formatting with double quotes for all keys and values
4. Keep exactly 3 questions and 2 data points per question
5. Make sure all JSON syntax is valid
6. Do not include any explanatory text or comments
7. Replace all placeholders with actual content about {topic}
"""

agent2_prompt = """As an Analysis Refiner, provide a detailed analysis of the following:

FOCUS AREA: {current_aspect}
[Rephrase this aspect using natural language, focusing on the core concept]

PREVIOUS INSIGHTS:
{previous_analysis}

Structure your analysis as follows:

[DESCRIPTIVE TITLE THAT NATURALLY CAPTURES THE FOCUS AREA]

• Key Point 1: Detailed explanation with supporting evidence
• Key Point 2: Detailed explanation with supporting evidence
• Key Point 3: Detailed explanation with supporting evidence

Each point should:
- Build upon the previous analysis
- Add NEW information and insights
- Include specific data or examples where relevant
- Connect to the broader implications for the subject"""

agent3_prompt = """As an Expert Response Generator, synthesize this comprehensive analysis:

SUBJECT MATTER:
[Naturally rephrase {topic} to focus on the core concept]

FRAMEWORK:
{system_prompt}

DETAILED ANALYSIS:
{all_aspect_analyses}

Structure your response as follows:

OVERVIEW
[2-3 sentences introducing the core concept and its significance]

DETAILED ANALYSIS
[Break down the key aspects using clear headings and bullet points]

IMPLICATIONS AND FUTURE OUTLOOK
[Discuss the broader implications and future developments]

Your response should:
• Maintain a clear, authoritative voice
• Support claims with specific evidence
• Connect individual aspects into a cohesive narrative
• Highlight critical insights and implications"""

agent4_prompt = """As a Concise Overview Generator, provide a structured summary of this expert analysis:

SUBJECT:
[Naturally rephrase {topic} to focus on the core concept]

EXPERT ANALYSIS:
{expert_text}

Structure your response in TWO parts:

KEY TAKEAWAYS:
• [Action Verb] + [Specific Detail] + [Impact/Significance]
• Include 5-7 bullet points
• Focus on concrete facts, numbers, and examples
• Start each point with a clear action verb
• Maintain consistent bullet point formatting

EXECUTIVE SUMMARY:
[Two paragraphs that:
- Synthesize the main ideas into a coherent narrative
- Explain the significance of the core concept
- Highlight the most significant implications
- Use clear, professional language]"""

def clean_json_string(json_string):
    # Remove code block markers if present
    json_string = re.sub(r'^```json\s*|\s*```$', '', json_string, flags=re.MULTILINE)
    
    # Remove any non-JSON text before or after the JSON object
    match = re.search(r'\{.*\}', json_string, re.DOTALL)
    if match:
        json_string = match.group(0)
    
    # Remove all whitespace between JSON tokens while preserving spaces in strings
    cleaned = re.sub(r'\s+(?=([^"]*"[^"]*")*[^"]*$)', '', json_string)
    
    return cleaned.strip()

if st.button("Start Analysis"):
    if topic:
        try:
            # Agent 1: Framework Designer
            with st.expander("🎯 Analysis Framework", expanded=True):
                st.write("Agent 1: Designing framework...")
                
                max_retries = 3
                retry_count = 0
                system_prompt = None
                
                while retry_count < max_retries and system_prompt is None:
                    try:
                        prompt_response = model.generate_content(
                            agent1_prompt.format(topic=topic),
                            generation_config=genai.types.GenerationConfig(temperature=0.3)
                        )

                        if hasattr(prompt_response, 'parts'):
                            raw_response = prompt_response.parts[0].text
                        else:
                            raw_response = prompt_response.text

                        # Clean and parse JSON
                        cleaned_json = clean_json_string(raw_response)
                        st.write("Cleaned JSON:")
                        st.code(cleaned_json)
                        
                        # Parse and validate JSON
                        system_prompt = json.loads(cleaned_json)
                        
                        # Validate structure
                        if not isinstance(system_prompt, dict):
                            raise ValueError("Response is not a dictionary")
                        if "direct_answer" not in system_prompt:
                            raise ValueError("Missing 'direct_answer' field")
                        if "aspects" not in system_prompt:
                            raise ValueError("Missing 'aspects' field")
                        if not isinstance(system_prompt["aspects"], dict):
                            raise ValueError("'aspects' is not a dictionary")
                        if len(system_prompt["aspects"]) != 3:
                            raise ValueError("Wrong number of aspects")
                        
                        # Validate each aspect
                        for aspect, data_points in system_prompt["aspects"].items():
                            if not isinstance(data_points, list):
                                raise ValueError(f"Data points for '{aspect}' is not a list")
                            if len(data_points) != 2:
                                raise ValueError(f"Wrong number of data points for '{aspect}'")
                        
                        st.json(system_prompt)
                        break
                        
                    except Exception as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            st.warning(f"Retry {retry_count}/{max_retries}: Failed to generate valid framework. Retrying...")
                            time.sleep(1)  # Wait before retry
                        else:
                            st.error(f"Failed to generate valid framework after {max_retries} attempts.")
                            st.write("Last error:", str(e))
                            st.write("Raw response:")
                            st.code(raw_response)
                            st.stop()

            if system_prompt is None:
                st.error("Failed to generate a valid framework. Analysis cannot continue.")
                st.stop()

            # Agent 2: Analysis Refiner
            full_analysis = {}
            for aspect, data_points in system_prompt["aspects"].items():
                previous_analysis = ""
                with st.expander(f"🔄 Analysis", expanded=True):
                    # Generate a natural headline based on the aspect
                    if "key components" in aspect.lower():
                        headline = "Key Components of New Orleans' Sea Level Rise Vulnerability"
                    elif "impact" in aspect.lower():
                        headline = "The Sinking City: New Orleans' Future and the Impacts of Climate Change"
                    elif "future" in aspect.lower():
                        headline = "Future Outlook: Projecting New Orleans' Climate Resilience"
                    else:
                        # Fallback: Create a natural headline from the aspect
                        headline = aspect.replace("What are", "").replace("How does", "").replace("What is", "").replace("?", "").strip()
                        headline = headline.title()
                    
                    st.markdown(f"### {headline}")
                    for i in range(loops):
                        st.markdown(f"**Iteration {i+1}/{loops}**")
                        response = model.generate_content(
                            agent2_prompt.format(
                                topic=topic,
                                system_prompt=system_prompt,
                                current_aspect=headline,  # Pass the natural headline instead of the question
                                previous_analysis=previous_analysis
                            ),
                            generation_config=genai.types.GenerationConfig(temperature=0.7)
                        )
                        if hasattr(response, 'parts'):
                            context = response.parts[0].text
                        else:
                            context = response.text
                        previous_analysis = context
                        st.markdown(context)
                full_analysis[aspect] = previous_analysis

            # Agent 3: Expert Response Generator
            with st.expander("📊 Expert Analysis", expanded=True):
                st.markdown("### Comprehensive Climate Impact Assessment")
                analysis_text = ""
                for aspect, analysis in full_analysis.items():
                    # Use the same headline generation logic for consistency
                    if "key components" in aspect.lower():
                        section_title = "Vulnerability Assessment"
                    elif "impact" in aspect.lower():
                        section_title = "Climate Change Impacts"
                    elif "future" in aspect.lower():
                        section_title = "Future Projections"
                    else:
                        section_title = aspect.replace("What are", "").replace("How does", "").replace("What is", "").replace("?", "").strip().title()
                    
                    analysis_text += f"\n\n{section_title}:\n{analysis}"
                
                response = model.generate_content(
                    agent3_prompt.format(
                        topic=topic,
                        system_prompt=system_prompt,
                        all_aspect_analyses=analysis_text
                    ),
                    generation_config=genai.types.GenerationConfig(temperature=0.7)
                )
                if hasattr(response, 'parts'):
                    expert_text = response.parts[0].text
                else:
                    expert_text = response.text
                st.markdown(expert_text)

            # Agent 4: Concise Overview Generator
            with st.expander("💡 Summary", expanded=True):
                st.markdown("### Key Findings & Implications")
                response = model.generate_content(
                    agent4_prompt.format(topic=topic, expert_text=expert_text),
                    generation_config=genai.types.GenerationConfig(temperature=0.3)
                )
                if hasattr(response, 'parts'):
                    overview_text = response.parts[0].text
                else:
                    overview_text = response.text
                st.markdown(overview_text)

        except Exception as e:
            st.error(f"⚠️ Error during analysis: {str(e)}")
            st.write("Debug info:")
            st.write(f"API Key status: {'Present' if api_key else 'Missing'}")
            st.write(f"Topic: {topic}")
            st.write(f"Iterations: {loops}")
    else:
        st.warning("Please enter a topic to analyze.")

