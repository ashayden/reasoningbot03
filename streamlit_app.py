import streamlit as st
import google.generativeai as genai
import time
import logging

# Configure logging with debug level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
loops = st.slider("How many reasoning iterations per aspect?", min_value=1, max_value=10, value=2)

# Agent Prompts
agent1_prompt = '''Define a structured approach for investigating: {topic}

Outline:
1. Core question/hypothesis
2. Key areas requiring investigation
3. Critical factors to examine
4. Required data and information sources
5. Potential challenges or limitations

Present this as a clear investigation framework that will guide our research and analysis.'''

agent2_prompt = '''Using the established framework, continue researching and analyzing: {topic}

PREVIOUS ANALYSIS:
{previous_analysis}

ITERATION FOCUS:
{current_aspect}

Build upon the existing analysis by:
1. Gathering relevant data and evidence
2. Analyzing new findings
3. Identifying connections and patterns
4. Updating conclusions based on new information
5. Noting any emerging implications'''

agent3_prompt = '''Based on the completed analysis of {topic}:

FRAMEWORK:
{system_prompt}

ANALYSIS:
{all_aspect_analyses}

### Comprehensive Analysis

**Current State:**
[Present the current situation and key context]

**Analysis:**
[Present the main findings and evidence]

**Conclusions:**
[Present the conclusions drawn from the analysis]

**Future Outlook:**
[Present the implications and future projections]'''

def handle_response(response):
    """Handle model response and extract text."""
    if hasattr(response, 'parts'):
        return response.parts[0].text.strip()
    return response.text.strip()

def generate_framework(topic):
    """Generate initial investigation framework using Agent 1."""
    try:
        prompt_response = model.generate_content(
            agent1_prompt.format(topic=topic),
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048
            )
        )
        
        framework = handle_response(prompt_response)
        logging.info("Investigation framework generated successfully")
        return framework
        
    except Exception as e:
        logging.error(f"Failed to generate framework: {str(e)}")
        return None

def conduct_research(topic, previous_analysis, current_aspect, iteration):
    """Conduct research and analysis using Agent 2."""
    try:
        prompt_response = model.generate_content(
            agent2_prompt.format(
                topic=topic,
                previous_analysis=previous_analysis,
                current_aspect=current_aspect
            ),
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,
                top_p=0.7,
                top_k=20,
                max_output_tokens=2048
            )
        )
        
        research = handle_response(prompt_response)
        logging.info(f"Research iteration {iteration} completed")
        return research
        
    except Exception as e:
        logging.error(f"Failed to conduct research: {str(e)}")
        return None

# Main Execution
if st.button("Start Analysis"):
    if topic:
        with st.spinner("Analyzing..."):
            # Agent 1: Define investigation framework
            framework = generate_framework(topic)
            
            if framework is None:
                st.error("Failed to generate investigation framework. Please try again.")
                st.stop()
            
            st.markdown("### Investigation Framework")
            st.markdown(framework)
            st.markdown("---")
            
            # Agent 2: Conduct research through iterations
            current_analysis = framework
            for i in range(loops):
                research = conduct_research(topic, current_analysis, f"Research Phase {i+1}", i+1)
                if research:
                    current_analysis = research
                    st.markdown(f"### Research Phase {i+1}")
                    st.markdown(research)
                    st.markdown("---")
            
            # Agent 3: Present comprehensive analysis
            try:
                final_response = model.generate_content(
                    agent3_prompt.format(
                        topic=topic,
                        system_prompt=framework,
                        all_aspect_analyses=current_analysis
                    ),
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        top_p=0.7,
                        top_k=20,
                        max_output_tokens=2048
                    )
                )
                
                final_analysis = handle_response(final_response)
                st.markdown("### Analysis Results")
                st.markdown(final_analysis)
                
            except Exception as e:
                st.error(f"Error in final analysis generation: {str(e)}")
                
    else:
        st.warning("Please enter a topic to analyze.")