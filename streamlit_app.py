import streamlit as st
import google.generativeai as genai
import time
import logging
import random
import io
from fpdf import FPDF

# ------------------ GLOBAL CONFIG & LOGGING ------------------ #
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --------------- STEP LABELS FOR THE WIZARD --------------- #
STEPS = [
    "Refining Prompt",
    "Developing Framework",
    "Conducting Research",
    "Final Report",
    "Analysis Complete"
]

# ------------------ FUNCTION: RENDER STEPPER ------------------ #
def render_stepper(current_step: int) -> None:
    """
    Render a 5-step progress wizard. 
    current_step can be 0..4, corresponding to STEPS above.
    """
    if current_step < 0:
        current_step = 0
    if current_step > 4:
        current_step = 4

    step_html = ""
    for i, label in enumerate(STEPS):
        # Determine if completed, active, or upcoming
        if i < current_step:
            status_class = "complete"   # completed step
        elif i == current_step:
            status_class = "active"     # current step
        else:
            status_class = ""           # future step
        
        step_html += f"""
        <div class="step {status_class}">
            <div class="step-number">{i+1}</div>
            <div class="step-label">{label}</div>
        </div>
        """
        # Add line except after the last step
        if i < len(STEPS) - 1:
            step_html += """<div class="step-line"></div>"""

    # The CSS for the stepper
    final_html = f"""
    <style>
    .stepper-container {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 2rem;
    }}
    .step {{
      flex: 1;
      text-align: center;
      position: relative;
    }}
    .step-line {{
      flex: none;
      width: 100px; 
      height: 2px;
      background: #e0e0e0;
      margin: 0 -50px; 
      z-index: -1;
    }}
    .step-number {{
      margin: 0 auto;
      width: 36px;
      height: 36px;
      line-height: 36px;
      border-radius: 50%;
      border: 2px solid #ccc;
      background: #fff;
      color: #999;
      font-weight: bold;
    }}
    .step-label {{
      margin-top: 0.5rem;
      font-size: 0.85rem;
      color: #666;
    }}
    /* Completed step = green */
    .step.complete .step-number {{
      border-color: #28a745;
      background-color: #28a745;
      color: #fff;
    }}
    /* Active step = accent color (blue) */
    .step.active .step-number {{
      border-color: #007bff;
      color: #007bff;
    }}
    </style>

    <div class="stepper-container">
      {step_html}
    </div>
    """

    st.markdown(final_html, unsafe_allow_html=True)

# ------------------ Inject Original CSS (Minus Old Bar) ------------------ #
st.markdown("""
<style>
/* Make container spacing more compact */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 1rem !important;
    max-width: 800px;
}

/* Input field styling */
.stTextInput > div > div > input {
    padding: 0.5rem 1rem;
    font-size: 1rem;
    border-radius: 0.5rem;
}

/* Button styling */
.stButton > button {
    width: 100%;
    padding: 0.5rem 1rem;
    font-size: 1rem;
    font-weight: 500;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
    transition: all 0.2s;
}

/* Expander styling */
.streamlit-expanderHeader {
    font-size: 1rem;
    font-weight: 600;
    padding: 0.75rem 0;
    border-radius: 0.5rem;
}

/* Slider styling */
.stSlider > div > div > div {
    height: 0.5rem !important;
}
.stSlider > div > div > div > div {
    height: 1rem !important;
    width: 1rem !important;
}

/* Download button styling */
[data-testid="stDownloadButton"] > button {
    width: 100%;
    padding: 0.5rem 1rem;
    font-size: 1rem;
    font-weight: 500;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}

/* Adjust spacing between sections */
.element-container {
    margin-bottom: 1rem;
}

/* Main title with hover effect */
.main-title {
    font-size: 2.5rem !important;
    color: rgba(49, 51, 63, 0.9) !important;
    text-align: center !important;
    margin-bottom: 2rem !important;
    font-weight: 700 !important;
    position: relative !important;
    cursor: help !important;
}
.main-title:hover::after {
    content: attr(data-title);
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    bottom: -30px;
    background: rgba(49, 51, 63, 0.9);
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.9rem;
    white-space: nowrap;
    z-index: 1000;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style>
""", unsafe_allow_html=True)

# ------------------ Initialize Session State ------------------ #
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'pdf_buffer' not in st.session_state:
    st.session_state.pdf_buffer = None
if 'final_analysis' not in st.session_state:
    st.session_state.final_analysis = None
if 'research_results' not in st.session_state:
    st.session_state.research_results = []
if 'tldr_summary' not in st.session_state:
    st.session_state.tldr_summary = None
if 'refined_prompt' not in st.session_state:
    st.session_state.refined_prompt = None
if 'framework' not in st.session_state:
    st.session_state.framework = None
if 'previous_input' not in st.session_state:
    st.session_state.previous_input = ""
if 'start_button_clicked' not in st.session_state:
    st.session_state.start_button_clicked = False
if 'random_fact' not in st.session_state:
    st.session_state.random_fact = None

# We'll track which wizard step we're on via session_state.current_step
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0

# ------------------ Set Up GenAI ------------------ #
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception as e:
    logging.error(f"GOOGLE_API_KEY not found in Streamlit secrets: {e}")
    st.error("⚠️ GOOGLE_API_KEY not found in Streamlit secrets! Make sure to add it in the Streamlit Cloud dashboard.")
    st.stop()

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    agent3_config = genai.types.GenerationConfig(
        temperature=0.7,
        top_p=0.8,
        top_k=40,
        max_output_tokens=2048,
    )
except Exception as e:
    logging.error(f"Error configuring Gemini API: {e}")
    st.error(f"⚠️ Error configuring Gemini API: {str(e)}")
    st.stop()

# --- Main Title ---
st.markdown(
    "<h1 class='main-title' data-title='Multi-Agent Reasoning Assistant a003'>M.A.R.A.</h1>",
    unsafe_allow_html=True
)

# ------------------ Input Section ------------------ #
topic = st.text_input(
    "Enter a topic or question:",
    placeholder='e.g. "Is the Ivory-billed woodpecker really extinct?"',
    key="topic_input",
    on_change=lambda: st.session_state.update({"start_button_clicked": True}) if st.session_state.topic_input else None,
)

if topic and st.session_state.get('topic_input', '') != st.session_state.get('previous_input', ''):
    st.session_state.start_button_clicked = True

# If input changes, reset analysis
if topic != st.session_state.previous_input:
    st.session_state.analysis_complete = False
    st.session_state.pdf_buffer = None
    st.session_state.final_analysis = None
    st.session_state.research_results = []
    st.session_state.tldr_summary = None
    st.session_state.refined_prompt = None
    st.session_state.framework = None
    st.session_state.previous_input = topic
    st.session_state.current_step = 0

# --- If analysis is complete, let's mark the final step as done ---
if st.session_state.analysis_complete:
    st.session_state.current_step = 4  # "Analysis Complete"

# ------------------ Render the Step Wizard at the Top ------------------ #
render_stepper(st.session_state.current_step)

# --- UI/UX - Add expander for prompt details ---
with st.expander("**☠️ Advanced Prompt Customization ☠️**"):
    agent1_prompt = st.text_area(
        "Agent 1 Prompt (Prompt Engineer)",
        '''You are an expert prompt engineer. Your task is to take a user's topic or question and refine it into a more specific and context-rich prompt. Then, based on this improved prompt, generate a structured investigation framework.

USER'S TOPIC/QUESTION: {topic}

1. **Prompt Refinement**
* Analyze the user's input and identify areas where you can add more detail, specificity, and context.
* Consider what background information or assumptions might be helpful to include.
* Reformulate the user's input into a more comprehensive and well-defined prompt.

2. **Investigation Framework**
* Based on your **refined prompt**, define a structured approach for investigating the topic.
* Outline:
- Core Question/Hypothesis
- Key Areas Requiring Investigation
- Critical Factors to Examine
- Required Data and Information Sources
- Potential Challenges or Limitations

* Present this as a clear investigation framework that will guide further research and analysis.

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

### Final Report

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

# ------------------ Sliders / Buttons ------------------ #
loops = st.select_slider(
    "How deep should we dive?",
    options=["Puddle", "Lake", "Ocean", "Mariana Trench"],
    value="Lake",
)

_, _, button_col = st.columns([1, 1, 1])
with button_col:
    start_button_clicked = st.button("🌊 Dive In", key="start_button")

# ------------------ Display Past Results (if complete) ------------------ #
if st.session_state.analysis_complete and topic:
    with st.expander("🎲 Random Fact", expanded=True):
        st.markdown(
            st.session_state.random_fact if st.session_state.random_fact 
            else "Unable to generate random fact."
        )

    if st.session_state.tldr_summary:
        with st.expander("💡 TL;DR", expanded=True):
            st.markdown(st.session_state.tldr_summary)

    if st.session_state.refined_prompt:
        with st.expander("🎯 Refined Prompt", expanded=False):
            st.markdown(st.session_state.refined_prompt)

    if st.session_state.framework:
        with st.expander("🗺️ Investigation Framework", expanded=False):
            st.markdown(st.session_state.framework)

    for title, content in st.session_state.research_results:
        with st.expander(f"**{title}**", expanded=False):
            st.markdown(content)

    if st.session_state.final_analysis:
        with st.expander(f"📋 Final Report", expanded=False):
            st.markdown(st.session_state.final_analysis)

    # Download
    _, download_col = st.columns([1, 2])
    with download_col:
        st.download_button(
            label="⬇️ Download Report as PDF",
            data=st.session_state.pdf_buffer,
            file_name=f"{topic}_analysis_report.pdf",
            mime="application/pdf",
            key="download_button",
            help="Download the complete analysis report as a PDF file",
            use_container_width=True
        )

# ------------------ Utility Functions ------------------ #
def handle_response(response):
    """Handle model response and extract text with more specific error handling."""
    try:
        if hasattr(response, "parts") and response.parts:
            # Return first text part found
            if text_part := next((part.text for part in response.parts if part.text), None):
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

def generate_random_fact(topic):
    """Generate a random interesting fact related to the topic."""
    try:
        fact_prompt = f"""
Generate ONE short, fascinating, and possibly bizarre fact related to this topic: {topic}
Make it engaging and fun. Include relevant emojis. Keep it to one or two sentences maximum.
Focus on surprising, lesser-known, or unusual aspects of the topic.
"""
        response = model.generate_content(
            fact_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.9,
                top_p=0.9,
                top_k=40,
                max_output_tokens=100,
            ),
        )
        return handle_response(response)
    except Exception as e:
        logging.error(f"Failed to generate random fact: {e}")
    return None

def generate_quick_summary(topic):
    """Generate a quick summary (TL;DR) using the model."""
    try:
        quick_summary_prompt = f"""
Provide a very brief, one to two-sentence TL;DR (Too Long; Didn't Read) overview of the following topic,
incorporating emojis where relevant:
{topic}
"""
        response = model.generate_content(
            quick_summary_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048,
            ),
        )
        summary = handle_response(response)
        # Ensure summary is within 1-2 sentences
        sentences = summary.split('.')
        if len(sentences) > 2:
            summary = '. '.join(sentences[:2]) + '.' if sentences[0] else ''
        return summary.strip()
    except Exception as e:
        logging.error(f"Failed to generate quick summary: {e}")
    return None

def create_download_pdf(refined_prompt, framework, research_analysis, final_analysis):
    """Create a PDF report from the analysis results."""
    try:
        def sanitize_text(text):
            """Clean text for PDF compatibility."""
            if not text:
                return ""
            text = text.replace('—', '-').replace('–', '-')
            text = text.replace('"', '"')
            text = text.replace('’', "'").replace('‘', "'").replace('…', '...')
            # Remove emojis / special chars outside ASCII
            return ''.join(char for char in text if ord(char) < 128)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)

        # Title
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Analysis Report", ln=True, align="C")
        pdf.ln(10)

        # Refined prompt
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Refined Prompt", ln=True)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, sanitize_text(refined_prompt))
        pdf.ln(10)

        # Framework
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Investigation Framework", ln=True)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, sanitize_text(framework))
        pdf.ln(10)

        # Research analysis
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Research Analysis", ln=True)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, sanitize_text(research_analysis))
        pdf.ln(10)

        # Final analysis
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Final Analysis", ln=True)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, sanitize_text(final_analysis))

        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        logging.error(f"Failed to create PDF: {e}")
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 10, f"Error creating PDF report: {str(e)}", ln=True)
        return pdf.output(dest='S').encode('latin-1')

def generate_refined_prompt_and_framework(topic):
    """Generate a refined prompt and framework using Agent 1."""
    try:
        prompt_response = model.generate_content(
            agent1_prompt.format(topic=topic),
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048,
            ),
        )
        agent1_response = handle_response(prompt_response)
        if agent1_response:
            parts = agent1_response.split("---")
            if len(parts) >= 2:
                refined_prompt = parts[0].replace("Refined Prompt", "").strip()
                framework = parts[1].strip()
                if framework.startswith("Investigation Framework"):
                    framework = framework[len("Investigation Framework"):].strip()

                # Fix formatting indentation
                framework_lines = framework.split("\n")
                cleaned_framework_lines = []
                for line in framework_lines:
                    if line.lstrip().startswith("-"):
                        cleaned_framework_lines.append(" " + line.lstrip())
                    else:
                        cleaned_framework_lines.append(line)
                framework = "\n".join(cleaned_framework_lines)

                logging.info("Refined prompt & framework generated successfully")
                return refined_prompt, framework
            else:
                logging.warning("Could not split Agent 1 response properly.")
                return None, None
        else:
            logging.warning("Agent 1 response was empty.")
    except Exception as e:
        logging.error(f"Failed to generate refined prompt & framework: {e}")
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
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,
                top_p=0.7,
                top_k=40,
                max_output_tokens=2048,
            ),
        )
        research = handle_response(prompt_response)
        if research:
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
            logging.info(f"Research phase {iteration} completed successfully.")
            return research
        else:
            logging.warning(f"Research phase {iteration} returned no content.")
    except Exception as e:
        logging.error(f"Failed to conduct research phase {iteration}: {e}")
    return None

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
    loops_num = 2

# ------------------ Main Button Logic ------------------ #
if start_button_clicked:
    if topic:
        # Reset relevant session states
        st.session_state.analysis_complete = False
        st.session_state.research_results = []
        st.session_state.random_fact = None

        # ------------------ STEP 0: Refining Prompt (Random Fact + Quick Summary) ------------------ #
        st.session_state.current_step = 0
        render_stepper(st.session_state.current_step)
        st.write("**Step 1**: Refining Prompt (Generating random fact & quick summary)...")

        try:
            random_fact = generate_random_fact(topic)
            if random_fact:
                st.session_state.random_fact = random_fact
                with st.expander("🎲 Random Fact", expanded=True):
                    st.markdown(random_fact)

            tldr_summary = generate_quick_summary(topic)
            if tldr_summary:
                st.session_state.tldr_summary = tldr_summary
                with st.expander("💡 TL;DR", expanded=True):
                    st.markdown(tldr_summary)

            st.success("Prompt refinement step done.")
        except Exception as e:
            st.error(f"Refining prompt failed: {str(e)}")
            logging.error(e)
            st.stop()

        # ------------------ STEP 1: Developing Framework (Agent 1) ------------------ #
        st.session_state.current_step = 1
        render_stepper(st.session_state.current_step)
        st.write("**Step 2**: Developing framework...")

        refined_prompt, framework = generate_refined_prompt_and_framework(topic)
        if refined_prompt and framework:
            st.session_state.refined_prompt = refined_prompt.strip()
            st.session_state.framework = framework.strip()

            with st.expander(f"🎯 Refined Prompt", expanded=False):
                st.markdown(st.session_state.refined_prompt)
            with st.expander(f"🗺️ Investigation Framework", expanded=False):
                st.markdown(st.session_state.framework)

            st.success("Framework developed.")
        else:
            st.warning("Could not develop framework from Agent 1. Stopping.")
            st.stop()

        # ------------------ STEP 2: Conducting Research (Agent 2) ------------------ #
        st.session_state.current_step = 2
        render_stepper(st.session_state.current_step)
        st.write("**Step 3**: Conducting research...")

        current_analysis = ""
        aspects = []
        research_expanders = []

        # Extract aspects from framework lines that begin with "1.", "2.", "3.", etc.
        for line in st.session_state.framework.split("\n"):
            if line.strip().startswith(("1.", "2.", "3.", "4.")):
                aspects.append(line.strip())

        for i in range(loops_num):
            current_aspect = random.choice(aspects) if aspects else "Current State and Trends"
            research = conduct_research(
                refined_prompt=st.session_state.refined_prompt,
                framework=st.session_state.framework,
                previous_analysis=current_analysis,
                current_aspect=current_aspect,
                iteration=i+1
            )
            if research:
                current_analysis += "\n\n" + research
                lines = research.split("\n")
                title = next((ln for ln in lines if ln.strip()), current_aspect)
                content = "\n".join(lines[1:])

                # Simple emoji logic
                title_lower = title.lower()
                if any(word in title_lower for word in ["extinct","survival","species","wildlife","bird","animal","habitat"]):
                    emoji = "🦅"
                elif any(word in title_lower for word in ["economic","finance","market","cost","price","value"]):
                    emoji = "📊"
                elif any(word in title_lower for word in ["environment","climate","ecosystem","nature","conservation"]):
                    emoji = "🌍"
                elif any(word in title_lower for word in ["culture","social","community","tradition","heritage"]):
                    emoji = "🎭"
                elif any(word in title_lower for word in ["history","historical","past","timeline","archive"]):
                    emoji = "📜"
                elif any(word in title_lower for word in ["technology","innovation","digital","software","data"]):
                    emoji = "💻"
                elif any(word in title_lower for word in ["education","learning","teaching","study","research"]):
                    emoji = "📚"
                elif any(word in title_lower for word in ["health","medical","disease","treatment","care"]):
                    emoji = "🏥"
                elif any(word in title_lower for word in ["evidence","sighting","observation","search","investigation"]):
                    emoji = "🔍"
                elif any(word in title_lower for word in ["methodology","approach","technique","method"]):
                    emoji = "🔬"
                elif any(word in title_lower for word in ["debate","controversy","argument","discussion"]):
                    emoji = "💭"
                elif any(word in title_lower for word in ["future","prediction","forecast","prospect"]):
                    emoji = "🔮"
                else:
                    emoji = "📝"
                
                research_expanders.append((f"{emoji} {title}", content))
            else:
                st.error(f"Research phase {i+1} failed or returned no content.")
                st.stop()

        # Show the research expanders
        for title, content in research_expanders:
            with st.expander(f"**{title}**", expanded=False):
                st.markdown(content)

        st.success("Research phase complete.")

        # ------------------ STEP 3: Final Report (Agent 3) ------------------ #
        st.session_state.current_step = 3
        render_stepper(st.session_state.current_step)
        st.write("**Step 4**: Generating final report...")

        final_response = model.generate_content(
            agent3_prompt.format(
                refined_prompt=st.session_state.refined_prompt,
                system_prompt=st.session_state.framework,
                all_aspect_analyses=current_analysis,
            ),
            generation_config=agent3_config,
        )
        final_analysis = handle_response(final_response)
        if final_analysis:
            st.session_state.final_analysis = final_analysis
            with st.expander(f"📋 Final Report", expanded=False):
                st.markdown(final_analysis)
            st.success("Final report generated.")
        else:
            st.error("Failed to generate final report.")
            st.stop()

        # Create PDF
        pdf_buffer = create_download_pdf(
            st.session_state.refined_prompt, 
            st.session_state.framework, 
            current_analysis, 
            final_analysis
        )
        st.session_state.pdf_buffer = pdf_buffer
        st.session_state.research_results = research_expanders

        # ------------------ STEP 4: Analysis Complete ------------------ #
        st.session_state.current_step = 4
        st.session_state.analysis_complete = True
        render_stepper(st.session_state.current_step)
        st.balloons()
        st.write("**Step 5**: Analysis complete! 🏆")

        # Download button
        _, download_col = st.columns([1, 2])
        with download_col:
            st.download_button(
                label="⬇️ Download Report as PDF",
                data=pdf_buffer,
                file_name=f"{topic}_analysis_report.pdf",
                mime="application/pdf",
                key="download_button",
                help="Download the complete analysis report as a PDF file",
                use_container_width=True
            )

    else:
        st.warning("Please enter a topic to analyze.")
