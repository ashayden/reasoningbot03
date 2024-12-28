import streamlit as st
import google.generativeai as genai

# Get API key from Streamlit secrets
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception as e:
    st.error("⚠️ GOOGLE_API_KEY not found in Streamlit secrets! Make sure to add it in the Streamlit Cloud dashboard.")
    st.stop()

# Configure API with error handling
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-1219")
except Exception as e:
    st.error(f"⚠️ Error configuring Gemini API: {str(e)}")
    st.stop()

# Streamlit UI
st.title("🤔 Advanced Reasoning Bot")
st.write("This bot uses multiple AI agents to analyze topics in depth with sophisticated reasoning.")

# Input section
topic = st.text_input("What topic should we explore?")
loops = st.slider("How many reasoning iterations?", min_value=1, max_value=5, value=3)

if st.button("Start Analysis"):
    if topic:
        try:
            # Agent 1: Framework Designer
            # Creates a structured analysis framework for the topic
            with st.expander("🎯 Analysis Framework", expanded=True):
                st.write("Agent 1: Designing analysis framework...")
                prompt_response = model.generate_content(
                    f"""As a Framework Designer, create a comprehensive system prompt for analyzing '{topic}'.
                    Your framework should include:
                    1. Key aspects to examine
                    2. Different perspectives to consider
                    3. Potential implications to explore
                    4. Interconnected elements to analyze
                    5. Specific questions to address
                    
                    Make the framework clear, structured, and actionable for deep analysis.""",
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3
                    )
                )
                if hasattr(prompt_response, 'parts'):
                    system_prompt = prompt_response.parts[0].text
                else:
                    system_prompt = prompt_response.text
                st.write(system_prompt)

            # Agent 2: Analysis Executor
            # Executes the framework through multiple iterations
            full_analysis = []
            context = topic
            for i in range(loops):
                with st.expander(f"🔄 Analysis Iteration {i+1}/{loops}", expanded=True):
                    st.write(f"Agent 2: Executing iteration {i+1}...")
                    response = model.generate_content(
                        f"""As an Analysis Executor, your task is to apply the following analytical framework to the topic:

                        Framework:
                        {system_prompt}

                        Previous Analysis Context: {context}

                        Execute this framework rigorously as if you were a Nobel prize winner in the relevant field, building upon previous insights while maintaining focus on the framework structure. 
                        Provide novel insights and deep analysis for each point in the framework.""",
                        generation_config=genai.types.GenerationConfig(
                            temperature=1.0
                        )
                    )
                    if hasattr(response, 'parts'):
                        context = response.parts[0].text
                    else:
                        context = response.text
                    full_analysis.append(context)
                    st.write(context)

            # Agent 3: Synthesis Expert
            # Synthesizes insights from all iterations
            with st.expander("📊 Final Synthesis", expanded=True):
                st.write("Agent 3: Synthesizing findings...")
                summary = model.generate_content(
                    f"""As a Synthesis Expert, analyze and synthesize the findings from {loops} iterations of analysis on '{topic}'.

                    Analysis Iterations:
                    {' '.join(full_analysis)}

                    Provide:
                    1. Key Insights: Bullet point the most significant findings
                    2. Synthesis: Write a concise paragraph that weaves together the main themes in simple language
                    3. Evolution of Understanding: How did the analysis deepen or change across iterations
                    4. Follow-up Questions:
                       - One question that delves deeper into the most intriguing aspect
                       - One question that explores a related but unexplored area
                       - One question that examines unexpected connections discovered

                    Focus on extracting unique insights and patterns that emerged across iterations.""",
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1
                    )
                )
                if hasattr(summary, 'parts'):
                    summary_text = summary.parts[0].text
                else:
                    summary_text = summary.text
                st.write(summary_text)
        except Exception as e:
            st.error(f"⚠️ Error during analysis: {str(e)}")
            st.write("Debug info:")
            st.write(f"API Key status: {'Present' if api_key else 'Missing'}")
            st.write(f"Topic: {topic}")
            st.write(f"Iterations: {loops}")
    else:
        st.warning("Please enter a topic to analyze.")

