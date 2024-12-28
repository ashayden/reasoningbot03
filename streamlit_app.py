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
            with st.expander("🎯 Analysis Framework", expanded=True):
                st.write("Agent 1: Designing framework...")
                prompt_response = model.generate_content(
                    f"""As a Framework Designer, your task is to create a structured framework for answering the following user input directly and comprehensively:

                    User Input: {topic}

                    Your framework should include:
                    1. A concise direct answer to the user's input
                    2. Key aspects or sub-questions that need to be explored to support and justify the answer
                    3. Relevant perspectives or angles to consider when examining each aspect

                    The framework should be actionable and guide the subsequent analysis.""",
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3
                    )
                )
                if hasattr(prompt_response, 'parts'):
                    system_prompt = prompt_response.parts[0].text
                else:
                    system_prompt = prompt_response.text
                st.write(system_prompt)

            # Agent 2: Analysis Refiner
            full_analysis = []
            context = ""
            for i in range(loops):
                with st.expander(f"🔄 Analysis Iteration {i+1}/{loops}", expanded=True):
                    st.write(f"Agent 2: Refining analysis (iteration {i+1})...")
                    response = model.generate_content(
                        f"""As an Analysis Refiner, your task is to conduct a detailed analysis based on the following framework and previous analysis context:

                        User Input: {topic}

                        Framework:
                        {system_prompt}

                        Previous Analysis Context: {context}

                        For each key aspect (sub-question) in the framework, provide a deep, well-reasoned explanation, considering the suggested perspectives. Build upon the previous analysis context in each iteration. Focus on providing detailed information and insights related to each aspect.

                        Output each aspect with the original question, followed by your analysis.""",
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

            # Agent 3: Expert Response Generator
            with st.expander("📊 Expert Response", expanded=True):
                st.write("Agent 3: Generating expert response...")
                expert_response = model.generate_content(
                    f"""As an Expert Response Generator, your task is to create a comprehensive, Nobel laureate-level response to the following user input, informed by the detailed analysis provided:

                    User Input: {topic}

                    Framework:
                    {system_prompt}

                    Detailed Analysis:
                    {' '.join(full_analysis)}

                    Your response should:
                    1. Provide a clear and authoritative answer to the user's input, directly addressing the question
                    2. Integrate the key insights and explanations from the analysis
                    3. Demonstrate a deep understanding of the topic, as if you were a leading expert in the field
                    4. Offer nuanced perspectives and potential implications

                    Write in a sophisticated and insightful manner.""",
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7
                    )
                )
                if hasattr(expert_response, 'parts'):
                    expert_text = expert_response.parts[0].text
                else:
                    expert_text = expert_response.text
                st.write(expert_text)

            # Agent 4: Concise Overview Generator
            with st.expander("💡 Simple Explanation", expanded=True):
                st.write("Agent 4: Providing simplified overview...")
                overview = model.generate_content(
                    f"""As a Concise Overview Generator, your task is to provide a simplified, easy-to-understand summary of the following expert response:

                    User Input: {topic}

                    Expert Response:
                    {expert_text}

                    Your summary should:
                    1. Capture the main points of the expert response
                    2. Use clear and simple language, avoiding jargon or technical terms
                    3. Be concise and easy to digest for a general audience""",
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3
                    )
                )
                if hasattr(overview, 'parts'):
                    overview_text = overview.parts[0].text
                else:
                    overview_text = overview.text
                st.write(overview_text)

        except Exception as e:
            st.error(f"⚠️ Error during analysis: {str(e)}")
            st.write("Debug info:")
            st.write(f"API Key status: {'Present' if api_key else 'Missing'}")
            st.write(f"Topic: {topic}")
            st.write(f"Iterations: {loops}")
    else:
        st.warning("Please enter a topic to analyze.")

