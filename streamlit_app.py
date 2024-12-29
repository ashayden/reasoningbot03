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

# STEP DEFINITIONS
STEPS = [
    "Refining Prompt",
    "Developing Framework",
    "Conducting Research",
    "Analysis Complete"
]

########################################
# RENDERING THE STEP WIZARD
########################################
def render_step_wizard(current_step: int) -> None:
    """
    Renders the wizard once at the top.
    We have 4 steps in STEPS, so current_step can be 0..3.
    Steps < current_step => 'complete' (green)
    Step == current_step => 'active' (blue)
    Steps > current_step => 'inactive'
    """
    # Basic clamp
    current_step = max(0, min(current_step, len(STEPS)-1))

    # Create a row of columns for steps + connectors
    # If we have N steps, we need 2*N-1 columns: step, connector, step, connector, ...
    st.markdown('<div class="step-wizard-wrapper">', unsafe_allow_html=True)
    columns = st.columns(len(STEPS)*2 - 1)

    for i, label in enumerate(STEPS):
        # Determine step state
        if i < current_step:
            status = "complete"
        elif i == current_step:
            status = "active"
        else:
            status = "inactive"

        # Render step in columns[i*2]
        columns[i*2].markdown(
            f"""
            <div class="step-box {status}">
                <div class="step-label">{label}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # If not the last step, place connector
        if i < len(STEPS)-1:
            # If we have completed step i, we can also color the connector green
            # only if we also completed step i+1 (meaning i < current_step - 1).
            # But simplest approach: if i < current_step, connector is green
            connector_status = "complete" if i < current_step else "inactive"

            columns[i*2 + 1].markdown(
                f'<div class="step-connector {connector_status}"></div>',
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)

########################################
# HELPER: CREATE PDF
########################################
def create_download_pdf(refined_prompt, framework, research_analysis, final_analysis):
    """Create a PDF from the analysis results."""
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


########################################
# SETUP SESSION STATE
########################################
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
if "current_step" not in st.session_state:
    st.session_state.current_step = 0
if "random_fact" not in st.session_state:
    st.session_state.random_fact = None
if "tldr_summary" not in st.session_state:
    st.session_state.tldr_summary = None
if "refined_prompt" not in st.session_state:
    st.session_state.refined_prompt = None
if "framework" not in st.session_state:
    st.session_state.framework = None
if "research_results" not in st.session_state:
    st.session_state.research_results = []
if "final_analysis" not in st.session_state:
    st.session_state.final_analysis = None
if "pdf_buffer" not in st.session_state:
    st.session_state.pdf_buffer = None

# We'll store the previous topic so we can reset if the user changes it
if "previous_topic" not in st.session_state:
    st.session_state.previous_topic = ""


########################################
# LLM CONFIG
########################################
logging.info("Configuring Google GenAI...")

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
except:
    st.error("Missing or invalid GOOGLE_API_KEY.")
    st.stop()

########################################
# MAIN APP UI
########################################
st.title("M.A.R.A. (Streamlined Wizard)")

topic = st.text_input("Enter a topic or question:", 
                      placeholder='e.g. "Is the Ivory-billed woodpecker really extinct?"')

# If topic changes, reset everything
if topic != st.session_state.previous_topic:
    st.session_state.analysis_complete = False
    st.session_state.current_step = 0
    st.session_state.random_fact = None
    st.session_state.tldr_summary = None
    st.session_state.refined_prompt = None
    st.session_state.framework = None
    st.session_state.research_results = []
    st.session_state.final_analysis = None
    st.session_state.pdf_buffer = None
    st.session_state.previous_topic = topic

# RENDER THE WIZARD ONCE AT THE TOP
render_step_wizard(st.session_state.current_step)

# Advanced prompt customization
with st.expander("Advanced Prompt Customization"):
    agent1_prompt = st.text_area("Agent 1 Prompt", "You are an expert prompt engineer...", height=120)
    agent2_prompt = st.text_area("Agent 2 Prompt", "Using the refined prompt & framework...", height=120)
    agent3_prompt = st.text_area("Agent 3 Prompt", "Based on all previous research...", height=120)

# Depth
depth = st.select_slider("How deep should we dive?",
                         options=["Puddle","Lake","Ocean","Mariana Trench"],
                         value="Lake")

start_btn = st.button("🌊 Dive In")

# MAP DEPTH => LOOPS
depth_map = {
    "Puddle": 1,
    "Lake": 2,
    "Ocean": 3,
    "Mariana Trench": 4
}
loops_num = depth_map.get(depth, 2)

# -------------- LLM UTILITY EXAMPLES --------------
def handle_response(response):
    """Safely parse GenAI response text."""
    if hasattr(response, "parts") and response.parts:
        for part in response.parts:
            if part.text:
                return part.text.strip()
    elif hasattr(response, "text"):
        return response.text.strip()
    return ""

def generate_random_fact(topic):
    """Example random fact generation."""
    prompt = f"Give a random surprising fact about {topic}."
    resp = model.generate_content(prompt)
    return handle_response(resp)

def generate_quick_summary(topic):
    """Example summary generation."""
    prompt = f"Summarize {topic} in 1-2 sentences."
    resp = model.generate_content(prompt)
    return handle_response(resp)

def generate_refined_prompt_and_framework(topic):
    prompt = f"""You are an expert prompt engineer. Please generate:
Refined Prompt:
[Your refined prompt about {topic}]
---
[Investigation framework (4 or 5 bullet points)]
"""
    resp = model.generate_content(prompt)
    text = handle_response(resp)
    if not text or "---" not in text:
        return None, None

    parts = text.split("---")
    refined = parts[0].replace("Refined Prompt:", "").strip()
    fw = parts[1].strip()
    return refined, fw

def conduct_research(refined_prompt, framework, previous_analysis, aspect):
    prompt = f"""You are a researcher analyzing this aspect:
{aspect}
Refined Prompt: {refined_prompt}
Framework: {framework}
Previous Analysis: {previous_analysis}

Write a detailed analysis.
"""
    resp = model.generate_content(prompt)
    return handle_response(resp)

########################################
# MAIN LOGIC
########################################
if start_btn:
    if not topic.strip():
        st.warning("Please enter a topic.")
    else:
        try:
            # STEP 0 => "Refining Prompt"
            st.session_state.current_step = 0
            st.write("**Step 1**: Generating Random Fact & TL;DR")
            st.session_state.random_fact = generate_random_fact(topic)
            st.session_state.tldr_summary = generate_quick_summary(topic)

            if st.session_state.random_fact:
                with st.expander("🎲 Random Fact", expanded=True):
                    st.markdown(st.session_state.random_fact)

            if st.session_state.tldr_summary:
                with st.expander("💡 TL;DR", expanded=True):
                    st.markdown(st.session_state.tldr_summary)

            # Move on to next step => "Developing Framework"
            st.session_state.current_step = 1
            st.write("**Step 2**: Developing Framework (Agent 1)")

            refined_prompt, fw = generate_refined_prompt_and_framework(topic)
            if not refined_prompt or not fw:
                st.error("Could not generate prompt/framework. Stopping.")
                st.stop()

            st.session_state.refined_prompt = refined_prompt
            st.session_state.framework = fw

            with st.expander("🎯 Refined Prompt", expanded=False):
                st.markdown(refined_prompt)
            with st.expander("🗺️ Investigation Framework", expanded=False):
                st.markdown(fw)

            # Move on => "Conducting Research"
            st.session_state.current_step = 2
            st.write("**Step 3**: Conducting Research (Agent 2)")

            # Extract aspects from framework lines
            lines = fw.split("\n")
            aspects = []
            for line in lines:
                if line.strip().startswith(tuple(str(x)+"." for x in range(1,10))):
                    aspects.append(line.strip())

            current_analysis = ""
            research_list = []
            for i in range(loops_num):
                aspect = aspects[i % len(aspects)]
                result = conduct_research(refined_prompt, fw, current_analysis, aspect)
                if not result:
                    st.error(f"Could not conduct research for aspect: {aspect}")
                    st.stop()

                current_analysis += "\n\n" + result
                splitted = result.split("\n",1)
                title = splitted[0] if splitted else aspect
                content = splitted[1] if len(splitted) > 1 else result
                research_list.append((title, content))
                with st.expander(f"{i+1}. {title}", expanded=False):
                    st.markdown(content)

            st.session_state.research_results = research_list

            # Move on => "Analysis Complete"
            st.session_state.current_step = 3
            st.write("**Step 4**: Generating Final Report (Agent 3)")

            # Build final analysis
            combined = "\n\n".join(f"# {t}\n{c}" for t,c in research_list)
            final_prompt = f"""You are an expert analyst. Combine these results into a final report:
{combined}
"""
            final_resp = model.generate_content(final_prompt)
            final_analysis = handle_response(final_resp)
            if not final_analysis:
                st.error("No final analysis. Stopping.")
                st.stop()

            st.session_state.final_analysis = final_analysis
            with st.expander("📋 Final Report", expanded=True):
                st.markdown(final_analysis)

            # Create PDF
            pdf_data = create_download_pdf(refined_prompt, fw, current_analysis, final_analysis)
            st.session_state.pdf_buffer = pdf_data

            # Mark complete
            st.session_state.analysis_complete = True
            # current_step=3 is the final index in STEPS => "Analysis Complete"

            st.download_button(
                "⬇️ Download Report as PDF",
                data=pdf_data,
                file_name=f"{topic}_analysis.pdf",
                mime="application/pdf"
            )

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.stop()

# Add CSS at the top, after imports
st.markdown("""
<style>
/* Container for the entire wizard */
.step-wizard-wrapper {
    margin: 30px 0;
    padding: 20px 0;
    background-color: rgba(0,0,0,0.2);
    border-radius: 10px;
    position: relative;
    z-index: 1000;
}

/* Each step is a "pill" with border, color, etc. */
.step-box {
    background-color: rgba(255, 255, 255, 0.1);
    border: 2px solid rgba(255,255,255,0.2);
    color: rgba(255,255,255,0.6);
    padding: 12px 20px;
    border-radius: 20px;
    text-align: center;
    transition: all 0.3s ease;
    margin: 0 5px;
}

.step-box.active {
    background-color: rgba(255,255,255,0.1);
    border-color: #2439f7; /* Blue border */
    color: #fff;
    box-shadow: 0 0 10px rgba(36, 57, 247, 0.3);
}

.step-box.complete {
    background-color: #28a745; /* green */
    border-color: #28a745;
    color: #fff;
    box-shadow: 0 0 10px rgba(40, 167, 69, 0.3);
}

.step-label {
    font-size: 0.9rem;
    font-weight: 500;
    white-space: nowrap;
}

.step-connector {
    height: 2px;
    background-color: rgba(255,255,255,0.2);
    margin-top: 25px;
    transition: background-color 0.3s ease;
}

.step-connector.complete {
    background-color: #28a745;
    box-shadow: 0 0 5px rgba(40,167,69,0.3);
}

/* Fix for Streamlit containers */
[data-testid="stHorizontalBlock"] {
    background: transparent !important;
    gap: 0.5rem;
}

/* Add spacing after the step wizard */
.step-wizard-wrapper + div {
    margin-top: 20px;
}
</style>
""", unsafe_allow_html=True)
