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
            # Agent 1: Creates sophisticated prompt structure
            with st.expander("🎯 Analysis Framework", expanded=True):
                st.write("Formulating analysis framework...")
                prompt_response = model.generate_content(
                    f"""Create a detailed system prompt for analyzing '{topic}'. 
                    Include instructions for examining multiple perspectives, potential implications, and interconnected aspects.
                    Be specific but concise.""",
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3
                    )
                )
                if hasattr(prompt_response, 'parts'):
                    system_prompt = prompt_response.parts[0].text
                else:
                    system_prompt = prompt_response.text
                st.write(system_prompt)

            # Agent 2: Reasoning agent
            full_analysis = []
            context = topic
            for i in range(loops):
                with st.expander(f"🔄 Reasoning Loop {i+1}/{loops}", expanded=True):
                    st.write(f"Processing iteration {i+1}...")
                    response = model.generate_content(
                        f"""{system_prompt}
                        
                        Previous context: {context}
                        Analyze this topic as if you were a Nobel Prize winner in the relevant field, drawing upon deep expertise and groundbreaking insights. Provide fresh analysis following the framework above.""",
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

            # Agent 3: Summarization agent
            with st.expander("📊 Final Summary", expanded=True):
                st.write("Generating final summary...")
                summary = model.generate_content(
                    f"""Synthesize the findings from the analysis loops about '{topic}' into a clear, comprehensive summary in simple language bulleting key points and crafting a concise summary paragraph. Finally, suggest 3 follow-up questions, 1 that digs deeper into a key aspect of the topic, 1 that explores a related topic, and 1 that investigates unexpected connections to the topic:

                    {' '.join(full_analysis)}""",
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

