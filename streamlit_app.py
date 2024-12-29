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
    "Analysis Complete"
]

########################################
# STEP WIZARD RENDERING
########################################
def render_stepper(current_step: int) -> None:
    """Renders a 4-step wizard with proper styling."""
    # Clamp current_step between 0 and 4 (4 is complete state)
    current_step = max(0, min(current_step, 4))
    
    # Create the CSS with improved transitions and states
    st.markdown("""
        <style>
        .stepper-container {
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 1rem auto;
            padding: 0.5rem;
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
            padding: 0 1rem;
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
            font-weight: 500;
            font-size: 0.9rem;
            position: relative;
            z-index: 2;
            transition: all 0.3s ease;
        }
        .step-label {
            font-size: 0.8rem;
            color: rgba(255, 255, 255, 0.6);
            text-align: center;
            margin-top: 0.5rem;
            font-weight: 400;
            position: relative;
            z-index: 2;
            transition: all 0.3s ease;
        }
        .step-line {
            position: absolute;
            top: 16px;
            left: calc(50% + 16px);
            right: calc(-50% + 16px);
            height: 2px;
            background: rgba(255, 255, 255, 0.2);
            z-index: 1;
            transition: background-color 0.3s ease;
        }
        .step.active .step-number {
            background-color: rgba(255, 255, 255, 0.9);
            border-color: #2439f7;
            color: #2439f7;
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
        .step.complete .step-label {
            color: rgba(255, 255, 255, 0.9);
        }
        .step:last-child .step-line {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Create the HTML with proper state handling
    html = '<div class="stepper-container">'
    
    for i, label in enumerate(STEPS):
        if i < current_step:
            status = "complete"
        elif i == current_step:
            status = "active"
        else:
            status = ""
        
        html += f'''
            <div class="step {status}">
                <div class="step-number">{i + 1}</div>
                <div class="step-label">{label}</div>
                <div class="step-line"></div>
            </div>
        '''
    
    html += '</div>'
    
    # Render the HTML
    st.markdown(html, unsafe_allow_html=True)

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
if 'step_wizard_container' not in st.session_state:
    st.session_state.step_wizard_container = None
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
    # Update step wizard to initial state
    if st.session_state.step_wizard_container:
        st.session_state.step_wizard_container.markdown(render_stepper(0), unsafe_allow_html=True)

# If done, step=4
if st.session_state.analysis_complete:
    st.session_state.current_step = 4

# -------------- Step Wizard --------------
# Remove initial step wizard display
# step_wizard = st.empty()
# step_wizard.markdown(render_stepper(st.session_state.current_step), unsafe_allow_html=True)

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

def generate_random_fact(topic: str) -> str:
    """Generate a random interesting fact about the topic."""
    try:
        prompt = f"""Generate one interesting and surprising fact about {topic}.
        Make it concise (1-2 sentences) and engaging.
        Focus on lesser-known aspects that would intrigue readers."""
        
        response = model.generate_content(prompt)
        return handle_response(response)
    except Exception as e:
        logging.error(f"Error generating random fact: {e}")
        return None

def generate_quick_summary(topic: str) -> str:
    """Generate a quick TL;DR summary about the topic."""
    try:
        prompt = f"""Provide a brief, clear summary of {topic} in 2-3 sentences.
        Focus on the most important aspects that someone should know.
        Keep it factual and objective."""
        
        response = model.generate_content(prompt)
        return handle_response(response)
    except Exception as e:
        logging.error(f"Error generating summary: {e}")
        return None

def generate_refined_prompt_and_framework(topic: str) -> tuple[str, str]:
    """Generate a refined prompt and research framework."""
    try:
        prompt = f"""As an expert prompt engineer, analyze {topic} and create:
        1. A refined, detailed prompt that will guide the research
        2. A structured framework for investigation (4-5 key aspects to explore)
        
        Format your response exactly as:
        
        Refined Prompt:
        [Your refined prompt here]
        ---
        [Your investigation framework with numbered points]"""
        
        response = model.generate_content(prompt)
        text = handle_response(response)
        
        if not text or "Refined Prompt:" not in text or "---" not in text:
            return None, None
            
        parts = text.split("---")
        refined = parts[0].replace("Refined Prompt:", "").strip()
        framework = parts[1].strip()
        
        return refined, framework
    except Exception as e:
        logging.error(f"Error generating framework: {e}")
        return None, None

def conduct_research(refined_prompt: str, framework: str, current_analysis: str, aspect: str, iteration: int) -> str:
    """Conduct research on a specific aspect of the topic."""
    try:
        # Create a more focused research prompt
        prompt = f"""You are a thorough researcher analyzing this aspect:
        {aspect}
        
        Context:
        - Refined Research Prompt: {refined_prompt}
        - Research Framework: {framework}
        - Previous Research: {current_analysis if current_analysis else "No previous research yet."}
        
        Please provide a detailed analysis of this aspect that:
        1. Focuses on factual, verifiable information
        2. Cites sources where possible
        3. Maintains objectivity
        4. Connects findings to the overall research goal
        
        Format your response with clear headings and structure.
        Keep the analysis focused and relevant to the specific aspect being investigated."""
        
        response = model.generate_content(prompt, generation_config=agent3_config)
        result = handle_response(response)
        
        if not result or len(result.strip()) < 50:  # Basic validation
            logging.error(f"Research iteration {iteration} returned insufficient content")
            return None
            
        return result
        
    except Exception as e:
        logging.error(f"Error in research iteration {iteration}: {str(e)}")
        return None

# Add loops_num variable
loops_num = {
    "Puddle": 2,
    "Lake": 3,
    "Ocean": 4,
    "Mariana Trench": 5
}.get(depth, 3)  # Default to 3 if depth not found

# -------------- MAIN LOGIC --------------
# Create step wizard container if it doesn't exist (only once)
if not st.session_state.step_wizard_container:
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    st.session_state.step_wizard_container = st.empty()

# Reset logic
if topic != st.session_state.previous_input:
    st.session_state.previous_input = topic
    st.session_state.analysis_complete = False
    st.session_state.current_step = 0
    st.session_state.final_analysis = None
    st.session_state.research_results = []
    st.session_state.tldr_summary = None
    st.session_state.refined_prompt = None
    st.session_state.framework = None
    # Update step wizard to initial state
    if st.session_state.step_wizard_container:
        st.session_state.step_wizard_container.markdown(render_stepper(0), unsafe_allow_html=True)

if start_clicked:
    if not topic.strip():
        st.warning("Please enter a topic.")
        st.stop()

    # Reset analysis states but keep the container
    st.session_state.update({
        'analysis_complete': False,
        'research_results': [],
        'random_fact': None,
        'current_step': 0
    })
    
    # Update step wizard to initial state
    st.session_state.step_wizard_container.markdown(render_stepper(0), unsafe_allow_html=True)

    try:
        # Step 1: Initial Analysis
        st.session_state.random_fact = generate_random_fact(topic)
        st.session_state.tldr_summary = generate_quick_summary(topic)

        if st.session_state.random_fact:
            with st.expander("🎲 Random Fact", expanded=True):
                st.markdown(st.session_state.random_fact)

        if st.session_state.tldr_summary:
            with st.expander("💡 TL;DR", expanded=True):
                st.markdown(st.session_state.tldr_summary)

        # Update Step 1 complete
        st.session_state.current_step = 1
        st.session_state.step_wizard_container.markdown(render_stepper(1), unsafe_allow_html=True)

        # Step 2: Framework Development
        refined_prompt, framework = generate_refined_prompt_and_framework(topic)
        if not refined_prompt or not framework:
            st.error("Could not generate refined prompt and framework. Please try again.")
            st.stop()

        st.session_state.refined_prompt = refined_prompt
        st.session_state.framework = framework

        with st.expander("🎯 Refined Prompt", expanded=False):
            st.markdown(refined_prompt)
        with st.expander("🗺️ Investigation Framework", expanded=False):
            st.markdown(framework)

        # Update Step 2 complete
        st.session_state.current_step = 2
        st.session_state.step_wizard_container.markdown(render_stepper(2), unsafe_allow_html=True)

        # Step 3: Research Phase
        aspects = [line.strip() for line in framework.split("\n") 
                if line.strip().startswith(tuple(f"{x}." for x in range(1,10)))]
        
        if not aspects:
            st.error("No research aspects found in the framework. Please try again.")
            st.stop()

        current_analysis = ""
        research_results_list = []
        
        for i in range(loops_num):
            aspect = aspects[i % len(aspects)]
            research_text = conduct_research(refined_prompt, framework, current_analysis, aspect, i+1)
            
            if not research_text:
                raise ValueError(f"Failed to generate research for aspect: {aspect}")
                
            current_analysis += "\n\n" + research_text
            
            # Extract title and content
            lines = research_text.split("\n")
            title = lines[0].strip() if lines else aspect
            content = "\n".join(lines[1:]) if len(lines) > 1 else research_text
            
            research_results_list.append((title, content))
            
            # Display research results
            with st.expander(f"{i+1}. {title}", expanded=False):
                st.markdown(content)
                
        st.session_state.research_results = research_results_list
        
        # Update Step 3 complete
        st.session_state.current_step = 3
        st.session_state.step_wizard_container.markdown(render_stepper(3), unsafe_allow_html=True)

        # Generate final report
        combined_results = "\n\n".join(f"### {t}\n{c}" for t, c in research_results_list)
        final_prompt = f"""Based on all previous research conducted, please provide a comprehensive final analysis of {topic}.
        
        Here are the key findings from our research:
        
        {combined_results}
        
        Please synthesize these findings into a clear, well-organized final report that:
        1. Summarizes the key insights
        2. Identifies patterns and connections
        3. Draws meaningful conclusions
        4. Suggests potential implications or next steps
        
        Format the response in a clear, professional style with appropriate headings and structure."""
        
        resp = model.generate_content(final_prompt, generation_config=agent3_config)
        final_analysis = handle_response(resp)
        
        if not final_analysis:
            st.error("Could not generate final report. Please try again.")
            st.stop()
            
        st.session_state.final_analysis = final_analysis
        with st.expander("📋 Final Report", expanded=True):
            st.markdown(final_analysis)

        # Create PDF
        pdf_bytes = create_download_pdf(refined_prompt, framework, current_analysis, final_analysis)
        st.session_state.pdf_buffer = pdf_bytes

        # Update final step complete
        st.session_state.current_step = 4
        st.session_state.analysis_complete = True
        st.session_state.step_wizard_container.markdown(render_stepper(4), unsafe_allow_html=True)

        # Show download button
        st.download_button(
            label="⬇️ Download Report as PDF",
            data=pdf_bytes,
            file_name=f"{topic}_analysis_report.pdf",
            mime="application/pdf",
            key="download_button"
        )

    except Exception as e:
        logging.error(f"Error during analysis: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
        st.stop()
