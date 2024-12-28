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
agent1_prompt = '''You are an expert research strategist and analyst. Your task is to create a comprehensive reasoning strategy for analyzing: {topic}

Develop a strategic framework that will guide our analysis. Consider:
1. The core question or hypothesis to investigate
2. Key areas that need to be examined
3. Critical factors that could influence the outcome
4. Potential data sources or evidence to consider
5. Methodological approaches for analysis

Present your strategy in a clear, organized format that will guide further investigation.
Focus on creating a thorough and logical approach to understanding {topic}.

Your response should be comprehensive yet clear, avoiding unnecessary complexity while ensuring all crucial aspects are covered.'''

agent2_prompt = '''As an Analysis Refiner, build upon the previous analysis to deepen our understanding.

PREVIOUS ANALYSIS:
{previous_analysis}

FOCUS AREA:
{current_aspect}

Your task is to:
1. Evaluate the evidence and reasoning presented
2. Identify gaps or areas needing deeper investigation
3. Add new insights or perspectives
4. Challenge assumptions if necessary
5. Strengthen the analytical framework

Maintain a clear, logical structure while adding depth to the analysis.'''

agent3_prompt = '''As an Expert Response Generator, synthesize this comprehensive analysis:

TOPIC:
{topic}

ANALYSIS FRAMEWORK:
{system_prompt}

DETAILED ANALYSIS:
{all_aspect_analyses}

Provide a comprehensive expert analysis that:
1. Synthesizes all key findings
2. Evaluates the strength of evidence
3. Draws well-reasoned conclusions
4. Identifies implications
5. Addresses uncertainties

Format your response with clear sections:
### Comprehensive Analysis

**Key Findings:**
[Present main discoveries and insights]

**Evidence Assessment:**
[Evaluate the strength and reliability of evidence]

**Conclusions:**
[Present well-reasoned conclusions]

**Implications:**
[Discuss broader implications and impacts]'''

agent4_prompt = '''As a Concise Overview Generator, distill this expert analysis into a clear summary:

TOPIC:
{topic}

EXPERT ANALYSIS:
{expert_text}

Provide a concise summary in three parts:

TL;DR:
[Direct answer to the core question/topic, if applicable, using "✅ Yes" / "❌ No" / "❓ Uncertain"]

KEY TAKEAWAYS:
• [3-5 most important points, each starting with an action verb]

EXECUTIVE SUMMARY:
[Two paragraphs synthesizing the main findings and their significance]'''

def handle_response(response):
    """Handle model response and extract text."""
    if hasattr(response, 'parts'):
        return response.parts[0].text.strip()
    return response.text.strip()

def generate_analysis(topic):
    """Generate initial analysis framework using Agent 1."""
    try:
        prompt_response = model.generate_content(
            agent1_prompt.format(topic=topic),
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,  # Increased for more creative strategy
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048
            )
        )
        
        analysis = handle_response(prompt_response)
        logging.info("Initial analysis framework generated successfully")
        return analysis
        
    except Exception as e:
        logging.error(f"Failed to generate initial analysis: {str(e)}")
        return None

def refine_analysis(topic, previous_analysis, current_aspect, iteration):
    """Refine analysis using Agent 2."""
    try:
        prompt_response = model.generate_content(
            agent2_prompt.format(
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
        
        refined_analysis = handle_response(prompt_response)
        logging.info(f"Analysis refinement iteration {iteration} completed")
        return refined_analysis
        
    except Exception as e:
        logging.error(f"Failed to refine analysis: {str(e)}")
        return None

# Main Execution
if st.button("Start Analysis"):
    if topic:
        with st.spinner("Generating analysis..."):
            # Agent 1: Generate initial framework
            initial_analysis = generate_analysis(topic)
            
            if initial_analysis is None:
                st.error("Failed to generate initial analysis. Please try again.")
                st.stop()
            
            st.markdown("### Initial Analysis Framework")
            st.markdown(initial_analysis)
            st.markdown("---")
            
            # Agent 2: Refine analysis through iterations
            current_analysis = initial_analysis
            for i in range(loops):
                refined = refine_analysis(topic, current_analysis, f"Iteration {i+1}", i+1)
                if refined:
                    current_analysis = refined
                    st.markdown(f"### Refinement Iteration {i+1}")
                    st.markdown(refined)
                    st.markdown("---")
            
            # Agent 3: Generate expert analysis
            try:
                expert_response = model.generate_content(
                    agent3_prompt.format(
                        topic=topic,
                        system_prompt=initial_analysis,
                        all_aspect_analyses=current_analysis
                    ),
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        top_p=0.7,
                        top_k=20,
                        max_output_tokens=2048
                    )
                )
                
                expert_analysis = handle_response(expert_response)
                st.markdown("### Expert Analysis")
                st.markdown(expert_analysis)
                st.markdown("---")
                
                # Agent 4: Generate concise overview
                overview_response = model.generate_content(
                    agent4_prompt.format(
                        topic=topic,
                        expert_text=expert_analysis
                    ),
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.2,
                        top_p=0.7,
                        top_k=20,
                        max_output_tokens=2048
                    )
                )
                
                overview = handle_response(overview_response)
                st.markdown("### Summary")
                st.markdown(overview)
                
            except Exception as e:
                st.error(f"Error in final analysis generation: {str(e)}")
                
    else:
        st.warning("Please enter a topic to analyze.")