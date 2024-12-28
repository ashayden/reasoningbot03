import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-1219")

# Streamlit UI
st.title("🤔 Advanced Reasoning Bot")
st.write("This bot uses multiple AI agents to analyze topics in depth with sophisticated reasoning.")

# Input section
topic = st.text_input("What topic should we explore?")
loops = st.slider("How many reasoning iterations?", min_value=1, max_value=5, value=3)

if st.button("Start Analysis"):
    if topic:
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
            system_prompt = prompt_response.text
            st.write(system_prompt)

        # Agent 2: Reasoning agent
        full_analysis = []
        context = topic
        for i in range(loops):
            with st.expander(f"🔄 Reasoning Loop {i+1}/{loops}", expanded=True):
                response = model.generate_content(
                    f"""{system_prompt}
                    
                    Previous context: {context}
                    Analyze this topic as if you were a Nobel Prize winner in the relevant field, drawing upon deep expertise and groundbreaking insights. Provide fresh analysis following the framework above.""",
                    generation_config=genai.types.GenerationConfig(
                        temperature=1.0
                    )
                )
                context = response.text
                full_analysis.append(context)
                st.write(context)

        # Agent 3: Summarization agent
        with st.expander("📊 Final Summary", expanded=True):
            summary = model.generate_content(
                f"""Synthesize the findings from the analysis loops about '{topic}' into a clear, comprehensive summary in simple language bulleting key points and crafting a concise summary paragraph. Finally, suggest 3 follow-up questions, 1 that digs deeper into a key aspect of the topic, 1 that explores a related topic, and 1 that investigates unexpected connections to the topic:

                {' '.join(full_analysis)}""",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1
                )
            )
            st.write(summary.text)
    else:
        st.warning("Please enter a topic to analyze.")

