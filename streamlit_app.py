# latest working version 
	# to do: 
	# - Add reference section with links/downloads (include in PDF)
	# - Improve PDF formatting
	# - Add markdown and txt download options
	# - Add Follow-up prompt buttons


import streamlit as st
import google.generativeai as genai
import logging
import random
import io
from fpdf import FPDF
import re

########################################
# GLOBAL CONFIG & LOGGING
########################################
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# STEP LABELS FOR YOUR WIZARD
STEPS = [
    "Preparing",
    "Developing",
    "Researching",
    "Complete"
]

########################################
# FUNCTION: RENDER STEPPER
########################################
def render_stepper(current_step: int) -> str:
    """Renders a 5-step wizard with proper styling."""
    # Clamp current_step
    current_step = max(0, min(current_step, 4))
    
    # Create the CSS and HTML
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
    
    # Create the HTML with minimal whitespace
    html_parts = [
        '<div class="stepper-container">',
        *[f'<div class="step {status}"><div class="step-number">{i + 1}</div><div class="step-label">{label}</div><div class="step-line"></div></div>'
          for i, label in enumerate(STEPS)
          for status in ["complete" if i < current_step else "active" if i == current_step else ""]],
        '</div>'
    ]
    
    # Return the complete HTML
    return html + ''.join(html_parts)


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
def init_session_state():
    """Initialize all session state variables with default values."""
    defaults = {
        'analysis_complete': False,
        'current_step': 0,
        'pdf_buffer': None,
        'final_analysis': None,
        'research_results': [],
        'tldr_summary': None,
        'refined_prompt': None,
        'framework': None,
        'previous_input': "",
        'start_button_clicked': False,
        'random_fact': None
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# Complete reset function
def reset_all_states():
    """Reset all session states to their initial values."""
    init_session_state()  # Reuse initialization function
    st.experimental_rerun()

# Initialize states at startup
init_session_state()

# Error handling for Streamlit Cloud
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception as e:
    st.error("Please set the GOOGLE_API_KEY in your Streamlit Cloud secrets.")
    st.info("For local development, create a .streamlit/secrets.toml file with your API key.")
    st.stop()

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
except Exception as e:
    st.error("Error initializing Gemini API. Please check your API key and try again.")
    st.info("If the error persists, please contact support.")
    st.stop()

# --- Main Title ---
st.markdown(
    "<h1 class='main-title' data-title='Multi-Agent Reasoning Assistant a003'>M.A.R.A.</h1>",
    unsafe_allow_html=True
)

# ============ USER INPUT TOPIC ============
def handle_enter():
    """Handle enter key press in topic input."""
    if st.session_state.topic_input.strip():
        st.session_state.start_button_clicked = True
        st.experimental_rerun()

topic = st.text_input(
    "Enter a topic or question:",
    placeholder='e.g. "Is the Ivory-billed woodpecker really extinct?"',
    key="topic_input",
    on_change=handle_enter
)

# Add a complete reset function
def reset_all_states():
    """Reset all session states to their initial values."""
    st.session_state.update({
        'analysis_complete': False,
        'current_step': 0,
        'pdf_buffer': None,
        'final_analysis': None,
        'research_results': [],
        'tldr_summary': None,
        'refined_prompt': None,
        'framework': None,
        'random_fact': None,
        'start_button_clicked': False
    })

# Update the topic change handler
if topic != st.session_state.previous_input:
    st.session_state.previous_input = topic
    reset_all_states()
    st.experimental_rerun()

# If analysis is done, show step #5
if st.session_state.analysis_complete:
    st.session_state.current_step = 4

# ---------- EXPANDERS FOR PROMPTS ----------
with st.expander("**☠️ Advanced Prompt Customization ☠️**"):
    agent1_prompt = st.text_area(
        "Agent 1 Prompt (Prompt Engineer)",
        '''You are an expert prompt engineer. Your task is to take the user's topic:
{topic}

Create a refined prompt and structured investigation framework.

Format your response EXACTLY as follows:

Refined Prompt:
[Your refined prompt here]

---

[Create a concise, descriptive title that directly states the analysis focus]

A. Research Objectives:
   1. Primary Research Questions
      - Key inquiries driving the investigation
      - Specific aspects to explore
   2. Secondary Research Questions
      - Supporting questions
      - Related areas of interest
   3. Expected Outcomes
      - Anticipated findings
      - Potential implications

B. Methodological Approach:
   1. Research Methods
      - Primary investigation techniques
      - Analytical frameworks
   2. Data Collection Strategies
      - Types of information needed
      - Sources to be consulted
   3. Analysis Techniques
      - Methods for synthesizing findings
      - Evaluation approaches

C. Investigation Areas:
   1. Core Topics
      - Central themes
      - Primary concepts
   2. Subtopics
      - Related elements
      - Supporting aspects
   3. Cross-cutting Themes
      - Interconnections
      - Common patterns

D. Critical Considerations:
   1. Key Issues
      - Main challenges
      - Important factors
   2. Stakeholder Perspectives
      - Different viewpoints
      - Affected parties
   3. Impact Assessment
      - Potential effects
      - Broader implications

E. Evaluation Criteria:
   1. Success Metrics
      - Indicators of quality
      - Measurement approaches
   2. Quality Standards
      - Benchmarks
      - Assessment criteria
   3. Verification Methods
      - Validation techniques
      - Quality checks

Structure Requirements:
1. Each section should be clearly labeled (A, B, C, etc.)
2. Use hierarchical numbering (1, 2, 3) for subsections
3. Include bullet points for specific details
4. Maintain consistent formatting throughout
5. Focus on methodological and structural aspects
6. Use clear, precise language
7. Ensure logical flow between sections

Note: Focus on creating a comprehensive research structure. The framework should be methodologically sound and topic-appropriate.''',
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

Create a comprehensive research synthesis following this exact structure:

Title: [Descriptive title reflecting the main focus of topic analysis]
Subtitle: [Specific aspect of analysis]

1. Executive Summary
Provide a 2-3 paragraph overview that:
- Synthesizes key findings with citations
- Highlights major discoveries
- Summarizes methodology

2. Key Insights
Present 4-6 major insights that:
- Include specific citations
- Focus on significant findings
- Connect to methodology

3. Analysis
Develop a thorough analysis that:
- Synthesizes all findings
- Integrates perspectives
- Evaluates evidence
- Organizes by themes

4. Conclusion
Provide research implications:
- Summarize key findings
- Discuss impacts
- Suggest future directions
- Make recommendations

5. Further Considerations
Address complexities:
- Present counter-arguments
- Discuss limitations
- Note uncertainties
- Identify challenges

6. Recommended Readings
List essential sources:
- Note seminal works
- Include recent research
- Add methodology guides
- List digital resources

7. Works Cited
Provide full bibliography:
- Use APA 7th edition format
- Include all in-text citations
- Add DOIs where available
- List primary sources first
- Organize alphabetically
- Each entry should be on a new line
- Each entry should end with a period
- Each entry should start with a bullet point (*)

Important Guidelines:
- Use proper APA in-text citations (Author, Year)
- Ensure every citation has a reference
- Include both classic and recent works
- Maintain academic tone
- Cross-reference analyses
- Format citations consistently
- Include DOIs for recent works

Format Guidelines:
- Use numbered sections (1., 2., etc.)
- Use bullet points for lists (-)
- Include proper spacing between sections
- Format references with bullet points
- End each reference with a period''',
        height=250
    )

# Depth slider
loops = st.select_slider(
    "How deep should we dive?",
    options=["Puddle", "Lake", "Ocean", "Mariana Trench"],
    value="Lake",
)

# Button
start_button = st.button("🌊 Dive In")

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

def create_download_pdf():
    """Create a PDF report of the analysis results."""
    try:
        # Initialize PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Set font
        pdf.set_font("Arial", "B", 16)
        
        # Add title
        pdf.cell(0, 10, "Research Analysis Report", ln=True, align="C")
        pdf.ln(10)
        
        # TL;DR Summary
        if st.session_state.tldr_summary:
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Executive Summary", ln=True)
            pdf.set_font("Arial", "", 12)
            pdf.multi_cell(0, 10, st.session_state.tldr_summary)
            pdf.ln(10)
        
        # Research Results
        if st.session_state.research_results:
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Research Findings", ln=True)
            pdf.ln(5)
            
            for title, content in st.session_state.research_results:
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, title, ln=True)
                pdf.set_font("Arial", "", 12)
                pdf.multi_cell(0, 10, content)
                pdf.ln(5)
        
        # Final Analysis
        if st.session_state.final_analysis:
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Final Analysis", ln=True)
            pdf.set_font("Arial", "", 12)
            pdf.multi_cell(0, 10, st.session_state.final_analysis)
        
        # Save to buffer
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)
        
        return pdf_buffer
        
    except Exception as e:
        logging.error(f"PDF generation failed: {str(e)}")
        st.error("Unable to generate PDF. Please try again.")
        return None

def generate_random_fact(topic):
    """Generate a fascinating and unexpected fact about the topic."""
    try:
        fact_prompt = (
            "Generate a fascinating and unexpected fact about this topic: "
            f"'{topic}'\n\n"
            "The fact should:\n"
            "- Be surprising, unique, or counter-intuitive\n"
            "- Reveal an interesting connection or lesser-known aspect\n"
            "- Use vivid, engaging language\n"
            "- Include relevant statistics or specific details when possible\n"
            "- Add 1-2 relevant emojis that enhance understanding\n"
            "- Be exactly one sentence that hooks the reader\n"
            "- Challenge common assumptions or expectations\n\n"
            "Make it memorable and thought-provoking. Respond with just the fact, no additional text."
        )
        
        fact_resp = model.generate_content(fact_prompt)
        fact = handle_response(fact_resp)
        
        if fact:
            # Clean up any verification language or extra formatting
            fact = fact.strip().strip('"')
            fact = re.sub(r'^(Fact:|Here\'s a fact:|The fact is:?)', '', fact, flags=re.IGNORECASE).strip()
            return fact
            
        return None
        
    except Exception as e:
        logging.error(f"Random fact generation error: {str(e)}")
        return None

def count_emojis(text):
    """Count the number of emojis in text using regex pattern."""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"  # dingbats
        u"\U000024C2-\U0001F251" 
        "]+", flags=re.UNICODE)
    return len(emoji_pattern.findall(text))

def generate_quick_summary(topic):
    """Generate a quick summary (TL;DR) with naturally integrated emojis."""
    try:
        summary_prompt = f'''Create a concise 1-2 sentence summary about {topic}.
Include 1-4 relevant emojis naturally integrated into the text (not just at the beginning).
The emojis should enhance readability and meaning, not distract from it.

Guidelines:
- Place emojis where they naturally relate to the concepts they represent
- Don't cluster emojis together
- Use emojis to highlight key points or transitions
- Keep the total number of emojis between 1-4
- Ensure the text makes sense even if emojis were removed

Example format:
"The rise of social media 📱 has transformed how we communicate, creating new opportunities for connection 🤝 while also raising concerns about privacy 🔐."

Return only the summary with integrated emojis.'''

        resp = model.generate_content(summary_prompt)
        summary = handle_response(resp)
        
        # Validate emoji count
        emoji_count = count_emojis(summary)
        if emoji_count > 4:
            # If too many emojis, try to get a new summary
            retry_prompt = f'''Revise this summary to use fewer emojis (maximum 4):
{summary}

Keep the most relevant emojis and remove others while maintaining the meaning.'''
            
            retry_resp = model.generate_content(retry_prompt)
            summary = handle_response(retry_resp)
        
        return summary.strip()
        
    except Exception as e:
        logging.error(e)
        return None

def process_framework_output(raw_framework: str) -> str:
    """Process raw LLM framework output into a structured, machine-readable format."""
    try:
        lines = [line.strip() for line in raw_framework.split('\n') if line.strip()]
        processed = []
        current_section = 0
        
        for line in lines:
            # Main section headers
            if any(line.lower().startswith(p) for p in ['**1', '1.', '*1', '1)', '#1', 'section 1']):
                current_section += 1
                title = re.sub(r'^[*\d.)\s]+', '', line).split(':', 1)[0].strip().upper()
                processed.append(f"SECTION_{current_section}:{title}")
                continue
            
            # Primary research points
            if line.lstrip().startswith(('-', '•', '⚫', '○', '●')) or (len(line) > 2 and line[0].isalpha() and line[1] == ')'):
                text = line.lstrip('-•⚫○●abcdefghijklmnopqrstuvwxyz) ')
                if ':' in text:
                    point, desc = text.split(':', 1)
                    processed.append(f"POINT_{current_section}.{len([l for l in processed if l.startswith(f'POINT_{current_section}')])+ 1}:{point.strip()}|{desc.strip()}")
                else:
                    processed.append(f"POINT_{current_section}.{len([l for l in processed if l.startswith(f'POINT_{current_section}')])+ 1}:{text.strip()}")
                continue
            
            # Supporting details and sub-points
            if line.startswith(('  ', '\t')) or line.lower().startswith(('i.', 'ii.', 'iii.')):
                text = line.lstrip(' \t-•⚫○●ivxIVX.)')
                parent_points = [l for l in processed if l.startswith(f'POINT_{current_section}')]
                if parent_points:
                    parent_num = parent_points[-1].split(':')[0].split('_')[1]
                    sub_count = len([l for l in processed if l.startswith(f'SUB_{current_section}.{parent_num}')])
                    if ':' in text:
                        point, desc = text.split(':', 1)
                        processed.append(f"SUB_{current_section}.{parent_num}.{sub_count + 1}:{point.strip()}|{desc.strip()}")
                    else:
                        processed.append(f"SUB_{current_section}.{parent_num}.{sub_count + 1}:{text.strip()}")
                continue
            
            # Additional context or metadata
            if line:
                processed.append(f"META_{current_section}:{line.strip()}")
        
        return '\n'.join(processed)
        
    except Exception as e:
        logging.error(f"Framework processing error: {str(e)}")
        return raw_framework

def extract_research_aspects(framework: str) -> list:
    """Extract research aspects from machine-readable framework format."""
    aspects = []
    
    for line in framework.split('\n'):
        if not line.strip():
            continue
            
        # Extract points from structured format
        if line.startswith('POINT_'):
            try:
                content = line.split(':', 1)[1]
                if '|' in content:
                    point, desc = content.split('|', 1)
                    aspects.append((point.strip(), desc.strip()))
                else:
                    aspects.append((content.strip(), ''))
            except:
                continue
                
        # Include relevant metadata
        elif line.startswith('META_'):
            try:
                content = line.split(':', 1)[1].strip()
                if len(content) > 10:  # Only include substantial metadata
                    aspects.append((content, ''))
            except:
                continue
    
    return [aspect[0] for aspect in aspects if aspect[0]]  # Return only point titles

def generate_refined_prompt_and_framework(topic):
    """Generate structured research framework optimized for agent processing."""
    try:
        initial_prompt = f'''Analyze this topic and create:
1. A refined research prompt
2. A structured investigation framework

Topic: {topic}

Framework Requirements:
1. Use clear section markers (SECTION_1, SECTION_2, etc.)
2. Each point should have a clear identifier (POINT_1.1, POINT_1.2, etc.)
3. Include supporting details with parent references (SUB_1.1.1, SUB_1.1.2, etc.)
4. Add relevant metadata with META_ prefix
5. Use pipe symbol (|) to separate point titles from descriptions

Format:
Refined Prompt:
[prompt]
---
[structured framework]'''

        initial_resp = model.generate_content(initial_prompt)
        initial_result = handle_response(initial_resp)
        
        if not initial_result or "---" not in initial_result:
            return None, None
            
        parts = initial_result.split("---")
        refined_prompt = parts[0].replace("Refined Prompt:", "").strip()
        initial_framework = parts[1].strip()
        
        # Process framework into structured format
        processed_framework = process_framework_output(initial_framework)
            
        return refined_prompt, processed_framework
        
    except Exception as e:
        logging.error(f"Framework generation error: {str(e)}")
        return None, None

def conduct_research(refined_prompt, framework, prev_analysis, aspect, iteration):
    """Call Agent 2 to conduct deeper research."""
    try:
        # Base prompt for initial research
        base_prompt = f'''Using the following inputs:

REFINED PROMPT:
{refined_prompt}

FRAMEWORK:
{framework}

CURRENT FOCUS:
{aspect}

Follow the methodological approaches and evaluation criteria specified in the framework.
Provide detailed findings for each key area of investigation outlined.

Structure your analysis using this format:

Title: [Descriptive title reflecting the main focus of {aspect}]
Subtitle: [Specific aspect of analysis and/or approach being analyzed]

1. Introduction
   - Context and background
   - Scope of analysis
   - Key objectives

2. Methodology Overview
   - Approach used
   - Data sources
   - Analytical methods

3. Key Findings
   - Primary discoveries (with citations)
   - Supporting evidence (with citations)
   - Critical insights

4. Analysis
   - Detailed examination of findings (with citations)
   - Interpretation of results
   - Connections and patterns

5. Implications
   - Theoretical implications
   - Practical applications
   - Future considerations

6. Limitations and Gaps
   - Current limitations
   - Areas needing further research
   - Potential biases

7. Works Cited
   - Use APA 7th edition format
   - Include all in-text citations
   - Add DOIs where available
   - List primary sources first
   - Organize alphabetically
   - Each entry should be on a new line
   - Each entry should end with a period
   - Each entry should start with a bullet point (*)

Important:
- Use proper APA in-text citations (Author, Year)
- Each section should have at least 2-3 relevant citations
- Ensure citations are from reputable academic sources
- Include a mix of seminal works and recent research (last 5 years)
- All citations must have corresponding entries in Works Cited

Note: As this is iteration {iteration}, be more explorative and creative while maintaining academic rigor.'''

        # Additional prompt for subsequent iterations
        iteration_prompt = f'''
PREVIOUS ANALYSIS:
{prev_analysis}

For iteration #{iteration}, focus on:
1. Identifying gaps or areas needing more depth
2. Exploring new connections and implications
3. Refining and strengthening key arguments
4. Adding new supporting evidence or perspectives

Structure your analysis using this format:

Title: [Descriptive title reflecting the new focus]
Subtitle: [Specific aspect being expanded upon]

1. Previous Analysis Review
   - Key points from previous iteration
   - Areas identified for expansion
   - New perspectives to explore

2. Expanded Analysis
   - Deeper investigation of key themes (with citations)
   - New evidence and insights (with citations)
   - Advanced interpretations

3. Novel Connections
   - Cross-cutting themes (with citations)
   - Interdisciplinary insights
   - Emerging patterns

4. Critical Evaluation
   - Strengthened arguments (with citations)
   - Counter-arguments addressed
   - Enhanced evidence base

5. Synthesis and Integration
   - Integration with previous findings
   - Enhanced understanding
   - Refined conclusions

6. Works Cited
   - Use APA 7th edition format
   - Include all in-text citations
   - Add DOIs where available
   - List primary sources first
   - Organize alphabetically
   - Each entry should be on a new line
   - Each entry should end with a period
   - Each entry should start with a bullet point (*)

Important:
- Use proper APA in-text citations (Author, Year)
- Each section should have at least 2-3 relevant citations
- Ensure citations are from reputable academic sources
- Include a mix of seminal works and recent research (last 5 years)
- All citations must have corresponding entries in Works Cited

Note: As this is iteration {iteration}, be more explorative and creative while maintaining academic rigor.'''

        # Choose prompt based on iteration
        prompt = base_prompt if iteration == 1 else iteration_prompt
        
        resp = model.generate_content(prompt)
        return handle_response(resp)
    except Exception as e:
        logging.error(e)
    return None

def get_title_emoji(title: str) -> str:
    """Select an emoji based on keywords in the research block title."""
    keywords = {
        # Analysis & Research
        'analysis': '📊', 'research': '🔍', 'study': '📝', 'investigation': '🔎',
        'findings': '📋', 'results': '📈', 'data': '📊', 'evidence': '🔍',
        
        # Topics & Concepts
        'history': '📜', 'development': '📈', 'impact': '💥', 'evolution': '🔄',
        'technology': '💻', 'science': '🔬', 'nature': '🌿', 'social': '👥',
        'economic': '💰', 'culture': '🎭', 'environment': '🌍', 'health': '🏥',
        'education': '📚', 'politics': '🏛️', 'industry': '🏭', 'art': '🎨',
        
        # Methods & Approaches
        'comparison': '⚖️', 'evaluation': '📋', 'assessment': '📝', 'review': '🔎',
        'survey': '📊', 'experiment': '🧪', 'observation': '👁️', 'test': '✅',
        
        # Outcomes & Insights
        'conclusion': '🎯', 'recommendation': '💡', 'solution': '🔑', 'problem': '⚠️',
        'challenge': '🎯', 'success': '🏆', 'failure': '❌', 'improvement': '📈'
    }
    
    title_lower = title.lower()
    for keyword, emoji in keywords.items():
        if keyword in title_lower:
            return f"{emoji} "
    return "🔍 "  # Default emoji

# Convert slider selection to numeric loops
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

########################################
# MAIN LOGIC WHEN USER CLICKS BUTTON
########################################
if start_button or st.session_state.get('start_button_clicked', False):
    # Reset the enter key trigger for next time
    st.session_state.start_button_clicked = False
    
    if not topic.strip():
        st.warning("Please enter a topic.")
        st.stop()
    
    # Complete reset before starting new analysis
    reset_all_states()
    
    # Create progress indicator
    step_container = st.empty()
    step_container.markdown(render_stepper(st.session_state.current_step), unsafe_allow_html=True)
    
    # Show immediate feedback that analysis is starting
    st.markdown("### 🔍 Beginning Analysis...")
    
    # Generate and display random fact immediately
    with st.spinner("Discovering an interesting fact..."):
        random_fact = generate_random_fact(topic)
        if random_fact:
            with st.expander("🎲 Did You Know?", expanded=True):
                st.markdown(random_fact)
        st.session_state.random_fact = random_fact
    
    # Generate quick summary
    with st.spinner("Generating quick summary..."):
        tldr_summary = generate_quick_summary(topic)
        if tldr_summary:
            with st.expander("💡 TL;DR", expanded=True):
                st.markdown(tldr_summary)
        st.session_state.tldr_summary = tldr_summary

    # Step 2: Framework Development
    with st.spinner("Optimizing research approach..."):
        refined_prompt, framework = generate_refined_prompt_and_framework(topic)
        if not refined_prompt or not framework:
            st.error("Could not generate refined prompt and framework. Please try again.")
            st.stop()

        st.session_state.refined_prompt = refined_prompt
        st.session_state.framework = framework

        with st.expander("🎯 Refined Prompt", expanded=False):
            st.markdown(refined_prompt)

        with st.expander("🗺️ Investigation Framework", expanded=False):
            formatted_text = format_framework_text(framework)
            st.markdown(formatted_text)

    # Mark Step 1 complete and continue with rest of analysis
    st.session_state.current_step = 1
    step_container.markdown(render_stepper(st.session_state.current_step), unsafe_allow_html=True)

    # Continue with remaining steps...

# Add emoji range check helper at the top of the file with other imports
def is_emoji(c):
    return c in [
        '\U0001F300-\U0001F9FF',  # Emoticons
        '\U0001F600-\U0001F64F',  # Emoticons
        '\U0001F680-\U0001F6FF',  # Transport & Map
        '\U0001F700-\U0001F77F',  # Alchemical
        '\U0001F780-\U0001F7FF',  # Geometric
        '\U0001F800-\U0001F8FF',  # Supplemental Arrows-C
        '\U0001F900-\U0001F9FF',  # Supplemental Symbols and Pictographs
        '\U0001FA00-\U0001FA6F',  # Chess Symbols
        '\U0001FA70-\U0001FAFF',  # Symbols and Pictographs Extended-A
        '\U00002702-\U000027B0',  # Dingbats
        '\U000024C2-\U0001F251'   # Enclosed characters
    ]
