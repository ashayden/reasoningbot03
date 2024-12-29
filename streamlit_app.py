import streamlit as st
import google.generativeai as genai
import time
import logging
import random
import io
from fpdf import FPDF

# Configure logging with debug level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Custom CSS for a minimal, modern slider design + your existing custom styles ---
st.markdown("""
<style>
/* Container spacing */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 1rem !important;
    max-width: 800px;
}

/* Minimal heading but with a subtle fade-on-hover tooltip */
.main-title {
    color: rgba(49, 51, 63, 0.9) !important;
    text-align: center !important;
    margin-bottom: 0.5rem !important;
    position: relative;
    cursor: help; /* Show "help" cursor to indicate there's a tooltip. */
}
.main-title:hover::after {
    content: attr(data-title); /* Show the hover text */
    position: absolute;
    top: 120%;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(36, 57, 247, 0.9);
    color: #fff;
    padding: 6px 10px;
    border-radius: 4px;
    white-space: nowrap;
    opacity: 0.95;
    font-size: 0.85rem;
    z-index: 999;
}

/* Subheader (optional) */
.subheader {
    font-size: 1.2rem !important;
    color: rgba(49, 51, 63, 0.8) !important;
    text-align: center !important;
    margin-bottom: 2rem !important;
}

/* Minimal slider styling for "Puddle, Lake, Ocean, Mariana Trench" */
.stSlider label {
    font-weight: 600;
    color: rgba(49, 51, 63, 0.8) !important;
}
.stSlider > div > div > div {
    height: 6px !important; /* Thinner track for a clean look */
    background: #d9e6ff !important;
    border-radius: 3px !important;
    position: relative;
    margin-bottom: 2rem !important;
}
.stSlider > div > div > div > div {
    width: 20px !important;
    height: 20px !important;
    border-radius: 50%;
    background: #2439f7 !important;
    border: 2px solid #ffffff;
    box-shadow: 0 0 0 4px rgba(36, 57, 247, 0.25);
    transition: transform 0.2s ease-in-out;
}
.stSlider > div > div > div > div:hover {
    transform: scale(1.2);
}
/* Slider label text */
.css-1wlzasp .css-1y4p8pa, 
.stSlider .css-1ez65nl {
    font-size: 0.9rem;
    color: #31333f;
    margin-top: 10px;
}

/* Buttons */
.stButton > button, [data-testid="stDownloadButton"] > button {
    width: 100%;
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    font-weight: 500;
    border-radius: 6px;
    border: none;
    background-color: #2439f7;
    color: white;
    transition: all 0.2s ease-in-out;
    margin: 0.5rem 0;
    text-transform: none;
    letter-spacing: 0.5px;
    box-shadow: none;
}
.stButton > button:hover, [data-testid="stDownloadButton"] > button:hover {
    background-color: #1a2bc4;
    transform: translateY(-1px);
}
.stButton > button:active, [data-testid="stDownloadButton"] > button:active {
    transform: translateY(1px);
}

/* Expander styling */
.streamlit-expanderHeader {
    font-size: 1rem;
    font-weight: 600;
    padding: 0.75rem 1rem;
    border-radius: 0.5rem;
    transition: background-color 0.2s ease-in-out, padding-left 0.2s ease-in-out;
    margin-top: 1rem;
}
.streamlit-expanderHeader:hover {
    background-color: rgba(36, 57, 247, 0.05);
    padding-left: 1.25rem;
}

/* Progress bar styling */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, 
        #007bff 0%, 
        #007bff 98%, 
        #007bff 100%
    );
    background-size: 200% 100%;
    animation: loading 2s linear infinite;
    border-radius: 0.5rem;
    height: 0.5rem !important;
    transition: width 0.4s ease-in-out, background-color 0.3s ease-in-out;
}
@keyframes loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}
/* Completed progress bar */
.progress-complete > div > div > div > div {
    background: #28a745 !important;
    animation: none;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------------
# Main Title (with hover text "Multi-Agent Reasoning Assistant a003")
# ----------------------------------------------------------------------------------
st.markdown(
    "<h1 class='main-title' data-title='Multi-Agent Reasoning Assistant a003'>M.A.R.A.</h1>",
    unsafe_allow_html=True
)

# Optional subheader
st.markdown("<p class='subheader'>Your multi-agent reasoning interface</p>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------------
# Retrieve & Configure API
# ----------------------------------------------------------------------------------
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception as e:
    logging.error(f"GOOGLE_API_KEY not found in Streamlit secrets: {e}")
    st.error(
        "⚠️ GOOGLE_API_KEY not found in Streamlit secrets! Make sure to add it in the Streamlit Cloud dashboard."
    )
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

# ----------------------------------------------------------------------------------
# Initialize Session State
# ----------------------------------------------------------------------------------
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

# ----------------------------------------------------------------------------------
# Slider: "Puddle", "Lake", "Ocean", "Mariana Trench"
# ----------------------------------------------------------------------------------
loops = st.select_slider(
    "How deep should we dive?",
    options=["Puddle", "Lake", "Ocean", "Mariana Trench"],
    value="Lake"
)
st.write(f"Selected depth: {loops}")

# Convert slider selection to number of loops
if loops == "Puddle":
    loops_num = 1
elif loops == "Lake":
    loops_num = random.randint(2, 3)
elif loops == "Ocean":
    loops_num = random.randint(4, 6)
elif loops == "Mariana Trench":
    loops_num = random.randint(7, 10)
else:
    loops_num = 2  # Default

# ----------------------------------------------------------------------------------
# Text input
# ----------------------------------------------------------------------------------
topic = st.text_input(
    "Enter a topic or question:",
    placeholder='e.g. "Is the Ivory-billed woodpecker really extinct?"',
    key="topic_input",
    on_change=lambda: st.session_state.update({"start_button_clicked": True})
        if st.session_state.topic_input else None,
)

# If topic changes, reset states
if topic != st.session_state.previous_input:
    st.session_state.analysis_complete = False
    st.session_state.pdf_buffer = None
    st.session_state.final_analysis = None
    st.session_state.research_results = []
    st.session_state.tldr_summary = None
    st.session_state.refined_prompt = None
    st.session_state.framework = None
    st.session_state.previous_input = topic

# ----------------------------------------------------------------------------------
# Button in the sidebar
# ----------------------------------------------------------------------------------
with st.sidebar:
    start_button_clicked = st.button("🌊 Dive In", key="start_button")
    if start_button_clicked:
        st.session_state.start_button_clicked = True

# ----------------------------------------------------------------------------------
# Helper Functions (Your multi-agent logic, PDF creation, etc. remain the same)
# ----------------------------------------------------------------------------------
def handle_response(response):
    """Handle model response and extract text with more specific error handling."""
    try:
        if hasattr(response, "parts") and response.parts:
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
        Provide a very brief, one to two-sentence TL;DR (Too Long; Didn't Read) overview of the following topic, incorporating emojis where relevant:
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

def generate_refined_prompt_and_framework(topic):
    """Generate a refined prompt and framework using Agent 1."""
    try:
        # Attempt to pull agent1_prompt from session or define inline
        agent1_prompt = st.session_state.get("agent1_prompt", None)
        if not agent1_prompt:
            # If you haven't defined it earlier or in session state, you can define it here:
            agent1_prompt = '''You are an expert prompt engineer...
[Insert the complete text of Agent 1 prompt here, or retrieve from your code]'''

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
                
                # Clean up
                framework = framework.replace("Core Question/Hypothesis:", "Core Question/Hypothesis")
                framework = framework.replace("Key Areas Requiring Investigation:", "Key Areas Requiring Investigation")
                
                # Align bullet points
                framework_lines = framework.split("\n")
                cleaned_framework_lines = []
                for line in framework_lines:
                    if line.lstrip().startswith("-"):
                        cleaned_framework_lines.append("   " + line.lstrip())
                    else:
                        cleaned_framework_lines.append(line)
                framework = "\n".join(cleaned_framework_lines)
                
                logging.info("Refined prompt and framework generated successfully")
                return refined_prompt, framework
            else:
                logging.warning("Could not properly split the response from Agent 1.")
                return None, None
        else:
            logging.warning("Agent 1 response was empty or invalid.")
            return None, None
    except Exception as e:
        logging.error(f"Failed to generate refined prompt and framework: {e}")
        return None, None

def conduct_research(refined_prompt, framework, previous_analysis, current_aspect, iteration):
    """Conduct research and analysis using Agent 2."""
    try:
        # Attempt to pull agent2_prompt from session or define inline
        agent2_prompt = st.session_state.get("agent2_prompt", None)
        if not agent2_prompt:
            # If you haven't defined it earlier, define it here:
            agent2_prompt = '''Using the refined prompt and the established framework...
[Insert the complete text of Agent 2 prompt here, or retrieve from your code]'''

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
            # Remove iteration focus lines
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

def create_download_pdf(refined_prompt, framework, research_analysis, final_analysis):
    """Create a PDF report from the analysis results."""
    try:
        def sanitize_text(text):
            """Clean text for PDF compatibility."""
            if not text:
                return ""
            # Replace problematic characters
            text = text.replace('—', '-')
            text = text.replace('–', '-')
            text = text.replace('"', '"')
            text = text.replace('’', "'")
            text = text.replace('‘', "'")
            text = text.replace('…', '...')
            # Remove emojis and other special characters
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
        
        # Research Analysis
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Research Analysis", ln=True)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, sanitize_text(research_analysis))
        pdf.ln(10)
        
        # Final Analysis
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

# ----------------------------------------------------------------------------------
# The main workflow: if user clicks "Dive In" & has a topic, run the analysis
# ----------------------------------------------------------------------------------
progress_placeholder = st.empty()

if st.session_state.start_button_clicked:
    st.session_state.start_button_clicked = False  # reset after we see it
    if topic:
        # Reset relevant state
        st.session_state.analysis_complete = False
        st.session_state.research_results = []
        st.session_state.random_fact = None
        
        # Create a progress bar
        progress_bar = st.progress(0)
        
        try:
            # 1) Generate a random fact
            random_fact = generate_random_fact(topic)
            if random_fact:
                st.session_state.random_fact = random_fact
                with st.expander("🎲 Random Fact", expanded=True):
                    st.markdown(random_fact)
                progress_bar.progress(10)
            
            # 2) Generate quick summary (TL;DR)
            tldr_summary = generate_quick_summary(topic)
            if tldr_summary:
                st.session_state.tldr_summary = tldr_summary
                with st.expander("💡 TL;DR", expanded=True):
                    st.markdown(tldr_summary)
                progress_bar.progress(20)
            
            # 3) Agent 1: refine prompt & framework
            refined_prompt, framework = generate_refined_prompt_and_framework(topic)
            if refined_prompt and framework:
                st.session_state.refined_prompt = refined_prompt
                st.session_state.framework = framework
                
                with st.expander(f"🎯 Refined Prompt", expanded=False):
                    st.markdown(refined_prompt)
                
                with st.expander(f"🗺️ Investigation Framework", expanded=False):
                    st.markdown(framework)
                progress_bar.progress(40)
                
                # 4) Agent 2: conduct research
                current_analysis = ""
                aspects = []
                research_expanders = []

                if framework:
                    for line in framework.split("\n"):
                        if line.strip().startswith(("1.", "2.", "3.", "4.")):
                            aspects.append(line.strip())

                for i in range(loops_num):
                    current_aspect = random.choice(aspects) if aspects else "Current State and Trends"
                    research = conduct_research(refined_prompt, framework, current_analysis, current_aspect, i + 1)
                    
                    if research:
                        current_analysis += "\n\n" + research
                        research_lines = research.split("\n")
                        title = next((ln for ln in research_lines if ln.strip()), current_aspect)
                        research_content = "\n".join(research_lines[1:])
                        
                        # A quick emoji-based approach:
                        title_lower = title.lower()
                        if any(word in title_lower for word in ["extinct", "survival", "species", "wildlife", "bird", "animal", "habitat"]):
                            emoji = "🦅"
                        elif any(word in title_lower for word in ["economic", "finance", "market", "cost", "price", "value"]):
                            emoji = "📊"
                        elif any(word in title_lower for word in ["environment", "climate", "ecosystem", "nature", "conservation"]):
                            emoji = "🌍"
                        elif any(word in title_lower for word in ["culture", "social", "community", "tradition", "heritage"]):
                            emoji = "🎭"
                        elif any(word in title_lower for word in ["history", "historical", "past", "timeline", "archive"]):
                            emoji = "📜"
                        elif any(word in title_lower for word in ["technology", "innovation", "digital", "software", "data"]):
                            emoji = "💻"
                        elif any(word in title_lower for word in ["education", "learning", "teaching", "study", "research"]):
                            emoji = "📚"
                        elif any(word in title_lower for word in ["health", "medical", "disease", "treatment", "care"]):
                            emoji = "🏥"
                        elif any(word in title_lower for word in ["evidence", "sighting", "observation", "search", "investigation"]):
                            emoji = "🔍"
                        elif any(word in title_lower for word in ["methodology", "approach", "technique", "method"]):
                            emoji = "🔬"
                        elif any(word in title_lower for word in ["debate", "controversy", "argument", "discussion"]):
                            emoji = "💭"
                        elif any(word in title_lower for word in ["future", "prediction", "forecast", "prospect"]):
                            emoji = "🔮"
                        else:
                            emoji = "📝"
                        
                        research_expanders.append((f"{emoji} {title}", research_content))
                        progress_bar.progress(40 + int((i + 1) / loops_num * 40))
                    else:
                        raise Exception(f"Research phase {i + 1} failed")

                # Show research expansions
                for title, content in research_expanders:
                    with st.expander(f"**{title}**", expanded=False):
                        st.markdown(content)
                
                # 5) Agent 3: final analysis
                agent3_prompt = st.session_state.get("agent3_prompt", None)
                if not agent3_prompt:
                    agent3_prompt = '''Based on the completed analysis of the topic...
[Insert the complete text of Agent 3 prompt here, or retrieve from your code]'''

                final_response = model.generate_content(
                    agent3_prompt.format(
                        refined_prompt=refined_prompt,
                        system_prompt=framework,
                        all_aspect_analyses=current_analysis,
                    ),
                    generation_config=agent3_config,
                )
                final_analysis = handle_response(final_response)
                
                # 6) Create a PDF
                pdf_buffer = create_download_pdf(refined_prompt, framework, current_analysis, final_analysis)

                st.session_state.research_results = research_expanders
                st.session_state.final_analysis = final_analysis
                st.session_state.pdf_buffer = pdf_buffer
                st.session_state.analysis_complete = True
                
                with st.expander(f"📋 Final Report", expanded=False):
                    st.markdown(final_analysis)
                
                # Complete progress bar
                progress_bar.progress(100)
                st.markdown(
                    """
                    <style>
                    .stProgress > div > div > div > div {
                        background: #28a745 !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )

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
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}. Please try again.")
            logging.error(f"Analysis failed: {e}")
            st.session_state.analysis_complete = False
    else:
        st.warning("Please enter a topic to analyze.")
