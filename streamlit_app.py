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

# DEPTH CONFIGURATION
DEPTH_MAP = {
    "Puddle": 2,
    "Lake": 3,
    "Ocean": 4,
    "Mariana Trench": 5
}

# LLM CONFIGURATION
DEFAULT_GEN_CONFIG = genai.types.GenerationConfig(
    temperature=0.7,
    top_p=0.8,
    top_k=40,
    max_output_tokens=2048,
)

########################################
# GLOBAL STYLING
########################################
st.markdown("""
<style>
/* Container spacing */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 1rem !important;
    max-width: 800px;
}

/* Step Wizard Styles */
.step-box {
    background-color: rgba(32, 33, 35, 0.7) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 25px !important;
    padding: 8px 16px !important;
    text-align: center;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.step-box.active {
    border-color: #4c8bf5 !important;
    background-color: rgba(32, 33, 35, 0.9) !important;
    box-shadow: 0 0 10px rgba(76, 139, 245, 0.3);
}

.step-box.complete {
    background-color: #28a745 !important;
    border-color: #28a745 !important;
    box-shadow: 0 0 10px rgba(40, 167, 69, 0.3);
}

.step-label {
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.9rem;
    font-weight: 500;
    white-space: nowrap;
}

.step-box.active .step-label {
    color: #4c8bf5;
}

.step-box.complete .step-label {
    color: #28a745;
}

.step-connector {
    height: 2px !important;
    background-color: rgba(255, 255, 255, 0.1);
    margin-top: 20px !important;
}

.step-connector.active {
    background-color: #4c8bf5 !important;
}

.step-connector.complete {
    background-color: #28a745 !important;
}

/* UI Elements */
.streamlit-expanderHeader {
    font-size: 1rem;
    font-weight: 600;
    background-color: rgba(32, 33, 35, 0.7) !important;
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.stButton > button {
    width: 100%;
    padding: 0.5rem 1rem;
    font-size: 1rem;
    border-radius: 10px;
    background-color: rgba(76, 139, 245, 0.1);
    border: 1px solid #4c8bf5;
    color: #4c8bf5;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    background-color: rgba(76, 139, 245, 0.2);
}

.stSlider > div > div > div {
    background-color: #4c8bf5 !important;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: rgba(32, 33, 35, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    color: white;
    padding: 0.5rem 1rem;
}
</style>
""", unsafe_allow_html=True)

########################################
# STEP WIZARD RENDERING
########################################
def render_step_wizard(step: int):
    """Renders the step wizard with the current progress."""
    # Use columns for layout with proper spacing
    cols = st.columns([1, 0.15, 1, 0.15, 1, 0.15, 1])
    
    # Render each step and connector
    for i, (col, label) in enumerate(zip(cols[::2], STEPS)):
        status = "complete" if i < step else "active" if i == step else "inactive"
        
        # Render step box
        col.markdown(
            f'''
            <div class="step-box {status}" style="margin: 0 auto;">
                <div class="step-label">{label}</div>
            </div>
            ''',
            unsafe_allow_html=True
        )
        
        # Render connector (except after last step)
        if i < len(STEPS) - 1:
            cols[i*2 + 1].markdown(
                f'<div class="step-connector {status}"></div>',
                unsafe_allow_html=True
            )

########################################
# SETUP SESSION STATE
########################################
if 'state' not in st.session_state:
    st.session_state.state = {
        'current_step': 0,
        'random_fact': None,
        'tldr_summary': None,
        'refined_prompt': None,
        'framework': None,
        'research_results': [],
        'final_analysis': None,
        'pdf_buffer': None,
        'previous_topic': ""
    }

def reset_analysis_state():
    """Reset all analysis-related state variables."""
    st.session_state.state.update({
        'current_step': 0,
        'random_fact': None,
        'tldr_summary': None,
        'refined_prompt': None,
        'framework': None,
        'research_results': [],
        'final_analysis': None,
        'pdf_buffer': None
    })

########################################
# LLM FUNCTIONS
########################################
def handle_response(response):
    """Safely extract text from GenAI response."""
    try:
        if hasattr(response, "parts") and response.parts:
            for part in response.parts:
                if part.text:
                    return part.text.strip()
        elif hasattr(response, "text"):
            return response.text.strip()
        return ""
    except Exception as e:
        logging.error(f"Error handling response: {str(e)}")
        return ""

def generate_content(prompt: str, error_msg: str = "Generation failed") -> str:
    """Generate content with error handling and consistent configuration."""
    try:
        response = model.generate_content(prompt, generation_config=DEFAULT_GEN_CONFIG)
        result = handle_response(response)
        if not result:
            raise ValueError(error_msg)
        return result
    except Exception as e:
        logging.error(f"{error_msg}: {str(e)}")
        return None

def generate_random_fact(topic: str) -> str:
    """Generate an interesting fact about the topic."""
    prompt = f"""Generate one interesting and surprising fact about {topic}.
    Make it concise (1-2 sentences) and engaging.
    Focus on lesser-known aspects that would intrigue readers."""
    return generate_content(prompt, "Failed to generate random fact")

def generate_quick_summary(topic: str) -> str:
    """Generate a quick TL;DR summary about the topic."""
    prompt = f"""Provide a brief, clear summary of {topic} in 2-3 sentences.
    Focus on the most important aspects that someone should know.
    Keep it factual and objective."""
    return generate_content(prompt, "Failed to generate summary")

def generate_refined_prompt_and_framework(topic: str) -> tuple[str, str]:
    """Generate a refined prompt and research framework."""
    prompt = f"""As an expert prompt engineer, analyze {topic} and create:
    1. A refined, detailed prompt that will guide the research
    2. A structured framework for investigation (4-5 key aspects to explore)
    
    Format your response exactly as:
    
    Refined Prompt:
    [Your refined prompt here]
    ---
    [Your investigation framework with numbered points]"""
    
    text = generate_content(prompt, "Failed to generate framework")
    if not text or "---" not in text:
        return None, None
        
    parts = text.split("---")
    refined = parts[0].replace("Refined Prompt:", "").strip()
    framework = parts[1].strip()
    
    return refined, framework

def conduct_research(refined_prompt: str, framework: str, previous_analysis: str, aspect: str, iteration: int) -> str:
    """Conduct research on a specific aspect of the topic."""
    prompt = f"""You are a researcher analyzing this aspect:
    {aspect}
    
    Context:
    - Refined Research Prompt: {refined_prompt}
    - Research Framework: {framework}
    - Previous Research: {previous_analysis if previous_analysis else "No previous research yet."}
    
    Please provide a detailed analysis of this aspect that:
    1. Focuses on factual, verifiable information
    2. Cites sources where possible
    3. Maintains objectivity
    4. Connects findings to the overall research goal
    
    Format your response with clear headings and structure.
    Keep the analysis focused and relevant to the specific aspect being investigated."""
    
    return generate_content(prompt, f"Failed to generate research for iteration {iteration}")

########################################
# PDF GENERATION
########################################
def create_download_pdf(refined_prompt: str, framework: str, research_analysis: str, final_analysis: str) -> bytes:
    """Create a PDF report from the analysis results.
    
    Args:
        refined_prompt: The refined research prompt
        framework: The research framework
        research_analysis: The detailed research findings
        final_analysis: The final analysis and conclusions
        
    Returns:
        bytes: The PDF file contents
    """
    def sanitize_text(txt: str) -> str:
        """Sanitize text for PDF compatibility."""
        if not txt:
            return ""
        txt = txt.replace('—', '-').replace('–', '-')
        txt = txt.replace(''', "'").replace(''', "'").replace('…', '...')
        return ''.join(ch for ch in txt if ord(ch) < 128)

    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Analysis Report", ln=True, align="C")
        pdf.ln(10)

        # Sections
        sections = [
            ("Refined Prompt", refined_prompt),
            ("Investigation Framework", framework),
            ("Research Analysis", research_analysis),
            ("Final Analysis", final_analysis)
        ]
        
        for title, content in sections:
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, title, ln=True)
            pdf.set_font("Helvetica", size=12)
            pdf.multi_cell(0, 10, sanitize_text(content))
            pdf.ln(10)

        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        logging.error(f"Error creating PDF: {str(e)}")
        return None

########################################
# MAIN APP UI
########################################
st.title("M.A.R.A.")

# User input
topic = st.text_input("Enter a topic or question:", 
                      placeholder='e.g. "Is the Ivory-billed woodpecker really extinct?"')

# Topic change handling
if topic != st.session_state.state['previous_topic']:
    reset_analysis_state()
    st.session_state.state['previous_topic'] = topic

# Render step wizard once at the top
render_step_wizard(st.session_state.state['current_step'])

# Advanced prompt customization
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

# Depth selection
depth = st.select_slider(
    "How deep should we dive?", 
    ["Puddle", "Lake", "Ocean", "Mariana Trench"], 
    "Lake"
)

# Calculate loops based on depth
loops_num = DEPTH_MAP.get(depth, 3)  # Default to 3 if depth not found

# Start button
start_btn = st.button("🌊 Dive In")

########################################
# MAIN LOGIC
########################################
try:
    # Initialize LLM
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
except Exception as e:
    st.error("Missing or invalid GOOGLE_API_KEY.")
    st.stop()

if start_btn:
    if not topic.strip():
        st.warning("Please enter a topic.")
        st.stop()
    
    try:
        # Step 1: Initial Analysis
        st.session_state.state['current_step'] = 0
        
        with st.spinner("Generating initial insights..."):
            random_fact = generate_random_fact(topic)
            tldr_summary = generate_quick_summary(topic)
            
            if random_fact:
                st.session_state.state['random_fact'] = random_fact
                with st.expander("🎲 Random Fact", expanded=True):
                    st.markdown(random_fact)

            if tldr_summary:
                st.session_state.state['tldr_summary'] = tldr_summary
                with st.expander("💡 TL;DR", expanded=True):
                    st.markdown(tldr_summary)

        # Step 2: Framework Development
        st.session_state.state['current_step'] = 1
        
        with st.spinner("Developing research framework..."):
            refined_prompt, framework = generate_refined_prompt_and_framework(topic)
            if not refined_prompt or not framework:
                st.error("Could not generate research framework. Please try again.")
                st.stop()
            
            st.session_state.state['refined_prompt'] = refined_prompt
            st.session_state.state['framework'] = framework
            
            with st.expander("🎯 Refined Prompt", expanded=False):
                st.markdown(refined_prompt)
            with st.expander("🗺️ Investigation Framework", expanded=False):
                st.markdown(framework)

        # Step 3: Research Phase
        st.session_state.state['current_step'] = 2
        
        aspects = [line.strip() for line in framework.split("\n") 
                if line.strip().startswith(tuple(f"{x}." for x in range(1,10)))]
        
        if not aspects:
            st.error("Invalid research framework. Please try again.")
            st.stop()

        current_analysis = ""
        research_results = []
        
        with st.spinner("Conducting research..."):
            for i in range(loops_num):
                aspect = aspects[i % len(aspects)]
                with st.status(f"Researching aspect {i+1}/{loops_num}..."):
                    research_text = conduct_research(refined_prompt, framework, current_analysis, aspect, i+1)
                    
                    if not research_text:
                        st.error(f"Research failed for aspect: {aspect}")
                        st.stop()
                    
                    current_analysis += "\n\n" + research_text
                    
                    # Extract title and content
                    lines = research_text.split("\n")
                    title = lines[0].strip() if lines else aspect
                    content = "\n".join(lines[1:]) if len(lines) > 1 else research_text
                    
                    research_results.append((title, content))
                    
                    with st.expander(f"{i+1}. {title}", expanded=False):
                        st.markdown(content)
            
            st.session_state.state['research_results'] = research_results

        # Step 4: Final Analysis
        st.session_state.state['current_step'] = 3
        
        with st.spinner("Generating final analysis..."):
            combined_results = "\n\n".join(f"### {t}\n{c}" for t, c in research_results)
            final_prompt = f"""Based on all previous research conducted, please provide a comprehensive final analysis of {topic}.
            
            Here are the key findings from our research:
            
            {combined_results}
            
            Please synthesize these findings into a clear, well-organized final report that:
            1. Summarizes the key insights
            2. Identifies patterns and connections
            3. Draws meaningful conclusions
            4. Suggests potential implications or next steps
            
            Format the response in a clear, professional style with appropriate headings and structure."""
            
            final_analysis = generate_content(final_prompt, "Could not generate final analysis")
            if not final_analysis:
                st.error("Final analysis generation failed. Please try again.")
                st.stop()
            
            st.session_state.state['final_analysis'] = final_analysis
            with st.expander("📋 Final Report", expanded=True):
                st.markdown(final_analysis)

            # Generate PDF
            pdf_bytes = create_download_pdf(refined_prompt, framework, current_analysis, final_analysis)
            if pdf_bytes:
                st.session_state.state['pdf_buffer'] = pdf_bytes
                st.download_button(
                    label="⬇️ Download Report as PDF",
                    data=pdf_bytes,
                    file_name=f"{topic}_analysis_report.pdf",
                    mime="application/pdf",
                    key="download_button"
                )

        # Complete
        st.session_state.state['current_step'] = 4

    except Exception as e:
        logging.error(f"Error during analysis: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
        reset_analysis_state()
        st.stop()
