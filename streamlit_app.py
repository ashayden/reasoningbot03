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

Investigation Framework:

**1.** Main Topic Area
- Core Concept or Finding
  - Key supporting evidence or detail
  - Additional context or implication
- Related Aspect or Development
  - Specific example or case study
  - Impact or significance

**2.** Secondary Topic Area
- Primary Analysis Point
  - Factual evidence or data
  - Interpretation or insight
- Comparative Analysis
  - Contrasting perspective
  - Synthesis of findings

**3.** Broader Implications
- Practical Applications
  - Real-world example
  - Implementation consideration
- Future Directions
  - Potential developments
  - Areas for further study

Structure Requirements:
1. Main sections: Bold numbers with period (**1.**)
2. Primary points: Single dash with clear, concise statement
3. Supporting details: Indented dash with specific evidence
4. Spacing: One blank line between main sections
5. Flow: Logical progression from specific to general
6. Depth: 2-3 primary points per section, each with 2-3 supporting details
7. Language: Clear, precise, and objective
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
Include AMA-style in-line citations for each claim or finding using superscript numbers.
Format citations as: Some claim[^1] another point[^2].

Begin your response with a short title, then detail your findings.
End your response with a References section using this format:

References:
1. Author(s). Title. Publication. Year;Volume(Issue):Pages.
2. [Additional references...]

Keep references scholarly, recent (within 10 years when possible), and from reputable sources.'''
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

You are an expert analyst. Provide a comprehensive final report with AMA-style citations.
Use superscript numbers for in-line citations: Example claim[^1] and another point[^2].

Structure:

1. Executive Summary
- A concise overview with key citations[^n]
- Support major claims with citations

2. Key Insights
- Bullet-pointed list with citations for each major claim
- Focus on actionable and noteworthy findings

3. Analysis
[Scale analysis depth based on research loops]
- Synthesize major concepts with citations
- Support all claims with evidence
- Address contradictions with cited sources

4. Supplementary Synthesis
[Dynamic section based on topic and research depth]
Choose relevant elements, all with proper citations:
- Evidence-based recommendations
- Implications supported by research
- Counter-arguments from literature
- Future trends with supporting evidence

5. Conclusion
- Summarize key findings with final citations
- Place in broader context with support

6. References
List all cited works in AMA format:
1. Author(s). Title. Publication. Year;Volume(Issue):Pages.
2. [Continue format for all references]

Write in a clear, authoritative tone. Every major claim must have a citation.'''
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
            text = text.replace(''', "'").replace(''', "'").replace('…', '...')
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
        
        # Process research analysis to separate content and references
        research_text, research_refs = process_citations(research_analysis)
        pdf.multi_cell(0, 10, sanitize_text(research_text))
        if research_refs:
            pdf.ln(5)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 10, "Research References", ln=True)
            pdf.set_font("Helvetica", size=12)
            pdf.multi_cell(0, 10, sanitize_text(research_refs))
        pdf.ln(10)

        # Final analysis
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Final Analysis", ln=True)
        pdf.set_font("Helvetica", size=12)
        
        # Process final analysis to separate content and references
        final_text, final_refs = process_citations(final_analysis)
        pdf.multi_cell(0, 10, sanitize_text(final_text))
        if final_refs:
            pdf.ln(5)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 10, "Final Analysis References", ln=True)
            pdf.set_font("Helvetica", size=12)
            pdf.multi_cell(0, 10, sanitize_text(final_refs))

        return pdf.output(dest='S').encode('latin-1')

    except Exception as e:
        logging.error(f"Failed to create PDF: {e}")
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 10, f"Error creating PDF: {str(e)}", ln=True)
        return pdf.output(dest='S').encode('latin-1')

def generate_random_fact(topic):
    """Generate a verified, interesting fact related to the topic's context but not answering the query."""
    try:
        # First, extract core topic terms and context
        context_prompt = f'''Extract 2-3 core subject terms from this topic/question, ignoring question words (how, why, what, etc):
Topic: {topic}
Return only the core terms, separated by commas.'''
        
        context_resp = model.generate_content(context_prompt)
        core_terms = handle_response(context_resp)
        
        # Generate fact with specific instructions
        fact_prompt = f'''Generate an interesting fact about {core_terms} following these rules:
1. The fact must be objectively verifiable and accurate
2. Do NOT attempt to answer or address any questions in the original topic
3. Focus on surprising or lesser-known aspects of the subject
4. Keep it to 1-2 sentences maximum
5. Include a relevant emoji if appropriate, but use sparingly
6. The fact must be from a reliable source

Format: Just provide the fact with optional emoji. No source needed.'''
        
        fact_resp = model.generate_content(fact_prompt)
        initial_fact = handle_response(fact_resp)
        
        # Verify the fact
        verify_prompt = f'''Verify this fact about {core_terms}:
"{initial_fact}"

Consider:
1. Is it verifiable from reliable sources?
2. Is it historically accurate?
3. Is it stated objectively?
4. Does it avoid speculation?

If the fact passes verification, return it unchanged.
If it fails verification, generate a new, verified fact following the same rules.'''
        
        verify_resp = model.generate_content(verify_prompt)
        verified_fact = handle_response(verify_resp)
        
        return verified_fact.strip()
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
    """Process raw LLM framework output into a structured format without citations."""
    try:
        lines = [line.strip() for line in raw_framework.split('\n') if line.strip()]
        processed = []
        current_section = 0
        
        for line in lines:
            # Remove any citation markers if present
            line = re.sub(r'\[\^?\d+\]', '', line).strip()
            
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
    """Extract research aspects from the framework text."""
    aspects = []
    
    try:
        # Split into lines and clean up
        lines = [line.strip() for line in framework.split('\n') if line.strip()]
        
        for line in lines:
            # Skip empty lines and metadata
            if not line or line.startswith('META_') or line.startswith('SUB_'):
                continue
            
            # Handle section markers
            if line.startswith('SECTION_'):
                section = line.split(':', 1)[1].strip() if ':' in line else ''
                if section:
                    aspects.append(section)
                continue
            
            # Handle point markers
            if line.startswith('POINT_'):
                point = line.split(':', 1)[1].strip() if ':' in line else ''
                if '|' in point:
                    point = point.split('|', 1)[0].strip()
                if point:
                    aspects.append(point)
                continue
            
            # Fallback for non-structured content
            if ':' in line and not line.lower().startswith(('i.', 'ii.', 'iii.')):
                point = line.split(':', 1)[0].strip()
                point = point.lstrip('•⚫○●-*').strip()
                if len(point) > 3 and not point.lower().startswith(('and', 'or', 'but', 'the')):
                    aspects.append(point)
    
    except Exception as e:
        logging.error(f"Error extracting research aspects: {str(e)}")
        return ["Research Point"]  # Fallback aspect
    
    # Ensure we have at least one aspect
    if not aspects:
        aspects = ["Research Point"]
    
    return aspects

def generate_refined_prompt_and_framework(topic):
    """Generate structured research framework without citations."""
    try:
        initial_prompt = f'''Analyze this topic and create:
1. A refined research prompt
2. A structured investigation framework

Topic: {topic}

Framework Requirements:
1. Use clear section markers (SECTION_1, SECTION_2, etc.)
2. Each point should have a clear identifier (POINT_1.1, POINT_1.2, etc.)
3. Include supporting details with parent references (SUB_1.1.1, SUB_1.1.2, etc.)
4. Focus on key investigation areas and research questions
5. Maintain clear hierarchical structure

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
    
    # Step 1: Initial Analysis
    st.session_state.random_fact = generate_random_fact(topic)
    st.session_state.tldr_summary = generate_quick_summary(topic)

    if st.session_state.random_fact:
        with st.expander("🎲 Random Fact", expanded=True):
            # Extract only the fact content
            fact = st.session_state.random_fact
            
            # Remove verification statements and commentary
            if "Return unchanged:" in fact:
                fact = fact.split("Return unchanged:", 1)[1].strip().strip('"')
            elif "The fact is" in fact:
                fact = fact.split("The fact is", 1)[1].strip().strip('"')
            elif "The statement is" in fact:
                fact = fact.split("The statement is", 1)[1].strip().strip('"')
            
            # Remove any verification language
            lines = fact.split('\n')
            fact = lines[-1] if len(lines) > 1 else fact
            fact = fact.strip().strip('"')
            
            # Remove any remaining verification prefixes
            fact = fact.replace("This is verifiable: ", "").replace("This is accurate: ", "").strip()
            
            st.markdown(fact)

    if st.session_state.tldr_summary:
        with st.expander("💡 TL;DR", expanded=True):
            st.markdown(st.session_state.tldr_summary)

    # Mark Step 1 complete
    st.session_state.current_step = 1
    step_container.markdown(render_stepper(st.session_state.current_step), unsafe_allow_html=True)

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
        def normalize_framework_text(text: str) -> list:
            """Convert any framework text into a normalized structure."""
            lines = text.split('\n')
            normalized = []
            current_section = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Detect main sections
                if any(line.lower().startswith(p) for p in ['**1', '1.', '*1', '1)', '#1']):
                    current_section += 1
                    # Extract title, removing any formatting
                    title = line.replace('*', '').strip()
                    title = ''.join(c for c in title if c.isprintable())
                    # Remove numbering and special characters
                    title = ' '.join(title.split()[1:]) if title.split() else ''
                    normalized.append(('section', current_section, title))
                    continue
                    
                # Detect primary points
                if line.lstrip().startswith(('-', '•', '⚫', '○', '●')) or (line[0].isalpha() and line[1] == ')'):
                    text = line.lstrip('-•⚫○●abcdefghijklmnopqrstuvwxyz) ')
                    normalized.append(('primary', text))
                    continue
                    
                # Detect sub-points
                if line.startswith(('  ', '\t')) or line.lower().startswith(('i.', 'ii.', 'iii.')):
                    text = line.lstrip(' \t-•⚫○●ivxIVX.)')
                    normalized.append(('sub', text))
                    continue
                    
                # Other content becomes additional text
                normalized.append(('text', line))
            
            return normalized

        def format_framework_text(framework: str) -> str:
            """Format framework text using hierarchical numbered lists with improved spacing."""
            try:
                # Normalize the input
                normalized = normalize_framework_text(framework)
                if not normalized:
                    return "Error: Could not parse framework structure."
                
                # Format according to template with numbered hierarchy and spacing
                formatted_lines = []
                current_section = 0
                current_point = 0
                current_subpoint = 0
                last_item_type = None
                
                for item in normalized:
                    if item[0] == 'section':
                        # Reset counters for new section
                        current_section = item[1]
                        current_point = 0
                        current_subpoint = 0
                        
                        # Add extra spacing before new sections
                        if formatted_lines:
                            formatted_lines.extend(['', ''])
                        
                        # Format section header
                        section_title = item[2].strip()
                        formatted_lines.append(f"**{current_section}.** {section_title}")
                        last_item_type = 'section'
                        
                    elif item[0] == 'primary':
                        current_point += 1
                        current_subpoint = 0
                        
                        # Add spacing before primary points
                        if last_item_type == 'primary':
                            formatted_lines.append('')
                        
                        # Format primary point with section.point numbering
                        if ':' in item[1]:
                            point, desc = item[1].split(':', 1)
                            formatted_lines.append(f"{current_section}.{current_point}. {point.strip()}: {desc.strip()}")
                        else:
                            formatted_lines.append(f"{current_section}.{current_point}. {item[1].strip()}")
                        last_item_type = 'primary'
                        
                    elif item[0] == 'sub':
                        current_subpoint += 1
                        
                        # Add slight spacing before first sub-point
                        if last_item_type != 'sub' and current_subpoint == 1:
                            formatted_lines.append('')
                        
                        # Format sub-point with section.point.subpoint numbering
                        if ':' in item[1]:
                            point, desc = item[1].split(':', 1)
                            formatted_lines.append(f"    {current_section}.{current_point}.{current_subpoint}. {point.strip()}: {desc.strip()}")
                        else:
                            formatted_lines.append(f"    {current_section}.{current_point}.{current_subpoint}. {item[1].strip()}")
                        last_item_type = 'sub'
                        
                    elif item[0] == 'text':
                        # Add spacing before additional text
                        if last_item_type != 'text':
                            formatted_lines.append('')
                        # Format additional text with clear indentation
                        formatted_lines.append(f"        {item[1].strip()}")
                        last_item_type = 'text'
                    
                # Add final spacing
                if formatted_lines:
                    formatted_lines.append('')
                
                return '\n'.join(formatted_lines)
                
            except Exception as e:
                logging.error(f"Framework formatting error: {str(e)}")
                return "Error: Failed to format framework. Please try again."

        # Format and display the framework
        formatted_text = format_framework_text(framework)
        st.markdown(formatted_text)

    # Mark Step 2 complete
    st.session_state.current_step = 2
    step_container.markdown(render_stepper(st.session_state.current_step), unsafe_allow_html=True)

    # Step 3: Research Phase
    current_analysis = ""
    research_results = []  # Changed from research_results_list for clarity

    aspects = extract_research_aspects(framework)
    
    # Ensure we have enough aspects for the number of loops
    if len(aspects) < loops_num:
        aspects = aspects * (loops_num // len(aspects) + 1)
    
    # Deduplicate aspects while maintaining order
    seen = set()
    aspects = [x for x in aspects if not (x in seen or seen.add(x))]

    for i in range(loops_num):
        try:
            aspect = aspects[i % len(aspects)]
            research_text = conduct_research(refined_prompt, framework, current_analysis, aspect, i+1)
            
            if not research_text:
                st.error(f"Research failed for aspect: {aspect}")
                continue
                
            current_analysis += "\n\n" + research_text
            
            try:
                # Split into title and content, with better error handling
                lines = research_text.split("\n")
                title = "Research Point"  # Default title
                content = research_text   # Default to full text
                
                # Find the first non-empty line for title
                for line in lines:
                    if line.strip():
                        title = line.strip()
                        # Remove the title line from content
                        content = "\n".join(lines[lines.index(line) + 1:]).strip()
                        break
                
                # If no content after title, use full text
                if not content:
                    content = research_text
                
                # Process citations with error handling
                try:
                    processed_content, references = process_citations(content)
                except Exception as citation_error:
                    logging.error(f"Citation processing error: {citation_error}")
                    processed_content = content
                    references = ""
                
                # Store research results
                research_results.append({
                    'title': title or f"Research Point {i+1}",
                    'content': processed_content or "No content available.",
                    'references': references
                })
                
                # Display research block with error handling
                safe_title = title or f"Research Point {i+1}"
                with st.expander(f"{get_title_emoji(safe_title)}{safe_title}", expanded=False):
                    if processed_content:
                        st.markdown(processed_content)
                        if references:
                            st.markdown("---")
                            st.markdown("**References:**")
                            st.markdown(references)
                    else:
                        st.markdown("No research content available.")
                        
            except Exception as e:
                logging.error(f"Error processing research block {i+1}: {str(e)}")
                # Fallback display for errors
                with st.expander(f"Research Point {i+1}", expanded=False):
                    st.markdown("Error processing research content. Original text:")
                    st.markdown(research_text)

        except Exception as e:
            logging.error(f"Error in research block {i+1}: {str(e)}")
            with st.expander(f"Research Point {i+1}", expanded=False):
                st.markdown("Error displaying research content. Please try again.")
            continue

    st.session_state.research_results = research_results

    # Mark Step 3 complete
    st.session_state.current_step = 3
    step_container.markdown(render_stepper(st.session_state.current_step), unsafe_allow_html=True)

    # Step 4: Final Analysis
    try:
        combined_results = "\n\n".join(
            f"### {result['title']}\n{result['content']}\n\nReferences:\n{result['references']}" 
            for result in research_results 
            if result['content']
        )
        
        final_prompt = agent3_prompt.format(
            refined_prompt=refined_prompt,
            framework=framework,
            research_results=combined_results
        )
        
        resp = model.generate_content(final_prompt, generation_config=agent3_config)
        final_analysis = handle_response(resp)
        
        if not final_analysis:
            st.error("Could not generate final report. Please try again.")
            st.stop()
            
        st.session_state.final_analysis = final_analysis
        final_text, final_refs = process_citations(final_analysis)
        with st.expander("📋 Final Report", expanded=True):
            st.markdown(final_text)
            if final_refs:
                st.markdown("---")
                st.markdown("**References:**")
                st.markdown(final_refs)

        # Create PDF
        pdf_bytes = create_download_pdf(refined_prompt, framework, current_analysis, final_analysis)
        st.session_state.pdf_buffer = pdf_bytes

        # Mark analysis complete
        st.session_state.current_step = 4
        st.session_state.analysis_complete = True
        step_container.markdown(render_stepper(st.session_state.current_step), unsafe_allow_html=True)

        # Show download button
        st.download_button(
            label="⬇️ Download Report as PDF",
            data=pdf_bytes,
            file_name=f"{topic}_analysis_report.pdf",
            mime="application/pdf",
            key="download_button"
        )

    except Exception as e:
        logging.error(f"Final report error: {e}")
        st.error("Error generating final report. Please try again.")
        st.stop()

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

# Add function to process citations and create reference list
def process_citations(text: str) -> tuple[str, str]:
    """Process text with citations and return processed text and reference list."""
    try:
        # Handle empty or invalid input
        if not text or not isinstance(text, str):
            return "", ""
        
        # Split on References section if it exists
        parts = text.split("\nReferences:", 1)
        main_text = parts[0].strip()
        references = parts[1].strip() if len(parts) > 1 else ""
        
        # If no explicit References section, look for numbered references at the end
        if not references:
            lines = main_text.split('\n')
            ref_start = -1
            for i, line in enumerate(lines):
                if line.strip() and line.strip()[0].isdigit() and '.' in line:
                    # Check if this line and subsequent lines look like references
                    if all(l.strip() and l.strip()[0].isdigit() for l in lines[i:i+2]):
                        ref_start = i
                        break
            
            if ref_start != -1:
                main_text = '\n'.join(lines[:ref_start]).strip()
                references = '\n'.join(lines[ref_start:]).strip()
        
        # Format references as a numbered list if not already
        if references:
            ref_lines = [line.strip() for line in references.split('\n') if line.strip()]
            formatted_refs = []
            for i, ref in enumerate(ref_lines, 1):
                if not ref.startswith(f"{i}."):
                    ref = f"{i}. {ref}"
                formatted_refs.append(ref)
            references = "\n".join(formatted_refs)
        
        return main_text, references
        
    except Exception as e:
        logging.error(f"Citation processing error: {str(e)}")
        return text, ""  # Return original text if processing fails
