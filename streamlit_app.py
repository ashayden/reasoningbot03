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

# --- Custom CSS for Streamlit ---
st.markdown("""
<style>
/* Set font family for entire app */
body {
    font-family: 'Roboto', sans-serif;
}

/* Style for expander headers */
.streamlit-expanderHeader {
    font-weight: bold;
    font-size: 1.2rem; 
}

/* Style for progress bar */
.stProgress > div > div > div > div {
    background-color: #5D1796;
}

/* Style for the main title */
.main-title {
    font-size: 2.5rem;
    font-weight: bold;
    color: #5D1796;
    margin-bottom: 0.5rem;
}

/* Style for the subheader */
.subheader {
    font-size: 1.2rem;
    color: #6c757d;
    margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# Get API key from Streamlit secrets
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception as e:
    logging.error(f"GOOGLE_API_KEY not found in Streamlit secrets: {e}")
    st.error(
        "⚠️ GOOGLE_API_KEY not found in Streamlit secrets! Make sure to add it in the Streamlit Cloud dashboard."
    )
    st.stop()

# Configure API with error handling
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
except Exception as e:
    logging.error(f"Error configuring Gemini API: {e}")
    st.error(f"⚠️ Error configuring Gemini API: {str(e)}")
    st.stop()

# --- Main Title ---
st.markdown("<h1 class='main-title'>Advanced Reasoning Bot 🤖</h1>", unsafe_allow_html=True)

# --- Subheader ---
st.markdown("<p class='subheader'>This bot uses multiple AI agents to analyze topics in depth with sophisticated reasoning.</p>", unsafe_allow_html=True)

# Input section
topic = st.text_input(
    "Enter a topic or question:",
    placeholder="e.g., 'What are the impacts of AI on the economy?'",
)

# --- UI/UX - Add expander for prompt details ---
with st.expander("**Advanced Prompt Customization**"):
    # Agent Prompts
    agent1_prompt = st.text_area(
        "Agent 1 Prompt (Prompt Engineer)",
        '''You are an expert prompt engineer. Your task is to take a user's topic or question and refine it into a more specific and context-rich prompt. Then, based on this improved prompt, generate a structured investigation framework.

USER'S TOPIC/QUESTION: {topic}

1.  **Prompt Refinement**
    *   Analyze the user's input and identify areas where you can add more detail, specificity, and context.
    *   Consider what background information or assumptions might be helpful to include.
    *   Reformulate the user's input into a more comprehensive and well-defined prompt.

2.  **Investigation Framework**
    *   Based on your **refined prompt**, define a structured approach for investigating the topic.
    *   Outline:
        -   Core Question/Hypothesis
        -   Key Areas Requiring Investigation
        -   Critical Factors to Examine
        -   Required Data and Information Sources
        -   Potential Challenges or Limitations

    *   Present this as a clear investigation framework that will guide further research and analysis.

Format your response with appropriate spacing between sections:

Refined Prompt
[Your refined prompt here]

---

Investigation Framework

Core Question/Hypothesis

[Your hypothesis here, which may wrap to multiple lines while maintaining proper alignment]

Key Areas Requiring Investigation

1. [Area Name]:
   - [First point with detailed explanation that may wrap to multiple lines, with proper indentation for wrapped lines]
   - [Second point with similarly detailed explanation, maintaining consistent indentation for wrapped text]
   - [Third point following the same format, ensuring all wrapped lines align with the first line of the point]

2. [Area Name]:
   - [First point with detailed explanation that may wrap to multiple lines, with proper indentation for wrapped lines]
   - [Second point with similarly detailed explanation, maintaining consistent indentation for wrapped text]
   - [Third point following the same format, ensuring all wrapped lines align with the first line of the point]

Note: 
- Each section header should be on its own line
- Leave a blank line between the header and its content
- Each numbered item starts with a number followed by a period, space, and area name
- Bullet points appear on new lines beneath the numbered item
- Use consistent indentation for bullet points
- Add a blank line between numbered items
- Use a hyphen (-) for bullet points''',
        key="agent1_prompt",
        height=300,
    )

    agent2_prompt = st.text_area(
        "Agent 2 Prompt (Researcher)",
        '''Using the refined prompt and the established framework, continue researching and analyzing:

REFINED PROMPT:
{refined_prompt}

FRAMEWORK:
{framework}

PREVIOUS ANALYSIS:
{previous_analysis}

CURRENT FOCUS:
{current_aspect}

Begin your response with a descriptive title that summarizes the focus area and its relation to the main topic.
For example: "Economic Factors: Impact on Regional Development Trends"

Then present your findings by:
1. Gathering relevant data and evidence
2. Analyzing new findings
3. Identifying connections and patterns
4. Updating conclusions based on new information
5. Noting any emerging implications

Structure your response with the descriptive title on the first line, followed by your analysis.''',
        key="agent2_prompt",
        height=300,
    )

    agent3_prompt = st.text_area(
        "Agent 3 Prompt (Expert Analyst)",
        '''Based on the completed analysis of the topic:

REFINED PROMPT:
{refined_prompt}

FRAMEWORK:
{system_prompt}

ANALYSIS:
{all_aspect_analyses}

You are a leading expert in fields relevant to the topic. Provide an in-depth analysis as a recognized authority on this topic. Offer insights and conclusions based on your extensive knowledge and experience.

Write a comprehensive report addressing the topic and/or answering the user's question. Include relevant statistics. Present the report in a neutral, objective, and informative tone, befitting an expert in the field.

### Analysis Results

[Title of Analysis]

Executive Summary:
[Provide a comprehensive overview of the key findings, challenges, and recommendations]

I. [First Major Section]:
[Detailed analysis with supporting evidence and data]

[Continue with subsequent sections as needed]

Recommendations:
[List specific, actionable recommendations based on the analysis]''',
        key="agent3_prompt",
        height=300,
    )

# Slider for research depth with descriptive options
loops = st.select_slider(
    "How deep should we dive?",
    options=["Puddle", "Lake", "Ocean", "Mariana Trench"],
    value="Lake",
)

# Convert the depth selection to a numerical value
if loops == "Puddle":
    loops_num = 1
elif loops == "Lake":
    loops_num = random.randint(2, 3)
elif loops == "Ocean":
    loops_num = random.randint(4, 6)
elif loops == "Mariana Trench":
    loops_num = random.randint(7, 10)
else:
    loops_num = 2  # Default value

def handle_response(response):
    """Handle model response and extract text with more specific error handling."""
    try:
        if hasattr(response, "parts") and response.parts:
            if text_part := next(
                (part.text for part in response.parts if part.text), None
            ):
                return text_part.strip()
            else:
                logging.warning("Response parts exist, but no text part found.")
        elif hasattr(response, "text"):
            return response.text.strip()
        else:
            logging.warning("Response does not contain expected structure for text extraction.")
    except Exception as e:
        logging.error(f"Error extracting text from response: {e}")
    return ""


# Define default generation config
default_generation_config = genai.types.GenerationConfig(
    temperature=0.7, top_p=0.8, top_k=40, max_output_tokens=2048
)

# Create new GenerationConfig objects for other agents:
agent2_config = genai.types.GenerationConfig(
    temperature=0.5, top_p=0.7, top_k=40, max_output_tokens=2048
)

agent3_config = genai.types.GenerationConfig(
    temperature=0.3, top_p=0.7, top_k=20, max_output_tokens=4096
)


def generate_refined_prompt_and_framework(topic):
    """Generate a refined prompt and investigation framework using Agent 1."""
    try:
        prompt_response = model.generate_content(
            agent1_prompt.format(topic=topic),
            generation_config=default_generation_config,
        )

        agent1_response = handle_response(prompt_response)

        # Extract refined prompt and framework from agent 1's response
        if agent1_response:
            parts = agent1_response.split("---")
            if len(parts) >= 2:
                # Clean up the refined prompt section
                refined_prompt = parts[0].replace("Refined Prompt", "").strip()

                # Clean up the framework section
                framework = parts[1].strip()
                if framework.startswith("Investigation Framework"):
                    framework = framework[len("Investigation Framework") :].strip()

                # Remove any stray colons from section headers
                framework = framework.replace(
                    "Core Question/Hypothesis:", "Core Question/Hypothesis"
                )
                framework = framework.replace(
                    "Key Areas Requiring Investigation:", "Key Areas Requiring Investigation"
                )

                # Further clean up for framework formatting
                framework_lines = framework.split("\n")
                cleaned_framework_lines = []
                for line in framework_lines:
                    # Ensure consistent indentation for bullet points
                    if line.lstrip().startswith("-"):
                        cleaned_framework_lines.append("   " + line.lstrip())
                    else:
                        cleaned_framework_lines.append(line)
                framework = "\n".join(cleaned_framework_lines)

                logging.info(
                    "Refined prompt and investigation framework generated successfully"
                )
                return refined_prompt, framework
            else:
                logging.warning(
                    "Could not properly split the response from Agent 1 into refined prompt and framework."
                )
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
            generation_config=agent2_config,
        )

        research = handle_response(prompt_response)
        if research:
            # Remove any iteration focus headers if they exist
            research_lines = research.split("\n")
            cleaned_research = []
            skip_next = False
            for line in research_lines:
                if "Iteration Focus:" in line or "ITERATION FOCUS:" in line:
                    skip_next = True
                    continue
                if skip_next:
                    skip_next = False
                    continue
                cleaned_research.append(line)

            research = "\n".join(cleaned_research).strip()
            logging.info(f"Research phase {iteration} completed successfully")
            return research
        else:
            logging.warning(f"Research phase {iteration} returned empty or invalid content")
    except Exception as e:
        logging.error(f"Failed to conduct research in phase {iteration}: {e}")
    return None


# Main Execution
if st.button("Start Analysis", key="start_button"):
    if topic:
        # Initialize progress indicators
        progress_states = {
            "refined_prompt": {"label": "Refined Prompt", "progress": 0, "status": "pending"},
            "framework": {"label": "Investigation Framework", "progress": 0, "status": "pending"},
            "research": {"label": "Research Phases", "progress": 0, "status": "pending"},
            "analysis": {"label": "Analysis Results", "progress": 0, "status": "pending"},
        }

        # Create placeholders for each section
        placeholders = {}
        for section in progress_states:
            placeholders[section] = st.empty()

        with st.spinner("Analyzing..."):
            # Agent 1: Refine prompt and generate framework
            refined_prompt, framework = generate_refined_prompt_and_framework(topic)
            progress_states["refined_prompt"]["progress"] = 100
            progress_states["refined_prompt"]["status"] = "complete"

            if refined_prompt is None or framework is None:
                st.error(
                    "Failed to generate refined prompt and investigation framework. Please check the logs for details and try again."
                )
            else:
                progress_states["framework"]["progress"] = 100
                progress_states["framework"]["status"] = "complete"

                # Update placeholders with expanders and content
                with placeholders["refined_prompt"]:
                    with st.expander(f"**{progress_states['refined_prompt']['label']}**", expanded=False):
                        if progress_states["refined_prompt"]["status"] == "complete":
                            st.markdown(refined_prompt.lstrip(":\n").strip())
                            st.markdown("✅ Complete")  # Indicate completion
                        else:
                            st.markdown("⏳ In progress...")

                with placeholders["framework"]:
                    with st.expander(f"**{progress_states['framework']['label']}**", expanded=False):
                        if progress_states["framework"]["status"] == "complete":
                            st.markdown(framework.lstrip(": **\n").strip())
                            st.markdown("✅ Complete")  # Indicate completion
                        else:
                            st.markdown("⏳ In progress...")

                # Agent 2: Conduct research through iterations
                current_analysis = ""
                aspects = []

                if framework:
                    for line in framework.split("\n"):
                        if (
                            line.strip().startswith("1.")
                            or line.strip().startswith("2.")
                            or line.strip().startswith("3.")
                            or line.strip().startswith("4.")
                        ):
                            aspects.append(line.strip())

                for i in range(loops_num):
                    progress_states["research"]["progress"] = int(((i + 1) / loops_num) * 100)
                    progress_states["research"]["status"] = "complete" if i == loops_num - 1 else "in progress"

                    if aspects:
                        current_aspect = random.choice(aspects)
                    else:
                        current_aspect = "Current State and Trends"

                    research = conduct_research(
                        refined_prompt, framework, current_analysis, current_aspect, i + 1
                    )
                    if research:
                        current_analysis += "\n\n" + research
                        research_lines = research.split("\n")
                        title = next(
                            (line for line in research_lines if line.strip()),
                            current_aspect,
                        )
                        with placeholders["research"]:
                            with st.expander(f"**{title}**", expanded=False):
                                st.markdown("\n".join(research_lines[1:]))
                                if progress_states["research"]["status"] == "complete":
                                    st.markdown("✅ Complete")  # Indicate completion
                                else:
                                    st.markdown("⏳ In progress...")
                    else:
                        with placeholders["research"]:
                            st.error(
                                f"Failed during research phase {i + 1}. Please check the logs for details and try again."
                            )
                            break

                # Agent 3: Present comprehensive analysis
                if research:
                    progress_states["analysis"]["progress"] = 100
                    progress_states["analysis"]["status"] = "complete"
                    try:
                        final_response = model.generate_content(
                            agent3_prompt.format(
                                refined_prompt=refined_prompt,
                                system_prompt=framework,
                                all_aspect_analyses=current_analysis,
                            ),
                            generation_config=agent3_config,
                        )

                        final_analysis = handle_response(final_response)

                        with placeholders["analysis"]:
                            with st.expander(f"**{progress_states['analysis']['label']}**", expanded=False):
                                if progress_states["analysis"]["status"] == "complete":
                                    st.markdown(final_analysis)
                                    st.markdown("✅ Complete")  # Indicate completion
                                else:
                                    st.markdown("⏳ In progress...")

                    except Exception as e:
                        with placeholders["analysis"]:
                            st.error(
                                f"Error in final analysis generation: {str(e)}. Please check the logs for details and try again."
                            )
                else:
                    progress_states["analysis"]["progress"] = 100
                    progress_states["analysis"]["status"] = "complete"

    else:
        st.warning("Please enter a topic to analyze.")