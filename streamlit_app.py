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

# --- Custom CSS for Streamlit ---
# NOTE: Retained your custom CSS, with some repeated sections removed and minor tidying.
st.markdown("""
<style>
/* More compact spacing */
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
    transition: border-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}
.stTextInput > div > div > input:focus {
    border-color: #2439f7;
    box-shadow: 0 0 0 1px #2439f7;
}

/* Button styling & base */
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
    box-shadow: none;
    margin: 0.5rem 0;
    text-transform: none;
    letter-spacing: 0.5px;
}
/* Button hover effects */
.stButton > button:hover, [data-testid="stDownloadButton"] > button:hover {
    background-color: #1a2bc4;
    transform: translateY(-1px);
}
/* Button active effects */
.stButton > button:active, [data-testid="stDownloadButton"] > button:active {
    transform: translateY(1px);
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

/* Expander styling */
.streamlit-expanderHeader {
    font-size: 1rem;
    font-weight: 600;
    padding: 0.75rem 0;
    border-radius: 0.5rem;
    transition: background-color 0.2s ease-in-out, padding-left 0.2s ease-in-out;
    padding: 0.75rem 1rem;
}
.streamlit-expanderHeader:hover {
    background-color: rgba(36, 57, 247, 0.1);
    padding-left: 1.25rem;
}

/* Slider styling */
.stSlider > div > div > div {
    height: 0.5rem !important;
}
.stSlider > div > div > div > div {
    height: 1rem !important;
    width: 1rem !important;
    transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}
.stSlider > div > div > div > div:hover {
    transform: scale(1.2);
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

/* Advanced prompt customization button styling */
[data-testid="stExpander"] {
    border: none !important;
    box-shadow: none !important;
    background-color: transparent !important;
    border-radius: 6px !important;
    margin-bottom: 1rem !important;
    width: auto !important;
    min-width: 50px !important;
    float: right !important;
}
/* Target the block container of the expander */
[data-testid="stExpander"] > .st-emotion-cache-1q1n0ol {
    background-color: transparent !important;
}
/* Target the expander content */
[data-testid="stExpander"] > .st-emotion-cache-1ehh7ok {
    background-color: transparent !important;
}

/* Subheader styling */
.subheader {
    font-size: 1.2rem !important;
    margin-bottom: 2rem !important;
    text-align: center !important;
}

/* Headings and text color fixes for consistent readability */
.main-title {
    color: rgba(49, 51, 63, 0.9) !important;
    text-align: center !important;
    margin-bottom: 0.5rem !important;
}
.subheader {
    color: rgba(49, 51, 63, 0.8) !important;
}
.stTextInput label, .stTextArea label, .stSlider label {
    color: rgba(49, 51, 63, 0.8) !important;
}
[data-testid="stExpander"] {
    color: rgba(49, 51, 63, 0.9) !important;
}
.stMarkdown {
    color: rgba(49, 51, 63, 0.9) !important;
}
[data-testid="stExpander"] textarea {
    background-color: rgba(255, 255, 255, 0.95) !important;
    border: 1px solid rgba(49, 51, 63, 0.2) !important;
    border-radius: 4px !important;
    padding: 8px !important;
    font-family: monospace !important;
    transition: border-color 0.2s ease-in-out !important;
    color: rgba(49, 51, 63, 0.9) !important;
}
[data-testid="stExpander"] textarea:focus {
    border-color: rgba(49, 51, 63, 0.4) !important;
    box-shadow: none !important;
    outline: none !important;
}

/* Headers inside expander */
[data-testid="stExpander"] h3, 
[data-testid="stExpander"] h4 {
    color: rgba(49, 51, 63, 0.9) !important;
    margin-bottom: 1rem !important;
}

/* Remove any default background color */
[data-testid="stExpander"],
[data-testid="stExpander"] div,
[data-testid="stExpander"] details,
.st-emotion-cache-1y4p8pa,
.st-emotion-cache-1gulkj3,
.st-emotion-cache-1q1n0ol,
.st-emotion-cache-1ehh7ok {
    background-color: transparent !important;
}
</style>
""", unsafe_allow_html=True)

# Main Title and Subheader
st.markdown("<h1 class='main-title'>🤖</h1>", unsafe_allow_html=True)
st.markdown("<p class='subheader'>Multi-Agent Reasoning Assistant a003</p>", unsafe_allow_html=True)

# -------------
# Retrieve API key from secrets
# -------------
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception as e:
    logging.error(f"GOOGLE_API_KEY not found in Streamlit secrets: {e}")
    st.error(
        "⚠️ GOOGLE_API_KEY not found in Streamlit secrets! Make sure to add it in the Streamlit Cloud dashboard."
    )
    st.stop()

# Configure the API
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    
    # Add agent3 configuration
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

# -------------
# Initialize Session State
# -------------
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

# -------------
# Sidebar Layout for Configuration
# -------------
# Place the slider and the "Dive In" button in the sidebar for a more organized layout.
with st.sidebar:
    loops = st.select_slider(
        "How deep should we dive?",
        options=["Puddle", "Lake", "Ocean", "Mariana Trench"],
        value="Lake",
    )
    
    # Create a button in the sidebar to start the analysis
    start_button_clicked = st.button("🌊 Dive In", key="start_button")
    # Also track session-wide button state
    if start_button_clicked:
        st.session_state.start_button_clicked = True

# -------------
# Main Input Section
# -------------
# Text input for topic or question
topic = st.text_input(
    "Enter a topic or question:",
    placeholder='e.g. "Is the Ivory-billed woodpecker really extinct?"',
    key="topic_input",
    # Trigger the same state when the user presses Enter
    on_change=lambda: st.session_state.update({"start_button_clicked": True}) if st.session_state.topic_input else None,
)

# If topic changes, reset relevant session states
if topic != st.session_state.previous_input:
    st.session_state.analysis_complete = False
    st.session_state.pdf_buffer = None
    st.session_state.final_analysis = None
    st.session_state.research_results = []
    st.session_state.tldr_summary = None
    st.session_state.refined_prompt = None
    st.session_state.framework = None
    st.session_state.previous_input = topic

# -------------
# Advanced Prompt Customization
# -------------
# Place the expander on the main page (right-aligned via CSS) for adjusting agent prompts.
with st.expander("                                                                                                                                                                                                ☠️"):
    st.markdown("### Customize Agent Prompts")

    # Agent 1 Prompt
    st.markdown("#### Agent 1: Prompt Engineer")
    agent1_prompt = st.text_area(
        "Prompt for refining user input and generating investigation framework",
        '''You are an expert prompt engineer. Your task is to take a user's topic or question and refine it into a more specific and context-rich prompt. Then, based on this improved prompt, generate a structured investigation framework.

USER'S TOPIC/QUESTION: {topic}

1.  **Prompt Refinement**
    *   Analyze the user's input and identify areas where you can add more detail, specificity, and context.
    *   Consider what background information or assumptions might be helpful to include.
    *   Reformulate the user's input into a more comprehensive and well-defined prompt.

2.  **Investigation Framework**
    *   Based on your **refined prompt**, define a structured approach for investigating the topic.
    *   Outline:
        -   Core Question/Hypothesis
        -   Key Areas Requiring Investigation
        -   Critical Factors to Examine
        -   Required Data and Information Sources
        -   Potential Challenges or Limitations

    *   Present this as a clear investigation framework that will guide further research and analysis.

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
        height=300,
    )

    # Agent 2 Prompt
    st.markdown("#### Agent 2: Researcher")
    agent2_prompt = st.text_area(
        "Prompt for conducting research and analysis",
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
        height=300,
    )

    # Agent 3 Prompt
    st.markdown("#### Agent 3: Expert Analyst")
    agent3_prompt = st.text_area(
        "Prompt for final analysis and synthesis",
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
        height=300,
    )

# -------------
# Define Helper Functions
# -------------

def handle_response(response):
    """Handle model response and extract text with more specific error handling."""
    try:
        if hasattr(response, "parts") and response.parts:
            # Return the first non-empty text part
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
    """Generate a refined prompt and investigation framework using Agent 1."""
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
                # Clean up the refined prompt section
                refined_prompt = parts[0].replace("Refined Prompt", "").strip()
                
                # Clean up the framework section
                framework = parts[1].strip()
                if framework.startswith("Investigation Framework"):
                    framework = framework[len("Investigation Framework"):].strip()
                
                # Remove extra colons from section headers
                framework = framework.replace("Core Question/Hypothesis:", "Core Question/Hypothesis")
                framework = framework.replace("Key Areas Requiring Investigation:", "Key Areas Requiring Investigation")
                
                # Align bullet points for readability
                framework_lines = framework.split("\n")
                cleaned_framework_lines = []
                for line in framework_lines:
                    if line.lstrip().startswith("-"):
                        cleaned_framework_lines.append("   " + line.lstrip())
                    else:
                        cleaned_framework_lines.append(line)
                framework = "\n".join(cleaned_framework_lines)
                
                logging.info("Refined prompt and investigation framework generated successfully")
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
            # Clean the research text from iteration focus lines
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
            text = text.replace(''', "'")
            text = text.replace(''', "'")
            text = text.replace('…', '...')
            # Remove emojis and other special characters
            return ''.join(char for char in text if ord(char) < 128)

        pdf = FPDF()
        pdf.add_page()
        
        # Set font
        pdf.set_font("Helvetica", size=12)
        
        # Add title
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Analysis Report", ln=True, align="C")
        pdf.ln(10)
        
        # Add refined prompt
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Refined Prompt", ln=True)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, sanitize_text(refined_prompt))
        pdf.ln(10)
        
        # Add framework
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Investigation Framework", ln=True)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, sanitize_text(framework))
        pdf.ln(10)
        
        # Add research analysis
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Research Analysis", ln=True)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, sanitize_text(research_analysis))
        pdf.ln(10)
        
        # Add final analysis
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Final Analysis", ln=True)
        pdf.set_font("Helvetica", size=12)
    
