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

1) Create a more refined prompt
2) Provide an initial structured investigation framework
3) Review and enhance the framework by adding depth and complexity to each point

Format your response exactly as:

Refined Prompt:
[Your refined prompt here]

---

Investigation Framework:

**1.** Main Section Title
- Primary Point: Description or explanation
  - Supporting detail or specific aspect
  - Additional detail or consideration

**2.** Main Section Title
- Primary Point: Description or explanation
  - Supporting detail or specific aspect
  - Additional detail or consideration

Formatting Guidelines:
1. Main Sections: Bold number with period (**1.**), followed by clear title
2. Primary Points: Single dash (-) with colon after point
3. Supporting Details: Indented with two spaces, single dash (-)
4. Spacing: One blank line between main sections only
5. Structure: 2-3 primary points per section, each with 2-3 supporting details''',
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

You are an expert analyst. Provide a comprehensive final report with the following structure:

1. Executive Summary
- A concise overview of the investigation and key findings (2-3 paragraphs)

2. Key Insights
- Bullet-pointed list of the most important discoveries and conclusions
- Focus on actionable and noteworthy findings
- Include surprising or counter-intuitive insights

3. Analysis
[Scale analysis depth based on research loops]
- Synthesize major concepts and themes from the research
- Examine relationships between different aspects
- Support claims with evidence from the research
- Address any contradictions or nuances found

4. Supplementary Synthesis
[Dynamic section based on topic and research depth]
Choose relevant elements from:
- Recommendations for action or further investigation
- Implications of the findings
- Counter-arguments or alternative perspectives
- Significance and broader impact
- Limitations of current understanding
- Future trends or developments

5. Conclusion
- Summarize the most important takeaways
- Place findings in broader context
- Highlight remaining questions or areas for future research

6. Further Learning
- List key sources referenced in the analysis
- Recommend additional reading materials
- Suggest related topics for deeper investigation

Write in a clear, authoritative tone. Support all major claims with evidence from the research.''',
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

def generate_quick_summary(topic):
    """Generate a quick summary (TL;DR)."""
    try:
        prompt = f"Give a concise 1-2 sentence summary about {topic}."
        resp = model.generate_content(prompt)
        return handle_response(resp)
    except Exception as e:
        logging.error(e)
    return None

def generate_refined_prompt_and_framework(topic):
    """Call Agent 1 to create and refine prompt + framework."""
    try:
        # Initial framework generation
        initial_prompt = f'''As an expert prompt engineer, analyze this topic and create:
1. A refined, detailed prompt
2. An initial structured framework for investigation

Topic: {topic}

Format your response exactly as:
Refined Prompt:
[Your refined prompt here]
---
[Your investigation framework with numbered points]'''

        initial_resp = model.generate_content(initial_prompt)
        initial_result = handle_response(initial_resp)
        
        if not initial_result or "---" not in initial_result:
            return None, None
            
        parts = initial_result.split("---")
        refined_prompt = parts[0].replace("Refined Prompt:", "").strip()
        initial_framework = parts[1].strip()
        
        # Framework refinement
        refinement_prompt = f'''As an expert analyst, review and enhance this investigation framework by adding depth and complexity to each point.

Original Framework:
{initial_framework}

Guidelines:
1. Add 2-3 specific sub-aspects under each main point
2. Include both obvious and non-obvious angles
3. Consider interconnections between points
4. Ensure comprehensive coverage while maintaining focus
5. Add specific areas of investigation under each point

Provide the enhanced framework maintaining the same overall structure but with added depth and detail.'''

        refinement_resp = model.generate_content(refinement_prompt)
        enhanced_framework = handle_response(refinement_resp)
        
        if not enhanced_framework:
            return refined_prompt, initial_framework
            
        return refined_prompt, enhanced_framework
        
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
    # Convert title to lowercase for matching
    title_lower = title.lower()
    
    # Common keywords and their corresponding emojis
    keyword_emojis = {
        # Cultural & Social
        'culture': '🎭', 'tradition': '📿', 'society': '👥', 'community': '🤝',
        'social': '👥', 'people': '👥', 'population': '👥',
        
        # Arts & Entertainment
        'music': '🎵', 'art': '🎨', 'dance': '💃', 'festival': '🎉',
        'entertainment': '🎪', 'celebration': '🎊', 'performance': '🎭',
        
        # Food & Cuisine
        'food': '🍲', 'cuisine': '🍳', 'culinary': '🍽️', 'dish': '🍽️',
        'cooking': '👨‍🍳', 'restaurant': '🍽️', 'dining': '🍽️',
        
        # Places & Locations
        'city': '🌆', 'urban': '🏙️', 'street': '🛣️', 'district': '🏘️',
        'neighborhood': '🏘️', 'area': '📍', 'location': '📍', 'region': '🗺️',
        
        # Nature & Environment
        'nature': '🌳', 'environment': '🌿', 'climate': '🌡️', 'weather': '☁️',
        'river': '🌊', 'ocean': '🌊', 'forest': '🌳', 'wildlife': '🦋',
        
        # Time Periods
        'history': '📜', 'historical': '📜', 'ancient': '🏺', 'modern': '🌆',
        'contemporary': '🎯', 'future': '🔮', 'past': '⌛', 'era': '⏳',
        
        # Architecture & Buildings
        'architecture': '🏛️', 'building': '🏗️', 'structure': '🏛️',
        'construction': '🏗️', 'design': '✏️', 'monument': '🗿',
        
        # Economy & Business
        'economy': '💹', 'business': '💼', 'trade': '🤝', 'market': '🏪',
        'industry': '🏭', 'commerce': '💰', 'financial': '💱',
        
        # Religion & Spirituality
        'religion': '⛪', 'spiritual': '✨', 'sacred': '🙏', 'ritual': '📿',
        'belief': '🙏', 'faith': '✨', 'worship': '⛪',
        
        # Transportation
        'transport': '🚊', 'traffic': '🚦', 'vehicle': '🚗', 'travel': '✈️',
        'transportation': '🚊', 'mobility': '🚶',
        
        # Education & Learning
        'education': '📚', 'school': '🏫', 'learning': '📖', 'teaching': '👨‍🏫',
        'academic': '🎓', 'study': '📝', 'research': '🔬',
        
        # Technology & Innovation
        'technology': '💻', 'innovation': '💡', 'digital': '🖥️', 'tech': '⚡',
        'scientific': '🔬', 'science': '🔬', 'development': '⚡',
        
        # Health & Medicine
        'health': '🏥', 'medical': '⚕️', 'healthcare': '🏥', 'wellness': '💪',
        'disease': '🦠', 'treatment': '💊',
        
        # Politics & Government
        'political': '🏛️', 'government': '🏛️', 'policy': '📜', 'law': '⚖️',
        'legislation': '📜', 'regulation': '📋'
    }
    
    # Check for keyword matches in the title
    for keyword, emoji in keyword_emojis.items():
        if keyword in title_lower:
            return emoji
    
    # Default emoji if no keywords match
    return '📌'

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
        # Clean up and format the framework text
        framework_lines = framework.split('\n')
        formatted_framework = []
        
        for line in framework_lines:
            line = line.strip()
            if not line:
                continue
                
            # Main numbered sections
            if line[0].isdigit() and '.' in line[:3]:
                if formatted_framework:  # Add spacing between sections
                    formatted_framework.append("")
                # Format: "**1.** Title"
                parts = line.split('.', 1)
                number = parts[0].strip()
                rest = parts[1].strip() if len(parts) > 1 else ""
                formatted_framework.append(f"**{number}.** {rest}")
                
            # Key points (first level)
            elif line.startswith(('-', '•', '⚫', '○', '●')) or (line[0].isalpha() and line[1] == '.'):
                # Remove any existing markers and clean the text
                clean_line = line.lstrip('-•⚫○●abcdefghijklmnopqrstuvwxyz.').strip()
                formatted_framework.append(f"- {clean_line}")
                
            # Sub-points (second level)
            elif line.startswith(('  ', '\t')) or line.lower().startswith(('i.', 'ii.', 'iii.')):
                # Remove any existing markers and clean the text
                clean_line = line.lstrip(' \t-•⚫○●ivxIVX.').strip()
                formatted_framework.append(f"  - {clean_line}")
            
            # Additional text
            else:
                formatted_framework.append(f"    {line}")
        
        st.markdown('\n'.join(formatted_framework))

    # Mark Step 2 complete
    st.session_state.current_step = 2
    step_container.markdown(render_stepper(st.session_state.current_step), unsafe_allow_html=True)

    # Step 3: Research Phase
    def extract_research_aspects(framework: str) -> list:
        """Extract research aspects from the framework."""
        aspects = []
        
        for line in framework.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Extract main numbered sections
            if line[0].isdigit() and '.' in line[:3]:
                point = line[line.find('.')+1:].strip()
                if point and ':' in point:
                    point = point.split(':', 1)[0].strip()
                if point:
                    aspects.append(point)
                    continue
                
            # Extract bullet points and labeled sections
            if ':' in line:
                # Skip sub-points (usually implementation details)
                if line.lower().startswith(('i.', 'ii.', 'iii.')):
                    continue
                # Get the main point before the colon
                point = line.split(':', 1)[0].strip()
                # Remove bullet points and other markers
                point = point.lstrip('•⚫○●-').strip()
                # Skip if it's too short or looks like a sub-point
                if len(point) > 3 and not point.lower().startswith(('and', 'or', 'but', 'the')):
                    aspects.append(point)
        
        return aspects

    aspects = extract_research_aspects(framework)
    
    if not aspects:
        st.error("Framework parsing failed. Please try again.")
        logging.error(f"Failed to parse framework: {framework}")
        st.stop()

    # Ensure we have enough aspects for the number of loops
    if len(aspects) < loops_num:
        aspects = aspects * (loops_num // len(aspects) + 1)
    
    current_analysis = ""
    research_results_list = []

    for i in range(loops_num):
        aspect = aspects[i % len(aspects)]
        research_text = conduct_research(refined_prompt, framework, current_analysis, aspect, i+1)
        
        if not research_text:
            st.error(f"Research failed for aspect: {aspect}")
            st.stop()
            
        current_analysis += "\n\n" + research_text
        lines = research_text.split("\n")
        
        try:
            # Ensure valid title and content
            title = lines[0].strip() if lines and lines[0].strip() else f"Research Point {i+1}"
            content = "\n".join(lines[1:]) if len(lines) > 1 else research_text
            
            # Clean and validate title
            title = ''.join(c for c in title if c.isprintable() and ord(c) < 128)  # Remove non-ASCII chars
            title = title.replace('"', '').replace("'", "")  # Remove quotes
            title = ' '.join(title.split())  # Normalize whitespace
            
            if not title or len(title) < 1:
                title = f"Research Point {i+1}"
            elif len(title) > 100:
                title = title[:97] + "..."
            
            # Clean and validate content
            content = content.strip()
            if not content:
                content = "No content available."
            
            research_results_list.append((title, content))
            
            # Try to get emoji, with fallback
            try:
                emoji = get_title_emoji(title)
                if not emoji or len(emoji) > 2 or not emoji.isprintable():
                    emoji = "📌"
                display_title = f"{emoji} {title}"
            except:
                display_title = f"📌 {title}"
            
            # Ensure display title is valid for Streamlit
            display_title = display_title.encode('ascii', 'ignore').decode('ascii')
            if not display_title or len(display_title) < 1:
                display_title = f"Research Point {i+1}"
            
            # Display the expander
            with st.expander(display_title, expanded=False):
                st.markdown(content)
                
        except Exception as e:
            logging.error(f"Error in research block {i+1}: {str(e)}")
            # Fallback display with guaranteed safe values
            fallback_title = f"Research Point {i+1}"
            with st.expander(fallback_title, expanded=False):
                st.markdown("Error displaying research content. Please try again.")

    st.session_state.research_results = research_results_list

    # Mark Step 3 complete
    st.session_state.current_step = 3
    step_container.markdown(render_stepper(st.session_state.current_step), unsafe_allow_html=True)

    # Step 4: Final Analysis
    try:
        combined_results = "\n\n".join(f"### {t}\n{c}" for t, c in research_results_list)
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
        with st.expander("📋 Final Report", expanded=True):
            st.markdown(final_analysis)

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
