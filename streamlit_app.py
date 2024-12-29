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
def render_step_wizard(step: int):
    """Renders a single step wizard instance."""
    cols = st.columns([1, 0.2, 1, 0.2, 1, 0.2, 1])
    
    # Define styles as CSS classes in the main CSS block
    for i, (col, label) in enumerate(zip(cols[::2], STEPS)):
        # Determine step state
        if i < step:
            status = "complete"
        elif i == step:
            status = "active"
        else:
            status = "inactive"
        
        # Render step without number
        col.markdown(
            f'''
            <div class="step-box {status}">
                <div class="step-label">{label}</div>
            </div>
            ''',
            unsafe_allow_html=True
        )
        
        # Render connector (except for last step)
        if i < len(STEPS) - 1:
            cols[i*2 + 1].markdown(
                f'<div class="step-connector {status}"></div>',
                unsafe_allow_html=True
            )

# Update the main logic to handle step wizard display
def display_step_wizard():
    """Display step wizard in a container."""
    wizard_container = st.empty()
    with wizard_container:
        st.markdown('<div class="step-wizard-wrapper">', unsafe_allow_html=True)
        render_step_wizard(st.session_state.state['current_step'])
        st.markdown('</div>', unsafe_allow_html=True)
    return wizard_container

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
/* Step wizard spacing */
.step-wizard-container {
  margin-top: 20px;
  margin-bottom: 20px;
}
/* Step Wizard Styles */
.step-box {
    background-color: rgba(255, 255, 255, 0.1);
    border: 2px solid rgba(255, 255, 255, 0.2);
    color: rgba(255, 255, 255, 0.6);
    padding: 12px 20px;
    border-radius: 20px;
    text-align: center;
    transition: all 0.3s ease;
    margin: 0 5px;
}

.step-box.active {
    background-color: rgba(255, 255, 255, 0.1);
    border-color: #2439f7;
    color: white;
    box-shadow: 0 0 10px rgba(36, 57, 247, 0.3);
}

.step-box.complete {
    background-color: #28a745;
    border-color: #28a745;
    color: white;
    box-shadow: 0 0 10px rgba(40, 167, 69, 0.3);
}

.step-label {
    font-size: 0.9rem;
    font-weight: 500;
    white-space: nowrap;
}

.step-connector {
    height: 2px;
    background-color: rgba(255, 255, 255, 0.2);
    margin-top: 25px;
    transition: background-color 0.3s ease;
}

.step-connector.complete {
    background-color: #28a745;
    box-shadow: 0 0 5px rgba(40, 167, 69, 0.3);
}

/* Container for step wizard */
.step-wizard-wrapper {
    margin: 30px 0;
    padding: 20px 0;
    background-color: rgba(0, 0, 0, 0.2);
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# -------------- Session State --------------
if 'state' not in st.session_state:
    st.session_state.state = {
        'analysis_complete': False,
        'current_step': 0,
        'research_results': [],
        'random_fact': None,
        'tldr_summary': None,
        'refined_prompt': None,
        'framework': None,
        'previous_topic': "",
        'analysis_started': False,
        'pdf_buffer': None,
        'final_analysis': None
    }

def reset_analysis_state():
    """Centralized function to reset analysis state."""
    st.session_state.state.update({
        'analysis_complete': False,
        'current_step': 0,
        'research_results': [],
        'random_fact': None,
        'tldr_summary': None,
        'refined_prompt': None,
        'framework': None,
        'analysis_started': False,
        'pdf_buffer': None,
        'final_analysis': None
    })

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

# Advanced customization expander
with st.expander("Advanced Prompt Customization"):
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
depth = st.select_slider(
    "How deep should we dive?", 
    ["Puddle", "Lake", "Ocean", "Mariana Trench"], 
    "Lake"
)

# Calculate loops based on depth
loops_num = {
    "Puddle": 2,
    "Lake": 3,
    "Ocean": 4,
    "Mariana Trench": 5
}.get(depth, 3)  # Default to 3 if depth not found

# Start button
start_clicked = st.button("🌊 Dive In")

# If topic changes, reset
if topic != st.session_state.state['previous_topic']:
    reset_analysis_state()
    st.session_state.state['previous_topic'] = topic

# If done, step=4
if st.session_state.state['analysis_complete']:
    st.session_state.state['current_step'] = 4

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

# -------------- MAIN LOGIC --------------
# Topic change handling (only once at the top)
if topic != st.session_state.state['previous_topic']:
    reset_analysis_state()
    st.session_state.state['previous_topic'] = topic

# Initialize analysis
if start_clicked:
    if not topic.strip():
        st.warning("Please enter a topic.")
        st.stop()
    
    # Start new analysis and create step wizard container
    if not st.session_state.state['analysis_started']:
        st.session_state.state['analysis_started'] = True
        reset_analysis_state()
    
    # Create step wizard container FIRST
    wizard_container = st.container()
    with wizard_container:
        st.markdown('<div class="step-wizard-wrapper">', unsafe_allow_html=True)
        render_step_wizard(st.session_state.state['current_step'])
        st.markdown('</div>', unsafe_allow_html=True)
    
    try:
        # Step 1: Initial Analysis
        st.session_state.state['random_fact'] = generate_random_fact(topic)
        st.session_state.state['tldr_summary'] = generate_quick_summary(topic)

        if st.session_state.state['random_fact']:
            with st.expander("🎲 Random Fact", expanded=True):
                st.markdown(st.session_state.state['random_fact'])

        if st.session_state.state['tldr_summary']:
            with st.expander("💡 TL;DR", expanded=True):
                st.markdown(st.session_state.state['tldr_summary'])

        # Update Step 1
        st.session_state.state['current_step'] = 1
        with wizard_container:
            st.markdown('<div class="step-wizard-wrapper">', unsafe_allow_html=True)
            render_step_wizard(1)
            st.markdown('</div>', unsafe_allow_html=True)

        # Step 2: Framework Development
        refined_prompt, framework = generate_refined_prompt_and_framework(topic)
        if not refined_prompt or not framework:
            st.error("Could not generate refined prompt and framework. Please try again.")
            st.stop()

        st.session_state.state['refined_prompt'] = refined_prompt
        st.session_state.state['framework'] = framework

        with st.expander("🎯 Refined Prompt", expanded=False):
            st.markdown(refined_prompt)
        with st.expander("🗺️ Investigation Framework", expanded=False):
            st.markdown(framework)

        # Update Step 2
        st.session_state.state['current_step'] = 2
        with wizard_container:
            st.markdown('<div class="step-wizard-wrapper">', unsafe_allow_html=True)
            render_step_wizard(2)
            st.markdown('</div>', unsafe_allow_html=True)

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
                
        st.session_state.state['research_results'] = research_results_list
        
        # Update Step 3
        st.session_state.state['current_step'] = 3
        with wizard_container:
            st.markdown('<div class="step-wizard-wrapper">', unsafe_allow_html=True)
            render_step_wizard(3)
            st.markdown('</div>', unsafe_allow_html=True)

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
            
        st.session_state.state['final_analysis'] = final_analysis
        with st.expander("📋 Final Report", expanded=True):
            st.markdown(final_analysis)

        # Create PDF
        pdf_bytes = create_download_pdf(refined_prompt, framework, current_analysis, final_analysis)
        st.session_state.state['pdf_buffer'] = pdf_bytes

        # Update final step
        st.session_state.state['current_step'] = 4
        st.session_state.state['analysis_complete'] = True
        with wizard_container:
            st.markdown('<div class="step-wizard-wrapper">', unsafe_allow_html=True)
            render_step_wizard(4)
            st.markdown('</div>', unsafe_allow_html=True)

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
        reset_analysis_state()
        st.stop()

# Show existing step wizard if analysis is in progress
elif st.session_state.state['analysis_started']:
    wizard_container = st.container()
    with wizard_container:
        st.markdown('<div class="step-wizard-wrapper">', unsafe_allow_html=True)
        render_step_wizard(st.session_state.state['current_step'])
        st.markdown('</div>', unsafe_allow_html=True)
