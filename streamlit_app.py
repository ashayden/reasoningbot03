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

# Initialize LLM
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    agent3_config = genai.types.GenerationConfig(
        temperature=0.7,
        top_p=0.8,
        top_k=40,
        max_output_tokens=2048,
    )
except Exception as e:
    st.error("Failed to initialize LLM: Check your API key")
    logging.error(f"LLM initialization error: {str(e)}")
    model = None
    agent3_config = None

# STEP DEFINITIONS
STEPS = [
    "Refining Prompt",
    "Developing Framework",
    "Conducting Research",
    "Analysis Complete"
]

# DEPTH CONFIGURATION
DEPTH_MAP = {
    "Puddle": 1,
    "Lake": (2, 3),
    "Ocean": (4, 6),
    "Mariana Trench": (7, 10)
}

# DEFAULT PROMPTS
DEFAULT_PROMPTS = {
    "agent1": '''You are an expert prompt engineer. Your task is to take the user's topic:
{topic}

1) Create a more refined prompt
2) Provide a structured investigation framework

Format exactly:
Refined Prompt:
[Your refined prompt here]
---
[Investigation framework with numbered items]
''',
    "agent2": '''Using the following inputs:

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
    "agent3": '''Based on all previous research and analysis:

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
'''
}

########################################
# SETUP SESSION STATE
########################################
def init_session_state():
    """Initialize all session state variables."""
    if 'state' not in st.session_state:
        st.session_state.state = {
            'current_step': 0,
            'analysis_complete': False,
            'random_fact': None,
            'tldr_summary': None,
            'refined_prompt': None,
            'framework': None,
            'research_results': [],
            'final_analysis': None,
            'pdf_buffer': None,
            'previous_input': ""
        }
    return st.session_state.state

def reset_analysis_state():
    """Reset analysis-related state variables."""
    if 'state' not in st.session_state:
        init_session_state()
    
    st.session_state.state.update({
        'current_step': 0,
        'analysis_complete': False,
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
def check_llm_initialized():
    """Check if LLM is properly initialized."""
    if model is None or agent3_config is None:
        st.error("LLM not properly initialized. Please check your API key.")
        st.stop()

def handle_response(response) -> str:
    """Extract text from GenAI response safely."""
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

def generate_content(prompt: str, error_msg: str = "Generation failed", config=None) -> str:
    """Generate content with error handling and consistent configuration."""
    check_llm_initialized()
    try:
        response = model.generate_content(prompt, generation_config=config or agent3_config)
        result = handle_response(response)
        if not result:
            raise ValueError(error_msg)
        return result
    except Exception as e:
        logging.error(f"{error_msg}: {str(e)}")
        return None

def generate_random_fact(topic: str) -> str:
    """Generate a random interesting fact about the topic."""
    prompt = f"Give a short and surprising fact about {topic} in one sentence."
    return generate_content(prompt, "Failed to generate random fact")

def generate_quick_summary(topic: str) -> str:
    """Generate a quick summary about the topic."""
    prompt = f"Give a concise 1-2 sentence summary about {topic}."
    return generate_content(prompt, "Failed to generate summary")

def generate_refined_prompt_and_framework(topic: str) -> tuple[str, str]:
    """Generate a refined prompt and research framework."""
    text = DEFAULT_PROMPTS["agent1"].format(topic=topic)
    result = generate_content(text, "Failed to generate framework")
    
    if not result or "---" not in result:
        return None, None
        
    parts = result.split("---")
    refined = parts[0].replace("Refined Prompt:", "").strip()
    framework = parts[1].strip()
    
    return refined, framework

def conduct_research(refined_prompt: str, framework: str, prev_analysis: str, aspect: str, iteration: int) -> str:
    """Conduct research on a specific aspect."""
    prompt = DEFAULT_PROMPTS["agent2"].format(
        refined_prompt=refined_prompt,
        framework=framework,
        previous_analysis=prev_analysis,
        current_aspect=aspect
    )
    return generate_content(prompt, f"Failed to generate research for iteration {iteration}")

########################################
# PDF GENERATION
########################################
def create_download_pdf(refined_prompt: str, framework: str, research_analysis: str, final_analysis: str) -> bytes:
    """Create a PDF report from the analysis results."""
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
# UI COMPONENTS
########################################
def render_stepper(current_step: int) -> str:
    """Render the step wizard with current progress."""
    current_step = max(0, min(current_step, len(STEPS)))
    
    html = """
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
    
    html_parts = [
        '<div class="stepper-container">',
        *[f'<div class="step {status}"><div class="step-number">{i + 1}</div><div class="step-label">{label}</div><div class="step-line"></div></div>'
          for i, label in enumerate(STEPS)
          for status in ["complete" if i < current_step else "active" if i == current_step else ""]],
        '</div>'
    ]
    
    return html + ''.join(html_parts)

def render_ui_components():
    """Render the main UI components."""
    st.markdown(
        "<h1 class='main-title' data-title='Multi-Agent Reasoning Assistant'>M.A.R.A.</h1>",
        unsafe_allow_html=True
    )
    
    topic = st.text_input(
        "Enter a topic or question:",
        placeholder='e.g. "Is the Ivory-billed woodpecker really extinct?"'
    )
    
    with st.expander("**☠️ Advanced Prompt Customization ☠️**"):
        agent1_prompt = st.text_area(
            "Agent 1 Prompt (Prompt Engineer)",
            DEFAULT_PROMPTS["agent1"],
            height=250
        )
        agent2_prompt = st.text_area(
            "Agent 2 Prompt (Researcher)",
            DEFAULT_PROMPTS["agent2"],
            height=250
        )
        agent3_prompt = st.text_area(
            "Agent 3 Prompt (Expert Analyst)",
            DEFAULT_PROMPTS["agent3"],
            height=250
        )
    
    depth = st.select_slider(
        "How deep should we dive?",
        options=list(DEPTH_MAP.keys()),
        value="Lake"
    )
    
    start_button = st.button("🌊 Dive In")
    
    return topic, depth, start_button, (agent1_prompt, agent2_prompt, agent3_prompt)

########################################
# MAIN APP LOGIC
########################################
def main():
    """Main application logic."""
    # Initialize state
    state = init_session_state()
    
    # Check LLM initialization
    check_llm_initialized()
    
    # Render UI
    topic, depth, start_button, prompts = render_ui_components()
    
    # Handle topic change
    if topic != state.get('previous_input', ''):
        reset_analysis_state()
        state['previous_input'] = topic
    
    # Create step wizard container
    step_container = st.empty()
    step_container.markdown(render_stepper(state['current_step']), unsafe_allow_html=True)
    
    if start_button:
        if not topic.strip():
            st.warning("Please enter a topic.")
            st.stop()
        
        try:
            # Calculate iterations
            depth_range = DEPTH_MAP[depth]
            loops_num = (
                depth_range if isinstance(depth_range, int)
                else random.randint(*depth_range)
            )
            
            # Step 1: Initial Analysis
            with st.spinner("Generating initial insights..."):
                random_fact = generate_random_fact(topic)
                tldr_summary = generate_quick_summary(topic)
                
                if random_fact:
                    state['random_fact'] = random_fact
                    with st.expander("🎲 Random Fact", expanded=True):
                        st.markdown(random_fact)
                
                if tldr_summary:
                    state['tldr_summary'] = tldr_summary
                    with st.expander("💡 TL;DR", expanded=True):
                        st.markdown(tldr_summary)
            
            state['current_step'] = 1
            step_container.markdown(render_stepper(state['current_step']), unsafe_allow_html=True)
            
            # Step 2: Framework Development
            with st.spinner("Developing research framework..."):
                refined_prompt, framework = generate_refined_prompt_and_framework(topic)
                if not refined_prompt or not framework:
                    st.error("Framework generation failed. Please try again.")
                    st.stop()
                
                state.update({
                    'refined_prompt': refined_prompt,
                    'framework': framework
                })
                
                with st.expander("🎯 Refined Prompt", expanded=False):
                    st.markdown(refined_prompt)
                with st.expander("🗺️ Investigation Framework", expanded=False):
                    st.markdown(framework)
            
            state['current_step'] = 2
            step_container.markdown(render_stepper(state['current_step']), unsafe_allow_html=True)
            
            # Step 3: Research Phase
            aspects = [line.strip() for line in framework.split("\n") 
                    if line.strip().startswith(tuple(f"{x}." for x in range(1,10)))]
            
            if not aspects:
                st.error("Invalid framework format. Please try again.")
                st.stop()
            
            current_analysis = ""
            research_results = []
            
            with st.spinner("Conducting research..."):
                for i in range(loops_num):
                    aspect = aspects[i % len(aspects)]
                    with st.status(f"Researching aspect {i+1}/{loops_num}..."):
                        research_text = conduct_research(
                            refined_prompt, framework, current_analysis, aspect, i+1
                        )
                        
                        if not research_text:
                            st.error(f"Research failed for aspect: {aspect}")
                            st.stop()
                        
                        current_analysis += "\n\n" + research_text
                        
                        # Parse research text
                        lines = research_text.split("\n")
                        title = lines[0].strip() if lines else aspect
                        content = "\n".join(lines[1:]) if len(lines) > 1 else research_text
                        
                        research_results.append((title, content))
                        
                        with st.expander(f"{i+1}. {title}", expanded=False):
                            st.markdown(content)
                
                state['research_results'] = research_results
            
            state['current_step'] = 3
            step_container.markdown(render_stepper(state['current_step']), unsafe_allow_html=True)
            
            # Step 4: Final Analysis
            with st.spinner("Generating final analysis..."):
                combined_results = "\n\n".join(f"### {t}\n{c}" for t, c in research_results)
                final_prompt = DEFAULT_PROMPTS["agent3"].format(
                    refined_prompt=refined_prompt,
                    framework=framework,
                    research_results=combined_results
                )
                
                final_analysis = generate_content(
                    final_prompt,
                    "Final analysis generation failed",
                    agent3_config
                )
                
                if not final_analysis:
                    st.error("Final analysis failed. Please try again.")
                    st.stop()
                
                state['final_analysis'] = final_analysis
                with st.expander("📋 Final Report", expanded=True):
                    st.markdown(final_analysis)
                
                # Generate PDF
                pdf_bytes = create_download_pdf(
                    refined_prompt, framework, current_analysis, final_analysis
                )
                
                if pdf_bytes:
                    state['pdf_buffer'] = pdf_bytes
                    st.download_button(
                        label="⬇️ Download Report as PDF",
                        data=pdf_bytes,
                        file_name=f"{topic}_analysis_report.pdf",
                        mime="application/pdf",
                        key="download_button"
                    )
            
            # Complete
            state.update({
                'current_step': 4,
                'analysis_complete': True
            })
            step_container.markdown(render_stepper(state['current_step']), unsafe_allow_html=True)
            
        except Exception as e:
            logging.error(f"Analysis error: {str(e)}")
            st.error("An error occurred during analysis. Please try again.")
            reset_analysis_state()
            st.stop()

if __name__ == "__main__":
    main()
