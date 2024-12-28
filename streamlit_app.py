import streamlit as st
import google.generativeai as genai
import time
import logging
import random

# Configure logging with debug level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Get API key from Streamlit secrets
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception as e:
    logging.error(f"GOOGLE_API_KEY not found in Streamlit secrets: {e}")
    st.error("⚠️ GOOGLE_API_KEY not found in Streamlit secrets! Make sure to add it in the Streamlit Cloud dashboard.")
    st.stop()

# Configure API with error handling
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-pro")  # Using gemini-pro
except Exception as e:
    logging.error(f"Error configuring Gemini API: {e}")
    st.error(f"⚠️ Error configuring Gemini API: {str(e)}")
    st.stop()

# Streamlit UI
st.title("🤔 Advanced Reasoning Bot")
st.write("This bot uses multiple AI agents to analyze topics in depth with sophisticated reasoning.")

# Input section
topic = st.text_input("Enter a topic or question:")
loops = st.slider("How many research iterations per aspect?", min_value=1, max_value=10, value=2)

# Agent Prompts
agent1_prompt = '''You are an expert prompt engineer. Your task is to take a user's topic or question and refine it into a more specific and context-rich prompt. Then, based on this improved prompt, generate a structured investigation framework.

USER'S TOPIC/QUESTION: {topic}

1.  **Prompt Refinement:**
    *   Analyze the user's input and identify areas where you can add more detail, specificity, and context.
    *   Consider what background information or assumptions might be helpful to include.
    *   Reformulate the user's input into a more comprehensive and well-defined prompt.

2.  **Investigation Framework:**
    *   Based on your **refined prompt**, define a structured approach for investigating the topic.
    *   Outline:
        *   Core question/hypothesis (based on the refined prompt)
        *   Key areas requiring investigation
        *   Critical factors to examine
        *   Required data and information sources
        *   Potential challenges or limitations

    *   Present this as a clear investigation framework that will guide further research and analysis.

    *   Start with the **Refined Prompt** followed by the **Investigation Framework** separated by "---".
'''

agent2_prompt = '''Using the refined prompt and the established framework, continue researching and analyzing:

REFINED PROMPT:
{refined_prompt}

FRAMEWORK:
{framework}

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

agent3_prompt = '''Based on the completed analysis of the topic:

REFINED PROMPT:
{refined_prompt}

FRAMEWORK:
{system_prompt}

ANALYSIS:
{all_aspect_analyses}

You are a leading expert in fields relevant to the topic. Provide an in-depth analysis as a recognized authority on this topic. Offer insights and conclusions based on your extensive knowledge and experience.

Write a comprehensive report addressing the topic and/or answering the user's question. Include relevant statistics. Present the report in a neutral, objective, and informative tone, befitting an expert in the field.

### Comprehensive Report'''


def handle_response(response):
    """Handle model response and extract text with more specific error handling."""
    try:
        if hasattr(response, 'parts') and response.parts:
            if text_part := next((part.text for part in response.parts if part.text), None):
                return text_part.strip()
            else:
                logging.warning("Response parts exist, but no text part found.")
        elif hasattr(response, 'text'):
            return response.text.strip()
        else:
            logging.warning("Response does not contain expected structure for text extraction.")
    except Exception as e:
        logging.error(f"Error extracting text from response: {e}")
    return ""


# Define default generation config
default_generation_config = genai.types.GenerationConfig(
    temperature=0.7,
    top_p=0.8,
    top_k=40,
    max_output_tokens=2048
)

# Create new GenerationConfig objects for other agents:
agent2_config = genai.types.GenerationConfig(
    temperature=0.5,
    top_p=0.7,
    top_k=40,  # Add top_k or other parameters as needed
    max_output_tokens=2048
)

agent3_config = genai.types.GenerationConfig(
    temperature=0.3,
    top_p=0.7,
    top_k=20,
    max_output_tokens=2048
)


def generate_refined_prompt_and_framework(topic):
    """Generate a refined prompt and investigation framework using Agent 1."""
    try:
        prompt_response = model.generate_content(
            agent1_prompt.format(topic=topic),
            generation_config=default_generation_config
        )

        agent1_response = handle_response(prompt_response)

        # Extract refined prompt and framework from agent 1's response
        if agent1_response:
            parts = agent1_response.split("---")
            if len(parts) >= 2:
                refined_prompt = parts[0].replace("Refined Prompt", "").strip()
                
                # Find the start of the Investigation Framework
                framework_start_index = agent1_response.find("Investigation Framework")
                if framework_start_index != -1:
                    framework = agent1_response[framework_start_index + len("Investigation Framework"):].strip()
                else:
                    framework = ""
                    logging.warning("Could not find 'Investigation Framework' in Agent 1's response.")

                logging.info("Refined prompt and investigation framework generated successfully")
                return refined_prompt, framework
            else:
                logging.warning("Could not properly split the response from Agent 1 into refined prompt and framework.")
        else:
            logging.warning("Agent 1 response was empty or invalid.")

    except Exception as e:
        logging.error(f"Failed to generate refined prompt and framework: {e}")
    return None, None


def conduct_research(refined_prompt, framework, previous_analysis, current_aspect, iteration):
    """Conduct research and analysis using Agent 2."""
    try:
        prompt_response = model.generate_content(
            agent2_prompt.format(
                refined_prompt=refined_prompt,
                framework=framework,
                previous_analysis=previous_analysis,
                current_aspect=current_aspect
            ),
            generation_config=agent2_config
        )

        research = handle_response(prompt_response)
        if research:
            logging.info(f"Research iteration {iteration} completed successfully")
            return research
        else:
            logging.warning(f"Research iteration {iteration} returned empty or invalid content")
    except Exception as e:
        logging.error(f"Failed to conduct research in iteration {iteration}: {e}")
    return None


# Main Execution
if st.button("Start Analysis"):
    if topic:
        with st.spinner("Analyzing..."):
            # Agent 1: Refine prompt and generate framework
            refined_prompt, framework = generate_refined_prompt_and_framework(topic)

            if refined_prompt is None or framework is None:
                st.error("Failed to generate refined prompt and investigation framework. Please check the logs for details and try again.")
            else:
                st.markdown("### Refined Prompt")
                st.markdown(refined_prompt)
                st.markdown("---")
                st.markdown("### Investigation Framework")
                st.markdown(framework)
                st.markdown("---")

                # Agent 2: Conduct research through iterations
                current_analysis = ""  # Start with an empty string for the first iteration
                aspects = []
                # Extract aspects from the framework
                if framework:
                    for line in framework.split('\n'):
                        if line.strip().startswith('-'):
                            aspects.append(line.strip('- ').strip())

                for i in range(loops):
                    # Dynamically select an aspect to focus on
                    if aspects:
                        current_aspect = random.choice(aspects)
                    else:
                        current_aspect = f"General Research Phase {i+1}"

                    research = conduct_research(refined_prompt, framework, current_analysis, current_aspect, i + 1)
                    if research:
                        current_analysis += "\n\n" + research  # Append to the ongoing analysis
                        st.markdown(f"### Research Phase {i + 1} (Focus: {current_aspect})")
                        st.markdown(research)
                        st.markdown("---")
                    else:
                        st.error(
                            f"Failed during research phase {i + 1}. Please check the logs for details and try again.")
                        break  # Stop further iterations if one fails

                # Agent 3: Present comprehensive analysis
                # Proceed to Agent 3 only if Agent 2 was successful
                if research:
                    try:
                        final_response = model.generate_content(
                            agent3_prompt.format(
                                refined_prompt=refined_prompt,
                                system_prompt=framework,
                                all_aspect_analyses=current_analysis
                            ),
                            generation_config=agent3_config
                        )

                        final_analysis = handle_response(final_response)
                        st.markdown("### Analysis Results")
                        st.markdown(final_analysis)

                    except Exception as e:
                        st.error(
                            f"Error in final analysis generation: {str(e)}. Please check the logs for details and try again.")
    else:
        st.warning("Please enter a topic to analyze.")