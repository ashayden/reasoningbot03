import streamlit as st
import google.generativeai as genai
import logging
import random
import io
from fpdf import FPDF

########################################
# GLOBAL CONFIG & LOGGING
########################################
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

STEPS = [
    "Refining Prompt",
    "Developing Framework",
    "Conducting Research",
    "Final Report",
    "Analysis Complete"
]

########################################
# STEP WIZARD RENDERING
########################################
def render_stepper(current_step: int) -> str:
    """Renders a 5-step wizard with proper styling."""
    # Clamp current_step
    current_step = max(0, min(current_step, 4))
    
    # Create the CSS and HTML
    css = """
        <style>
        .stepper-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 2rem auto;
            padding: 1rem 2rem;
            max-width: 700px;
            background: transparent;
            position: relative;
        }
        .step {
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            flex: 1;
            max-width: 140px;
            margin: 0 0.5rem;
        }
        .step-number {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background-color: rgba(255, 255, 255, 0.1);
            border: 2px solid rgba(255, 255, 255, 0.2);
            color: rgba(255, 255, 255, 0.6);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-bottom: 8px;
            z-index: 2;
            position: relative;
            transition: all 0.3s ease;
        }
        .step-label {
            font-size: 0.85rem;
            color: rgba(255, 255, 255, 0.6);
            text-align: center;
            max-width: 110px;
            word-wrap: break-word;
            position: relative;
            z-index: 2;
            line-height: 1.2;
            margin-top: 4px;
        }
        .step-line {
            position: absolute;
            top: 18px;
            left: calc(50% + 25px);
            right: calc(-50% + 25px);
            height: 2px;
            background-color: rgba(255, 255, 255, 0.2);
            z-index: 1;
        }
        .step.active .step-number {
            border-color: #2439f7;
            color: #2439f7;
            background-color: rgba(255, 255, 255, 0.9);
            box-shadow: 0 0 0 4px rgba(36, 57, 247, 0.1);
        }
        .step.active .step-label {
            color: rgba(255, 255, 255, 0.9);
            font-weight: 500;
        }
        .step.complete .step-number {
            background-color: #28a745;
            border-color: #28a745;
            color: white;
        }
        .step.complete .step-line {
            background-color: #28a745;
        }
        .step:last-child .step-line {
            display: none;
        }
        </style>
    """
    
    # Create the HTML with minimal whitespace
    html = '<div class="stepper-container">'
    
    for i, label in enumerate(STEPS):
        status = "complete" if i < current_step else "active" if i == current_step else ""
        html += f'<div class="step {status}"><div class="step-number">{i + 1}</div><div class="step-label">{label}</div><div class="step-line"></div></div>'
    
    html += '</div>'
    
    # Return the complete HTML
    return css + html

########################################
# MAIN APP + LLM CODE
########################################

# Basic CSS injection for your overall UI
st.markdown("""
<style>
/* Container spacing */
.block-container {
  padding-top: 2rem !important;
  padding-bottom: 1rem !important;
  max-width: 800px;
}
/* Tweak text input & button styling */
.stTextInput > div > div > input {
  padding: 0.5rem 1rem;
  font-size: 1rem;
  border-radius: 0.5rem;
}
.stButton > button {
  width: 100%;
  padding: 0.5rem 1rem;
  font-size: 1rem;
  border-radius: 0.5rem;
  margin: 0.5rem 0;
}
/* Expander headings */
.streamlit-expanderHeader {
  font-size: 1rem;
  font-weight: 600;
  padding: 0.75rem 0;
  border-radius: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# -------------- Session State --------------
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
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

# -------------- Configure LLM --------------
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception as e:
    st.error("GOOGLE_API_KEY not found in secrets.")
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
    st.error(f"Error configuring Gemini API: {e}")
    st.stop()

# -------------- Title --------------
st.markdown("<h1 style='text-align:center;'>M.A.R.A.</h1>", unsafe_allow_html=True)

# -------------- User Input --------------
topic = st.text_input("Enter a topic or question:", 
                      placeholder='e.g. "Is the Ivory-billed woodpecker really extinct?"')

# If topic changes, reset
if topic != st.session_state.previous_input:
    st.session_state.previous_input = topic
    st.session_state.analysis_complete = False
    st.session_state.current_step = 0
    st.session_state.final_analysis = None
    st.session_state.research_results = []
    st.session_state.tldr_summary = None
    st.session_state.refined_prompt = None
    st.session_state.framework = None

# If done, step=4
if st.session_state.analysis_complete:
    st.session_state.current_step = 4

# -------------- Step Wizard --------------
step_wizard = st.empty()
step_wizard.markdown(render_stepper(st.session_state.current_step), unsafe_allow_html=True)

# Expanders for advanced customization
with st.expander("**Advanced Prompt Customization**"):
    agent1_prompt = st.text_area(
        "Agent 1 Prompt (Prompt Engineer)",
        "You are an expert prompt engineer...\nRefined Prompt:\n---\n",
        height=150
    )
    agent2_prompt = st.text_area(
        "Agent 2 Prompt (Researcher)",
        "Using the refined prompt & framework...\n",
        height=150
    )
    agent3_prompt = st.text_area(
        "Agent 3 Prompt (Expert Analyst)",
        "Based on all previous research...\n",
        height=150
    )

# Depth slider
depth = st.select_slider("How deep should we dive?", 
                         ["Puddle", "Lake", "Ocean", "Mariana Trench"], 
                         "Lake")

# Start button
start_clicked = st.button("🌊 Dive In")

# -------------- Utility Functions --------------
def handle_response(response):
    """Safely extract text from GenAI response."""
    if hasattr(response, "parts") and response.parts:
        for part in response.parts:
            if part.text:
                return part.text.strip()
    elif hasattr(response, "text"):
        return response.text.strip()
    return ""

def create_download_pdf(refined_prompt, framework, research_analysis, final_analysis):
    """Create PDF from analysis results."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    def sanitize_text(txt):
        if not txt:
            return ""
        txt = txt.replace('—', '-').replace('–', '-')
        txt = txt.replace('’', "'").replace('‘', "'").replace('…', '...')
        return ''.join(ch for ch in txt if ord(ch) < 128)

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Analysis Report", ln=True, align="C")
    pdf.ln(10)

    # Refined Prompt
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


# -------------- MAIN LOGIC --------------
if start_clicked:
    if not topic.strip():
        st.warning("Please enter a topic to analyze.")
    else:
        # Example: progress steps
        st.session_state.analysis_complete = False
        st.session_state.current_step = 0
        step_wizard.markdown(render_stepper(st.session_state.current_step), unsafe_allow_html=True)

        # Step 0: random fact & summary
        # (Pretend to do LLM calls here)
        st.subheader("Step 1: Refining Prompt")

        random_fact = f"Fun Fact about {topic}..."
        st.expander("🎲 Random Fact", expanded=True).write(random_fact)

        summary = f"A quick summary for {topic}..."
        st.expander("💡 TL;DR", expanded=True).write(summary)

        # Step 1: refine prompt
        st.session_state.current_step = 1
        step_wizard.markdown(render_stepper(st.session_state.current_step), unsafe_allow_html=True)
        st.subheader("Step 2: Developing Framework")

        # Suppose agent1 returns these
        refined_prompt = f"My refined prompt for {topic}"
        framework = f"1. Explore history\n2. Key factors\n3. Potential challenges"

        st.expander("🎯 Refined Prompt", expanded=False).write(refined_prompt)
        st.expander("🗺️ Investigation Framework", expanded=False).write(framework)

        # Step 2: conduct research
        st.session_state.current_step = 2
        step_wizard.markdown(render_stepper(st.session_state.current_step), unsafe_allow_html=True)
        st.subheader("Step 3: Conducting Research")

        # Suppose agent2 does multiple loops
        research_content = "Some research findings..."
        st.expander("Research Title", expanded=False).write(research_content)
        
        # Step 3: final report
        st.session_state.current_step = 3
        step_wizard.markdown(render_stepper(st.session_state.current_step), unsafe_allow_html=True)
        st.subheader("Step 4: Final Report")

        final_report = f"Here is the final report about {topic}..."
        st.expander("📋 Final Report", expanded=True).write(final_report)

        # Create PDF
        pdf_buf = create_download_pdf(refined_prompt, framework, research_content, final_report)
        st.session_state.pdf_buffer = pdf_buf

        # Step 4: done
        st.session_state.current_step = 4
        st.session_state.analysis_complete = True
        step_wizard.markdown(render_stepper(st.session_state.current_step), unsafe_allow_html=True)

        st.download_button(
            label="Download Report as PDF",
            data=pdf_buf,
            file_name=f"{topic}_analysis_report.pdf",
            mime="application/pdf",
            key="download_button"
        )
