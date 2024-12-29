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

# STEP LABELS FOR YOUR WIZARD
STEPS = [
    "Refining Prompt",
    "Developing Framework",
    "Conducting Research",
    "Final Report",
    "Analysis Complete"
]

########################################
# FUNCTION: RENDER STEPPER
########################################
def render_stepper(current_step: int) -> None:
    """Renders a 5-step wizard with proper styling."""
    # Clamp current_step
    current_step = max(0, min(current_step, 4))
    
    # Create the CSS
    st.markdown("""
        <style>
        .stepper-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 1rem auto;
            padding: 1rem;
            max-width: 800px;
            background: transparent;
            position: relative;
        }
        .step {
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            flex: 1;
            min-width: 80px;
            max-width: 120px;
        }
        .step-number {
            width: 32px;
            height: 32px;
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
            font-size: 0.8rem;
            color: rgba(255, 255, 255, 0.6);
            text-align: center;
            max-width: 100px;
            word-wrap: break-word;
            position: relative;
            z-index: 2;
            line-height: 1.2;
        }
        .step-line {
            position: absolute;
            top: 16px;
            left: calc(50% + 20px);
            right: calc(-50% + 20px);
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
    """, unsafe_allow_html=True)
    
    # Create the HTML with minimal whitespace
    html_parts = ['<div class="stepper-container">']
    
    for i, label in enumerate(STEPS):
        status = "complete" if i < current_step else "active" if i == current_step else ""
        step_html = f'<div class="step {status}"><div class="step-number">{i + 1}</div><div class="step-label">{label}</div><div class="step-line"></div></div>'
        html_parts.append(step_html)
    
    html_parts.append('</div>')
    
    # Render the HTML
    st.markdown(''.join(html_parts), unsafe_allow_html=True)


########################################
# ORIGINAL STREAMLIT + LLM CODE
########################################

# Inject custom CSS (with no old wave bar)
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

# Initialize session state
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

# Get your GenAI key
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception as e:
    st.error(f"GOOGLE_API_KEY not found in secrets: {e}")
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

# --- Main Title ---
st.markdown(
    "<h1 class='main-title' data-title='Multi-Agent Reasoning Assistant a003'>M.A.R.A.</h1>",
    unsafe_allow_html=True
)

# ============ USER INPUT TOPIC ============
topic = st.text_input(
    "Enter a topic or question:",
    placeholder='e.g. "Is the Ivory-billed woodpecker really extinct?"',
    key="topic_input"
)

# If topic changes, reset states
if topic != st.session_state.previous_input:
    st.session_state.previous_input = topic
    st.session_state.analysis_complete = False
    st.session_state.current_step = 0
    st.session_state.final_analysis = None
    st.session_state.research_results = []
    st.session_state.tldr_summary = None
    st.session_state.refined_prompt = None
    st.session_state.framework = None

# If analysis is done, show step #5
if st.session_state.analysis_complete:
    st.session_state.current_step = 4

# ---------- EXPANDERS FOR PROMPTS ----------
with st.expander("**☠️ Advanced Prompt Customization ☠️**"):
    agent1_prompt = st.text_area(
        "Agent 1 Prompt (Prompt Engineer)",
        '''You are an expert prompt engineer. Your task is to:
1. Analyze the given topic
2. Create a refined, detailed prompt
3. Develop a structured framework for investigation

Topic: {topic}

Please format your response exactly as follows:

Refined Prompt:
[Your refined prompt here]
---
[Your investigation framework here with numbered points]''',
        height=250
    )
    agent2_prompt = st.text_area(
        "Agent 2 Prompt (Researcher)",
        '''Using the refined prompt and the framework...''',
        height=250
    )
    agent3_prompt = st.text_area(
        "Agent 3 Prompt (Expert Analyst)",
        '''Based on the completed analysis...''',
        height=250
    )

# Depth slider
loops = st.select_slider(
    "How deep should we dive?",
    options=["Puddle", "Lake", "Ocean", "Mariana Trench"],
    value="Lake",
)

# Start button
start_button = st.button("🌊 Dive In")

# -------------------- UTILITY FUNCTIONS --------------------
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

def generate_random_fact(topic):
    """Example: generate random interesting fact."""
    try:
        prompt = f"Give one short random fact about {topic}."
        resp = model.generate_content(prompt)
        return handle_response(resp)
    except Exception as e:
        logging.error(e)
    return None

def generate_quick_summary(topic):
    """Example: generate quick summary (TL;DR)."""
    try:
        prompt = f"Give a brief 1-2 sentence summary of {topic}."
        resp = model.generate_content(prompt)
        return handle_response(resp)
    except Exception as e:
        logging.error(e)
    return None

def generate_refined_prompt_and_framework(topic):
    """Example: call Agent 1 to refine prompt + framework."""
    try:
        text = agent1_prompt.format(topic=topic)
        resp = model.generate_content(text)
        ans = handle_response(resp)
        if ans and "---" in ans:
            parts = ans.split("---")
            refined_prompt = parts[0].replace("Refined Prompt", "").strip()
            framework = parts[1].strip()
            return refined_prompt, framework
    except Exception as e:
        logging.error(e)
    return None, None

def conduct_research(refined_prompt, framework, prev_analysis, aspect, iteration):
    """Example: call Agent 2 to do more research."""
    try:
        prompt = agent2_prompt.format(
            refined_prompt=refined_prompt,
            framework=framework,
            previous_analysis=prev_analysis,
            current_aspect=aspect
        )
        resp = model.generate_content(prompt)
        return handle_response(resp)
    except Exception as e:
        logging.error(e)
    return None

# Convert depth to number
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

# -------------------- MAIN LOGIC WHEN USER CLICKS BUTTON --------------------
if start_button:
    if not topic.strip():
        st.warning("Please enter a topic.")
    else:
        # Reset states relevant to analysis
        st.session_state.analysis_complete = False
        st.session_state.research_results = []
        st.session_state.random_fact = None
        st.session_state.current_step = 0

        # Show the step wizard once after the button
        render_stepper(st.session_state.current_step)

        # STEP 0: "Refining Prompt"
        st.session_state.current_step = 0

        # Example calls
        st.session_state.random_fact = generate_random_fact(topic)
        if st.session_state.random_fact:
            with st.expander("🎲 Random Fact", expanded=True):
                st.markdown(st.session_state.random_fact)

        st.session_state.tldr_summary = generate_quick_summary(topic)
        if st.session_state.tldr_summary:
            with st.expander("💡 TL;DR", expanded=True):
                st.markdown(st.session_state.tldr_summary)

        # STEP 1: "Developing Framework"
        st.session_state.current_step = 1

        try:
            refined, fw = generate_refined_prompt_and_framework(topic)
            if not refined or not fw:
                raise ValueError("Failed to generate refined prompt and framework")
                
            st.session_state.refined_prompt = refined
            st.session_state.framework = fw

            with st.expander("🎯 Refined Prompt", expanded=False):
                st.markdown(refined)
            with st.expander("🗺️ Investigation Framework", expanded=False):
                st.markdown(fw)

        except Exception as e:
            logging.error(f"Agent 1 error: {e}")
            st.error("An error occurred while generating the framework. Please try again.")
            st.stop()

        # STEP 2: "Conducting Research"
        st.session_state.current_step = 2

        current_analysis = ""
        aspects = []
        results_list = []

        # Extract aspect lines from framework
        for line in fw.split("\n"):
            if line.strip().startswith(("1.", "2.", "3.", "4.", "5.")):
                aspects.append(line.strip())

        if not aspects:
            st.error("No research aspects found in the framework.")
            st.stop()

        for i in range(loops_num):
            aspect = aspects[i % len(aspects)]  # Cycle through aspects instead of random choice
            research_txt = conduct_research(refined, fw, current_analysis, aspect, i+1)
            if research_txt:
                current_analysis += "\n\n" + research_txt
                lines = research_txt.split("\n")
                title = lines[0].strip() if lines else aspect
                content = "\n".join(lines[1:]) if len(lines) > 1 else research_txt
                results_list.append((title, content))
            else:
                st.error(f"Research iteration {i+1} failed. Please try again.")
                st.stop()

        # Show research results
        for title, content in results_list:
            with st.expander(title, expanded=False):
                st.markdown(content)

        st.session_state.research_results = results_list

        # STEP 3: "Final Report"
        st.session_state.current_step = 3

        # Generate final analysis
        try:
            final_prompt = agent3_prompt.format(
                refined_prompt=refined,
                framework=fw,
                research_results="\n\n".join([f"{title}\n{content}" for title, content in results_list])
            )
            resp = model.generate_content(final_prompt, generation_config=agent3_config)
            final_analysis = handle_response(resp)
            
            if not final_analysis:
                raise ValueError("No final analysis generated")
                
            st.session_state.final_analysis = final_analysis
            with st.expander("📋 Final Report", expanded=True):
                st.markdown(final_analysis)

        except Exception as e:
            logging.error(f"Final report error: {e}")
            st.error("An error occurred while generating the final report. Please try again.")
            st.stop()

        # Create PDF
        pdf_bytes = create_download_pdf(
            refined,
            fw,
            current_analysis,
            st.session_state.final_analysis
        )
        st.session_state.pdf_buffer = pdf_bytes

        # STEP 4: "Analysis Complete"
        st.session_state.current_step = 4
        st.session_state.analysis_complete = True

        # Download button
        st.download_button(
            "⬇️ Download Report as PDF",
            data=pdf_bytes,
            file_name=f"{topic}_analysis_report.pdf",
            mime="application/pdf",
            key="download_button"
        )
