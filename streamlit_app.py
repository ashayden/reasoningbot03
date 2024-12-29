import streamlit as st
import google.generativeai as genai
import logging
import random
from fpdf import FPDF

########################################
# GLOBAL CONFIG & LOGGING
########################################
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# STEP LABELS FOR YOUR WIZARD
STEPS = [
    "Making a Plan",
    "Developing Framework",
    "Conducting Research",
    "Analysis Complete"
]

########################################
# FUNCTION: RENDER PROGRESS (Updated)
########################################
def render_progress_html(current_step: int) -> str:
    """Returns the HTML for a progress indicator."""
    html_parts = []
    for idx, step in enumerate(STEPS):
        # Determine status
        if idx < current_step:
            status = "✅"
            color = "green"
        elif idx == current_step:
            status = "🔄"
            color = "blue"
        else:
            status = "⭕"
            color = "gray"

        # Append HTML
        html_parts.append(
            f"<div style='text-align: center; margin: 0 10px;'>"
            f"<div style='color: {color}; font-size: 20px; margin-bottom: 5px;'>{status}</div>"
            f"<div style='color: {color}; font-size: 14px;'>{step}</div>"
            f"</div>"
        )

    # Combine into a single horizontal layout
    return f"<div style='display: flex; justify-content: center;'>{''.join(html_parts)}</div>"

########################################
# UTILITY FUNCTIONS
########################################
def handle_response(response):
    """Extract text from GenAI response."""
    if hasattr(response, "parts") and response.parts:
        for part in response.parts:
            if part.text:
                return part.text.strip()
    elif hasattr(response, "text"):
        return response.text.strip()
    return ""

def create_download_pdf(refined_prompt, framework, research_analysis, final_analysis):
    """Create a PDF from the analysis results."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)

        def sanitize_text(text):
            if not text:
                return ""
            text = text.replace('—', '-').replace('–', '-')
            text = text.replace('’', "'").replace('‘', "'").replace('…', '...')
            return ''.join(char for char in text if ord(char) < 128)

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
        pdf.cell(0, 10, f"Error creating PDF: {str(e)}", ln=True)
        return pdf.output(dest='S').encode('latin-1')

########################################
# ORIGINAL STREAMLIT + LLM CODE
########################################

# Inject custom CSS
st.markdown("""
<style>
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 1rem !important;
    max-width: 800px;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception as e:
    st.error(f"GOOGLE_API_KEY not found in secrets: {e}")
    st.stop()

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
except Exception as e:
    st.error(f"Error configuring Gemini API: {e}")
    st.stop()

# --- Main Title ---
st.markdown(
    "<h1 class='main-title' data-title='Multi-Agent Reasoning Assistant a003'>M.A.R.A.</h1>",
    unsafe_allow_html=True
)

# ============ USER INPUT TOPIC ============
topic = st.text_input(
    "Enter a topic or question:",
    placeholder='e.g. "Is the Ivory-billed woodpecker really extinct?"'
)

if topic != st.session_state.get('previous_input', ''):
    st.session_state.previous_input = topic
    st.session_state.analysis_complete = False
    st.session_state.current_step = 0

# Create a container for the progress indicator at the top level
progress_container = st.empty()

# Depth slider
loops = st.select_slider(
    "How deep should we dive?",
    options=["Puddle", "Lake", "Ocean", "Mariana Trench"],
    value="Lake",
)

# --- Advanced Prompt Customization ---
with st.expander("**☠️ Advanced Prompt Customization ☠️**"):
    agent1_prompt = st.text_area(
        "Agent 1 Prompt (Prompt Engineer)",
        '''You are an expert prompt engineer. Your task is to take the user's topic:
{topic}

1) Create a more refined prompt
2) Provide a structured investigation framework

Format exactly:
Refined Prompt:
[Your refined prompt here]
---
[Investigation framework with numbered items]
''',
        height=250
    )
    agent2_prompt = st.text_area(
        "Agent 2 Prompt (Researcher)",
        '''Using the following inputs:

REFINED PROMPT:
{refined_prompt}

FRAMEWORK:
{framework}

PREVIOUS ANALYSIS:
{previous_analysis}

CURRENT FOCUS:
{current_aspect}

Perform additional research and provide new findings. 
Include any relevant data, references, or analysis points. 
Begin your response with a short title, then detail your findings.
''',
        height=250
    )
    agent3_prompt = st.text_area(
        "Agent 3 Prompt (Expert Analyst)",
        '''Based on all previous research and analysis:

REFINED PROMPT:
{refined_prompt}

FRAMEWORK:
{framework}

ALL RESEARCH RESULTS:
{research_results}

You are an expert in this field. Provide a comprehensive final report covering:
- Key insights
- Conclusions
- Supporting evidence
- Recommendations

Write in a neutral, authoritative tone.
''',
        height=250
    )

# Button
start_button = st.button("\U0001F30A Dive In")

if start_button:
    if not topic.strip():
        st.warning("Please enter a topic.")
        st.stop()

    # Reset states
    st.session_state.update({
        'analysis_complete': False,
        'current_step': 0
    })

    # Show initial progress
    progress_container.markdown(render_progress_html(st.session_state.current_step), unsafe_allow_html=True)

    try:
        # Step 1: Initial Analysis
        st.session_state.current_step = 1
        progress_container.markdown(render_progress_html(st.session_state.current_step), unsafe_allow_html=True)

        # Step 2: Framework Development
        st.session_state.current_step = 2
        progress_container.markdown(render_progress_html(st.session_state.current_step), unsafe_allow_html=True)

        # Step 3: Research Phase
        st.session_state.current_step = 3
        progress_container.markdown(render_progress_html(st.session_state.current_step), unsafe_allow_html=True)

        # Step 4: Final Analysis
        st.session_state.current_step = 4
        st.session_state.analysis_complete = True
        progress_container.markdown(render_progress_html(st.session_state.current_step), unsafe_allow_html=True)

    except Exception as e:
        logging.error(f"Analysis error: {str(e)}")
        st.error("An error occurred during analysis. Please try again.")
        st.stop()
