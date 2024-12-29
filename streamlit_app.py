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
st.markdown("""
<style>
/* Set font family for entire app */
body, .stTextInput, .st-bb, .st-da, .st-ea, .st-eb, .st-ec, .st-ed, .st-ee, .st-ef, .st-eg, .st-eh, .st-ei, .st-ej, .st-ek, .st-el, .st-em, .st-en, .st-eo, .st-ep, .st-eq, .st-er, .st-es, .st-et, .st-eu, .st-ev, .st-ew, .st-ex, .st-ey, .st-ez, .st-fa, .st-fb, .st-fc, .st-fd, .st-fe, .st-ff, .st-fg, .st-fh, .st-fi, .st-fj, .st-fk, .st-fl, .st-fm, .st-fn, .st-fo, .st-fp, .st-fq, .st-fr, .st-fs, .st-ft, .st-fu, .st-fv, .st-fw, .st-fx, .st-fy, .st-fz, .st-g0, .st-g1, .st-g2, .st-g3, .st-g4, .st-g5, .st-g6, .st-g7, .st-g8, .st-g9, .st-ga, .st-gb, .st-gc, .st-gd, .st-ge, .st-gf, .st-gg, .st-gh, .st-gi, .st-gj, .st-gk, .st-gl, .st-gm, .st-gn, .st-go, .st-gp, .st-gq, .st-gr, .st-gs, .st-gt, .st-gu, .st-gv, .st-gw, .st-gx, .st-gy, .st-gz, .st-h0, .st-h1, .st-h2, .st-h3, .st-h4, .st-h5, .st-h6, .st-h7, .st-h8, .st-h9, .st-ha, .st-hb, .st-hc, .st-hd, .st-he, .st-hf, .st-hg, .st-hh, .st-hi, .st-hj, .st-hk, .st-hl, .st-hm, .st-hn, .st-ho, .st-hp, .st-hq, .st-hr, .st-hs, .st-ht, .st-hu, .st-hv, .st-hw, .st-hx, .st-hy, .st-hz, .st-i0, .st-i1, .st-i2, .st-i3, .st-i4, .st-i5, .st-i6, .st-i7, .st-i8, .st-i9, .st-ia, .st-ib, .st-ic, .st-id, .st-ie, .st-if, .st-ig, .st-ih, .st-ii, .st-ij, .st-ik, .st-il, .st-im, .st-in, .st-io, .st-ip, .st-iq, .st-ir, .st-is, .st-it, .st-iu, .st-iv, .st-iw, .st-ix, .st-iy, .st-iz, .st-j0, .st-j1, .st-j2, .st-j3, .st-j4, .st-j5, .st-j6, .st-j7, .st-j8, .st-j9, .st-ja, .st-jb, .st-jc, .st-jd, .st-je, .st-jf, .st-jg, .st-jh, .st-ji, .st-jj, .st-jk, .st-jl, .st-jm, .st-jn, .st-jo, .st-jp, .st-jq, .st-jr, .st-js, .st-jt, .st-ju, .st-jv, .st-jw, .st-jx, .st-jy, .st-jz {
    font-family: 'Roboto', sans-serif;
}

/* Style for progress bar */
.stProgress {
    width: 100% !important;
    margin: 30px 0;
    background-color: rgba(0, 123, 255, 0.1);
    border-radius: 20px;
    padding: 0;
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #007bff 0%, #007bff var(--progress), #28a745 var(--progress), #28a745 100%);
    border-radius: 20px;
    height: 12px;
    transition: all 0.3s ease;
}

/* Style for the slider */
.stSlider {
    width: 100% !important;
    padding: 20px 0;
}

.stSlider > div {
    margin-bottom: 20px;
}

/* Make the slider track taller */
.stSlider > div > div > div {
    height: 24px !important;
}

/* Style the slider thumb */
.stSlider > div > div > div > div {
    height: 24px !important;
    width: 24px !important;
    background-color: #007bff !important;
    border: 2px solid white !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
    transition: all 0.2s ease !important;
}

.stSlider > div > div > div > div:hover {
    transform: scale(1.1);
    box-shadow: 0 3px 6px rgba(0,0,0,0.3) !important;
}

/* Style slider value text */
.stSlider > div > div:nth-child(3) > span {
    font-family: 'Roboto', sans-serif !important;
    font-size: 1.1rem !important;
    font-weight: 500 !important;
    color: #007bff !important;
    margin-top: 8px !important;
}

/* Add padding to main content */
.main .block-container {
    padding: 3rem 3rem 1rem !important;
}

/* Style for buttons */
.stButton > button {
    float: right;
    margin-bottom: 20px;
}

/* Style for expander headers */
.streamlit-expanderHeader {
    font-weight: bold;
    font-size: 1.2rem;
    padding: 10px 0;
    border-radius: 5px;
    transition: all 0.2s ease;
}

.streamlit-expanderHeader:hover {
    background-color: rgba(0, 123, 255, 0.1);
}

/* Style for the main title (remove color to use default)*/
.main-title {
    font-size: 2.5rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}

/* Style for the subheader */
.subheader {
    font-size: 1.2rem;
    color: #6c757d;
    margin-bottom: 1.5rem;
}

/* Style for the slider - remove background and change font*/
.stSlider > div > div {
    font-family: 'Roboto', sans-serif !important;
}

.stSlider > div > div:nth-child(3) {
    background-color: transparent !important;
}

.stSlider > div > div:nth-child(3) > span {
    color: #007bff; 
    background-color: transparent !important;
    border: none !important;
    font-family: 'Roboto', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

# Get API key from Streamlit secrets
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception as e:
    logging.error(f"GOOGLE_API_KEY not found in Streamlit secrets: {e}")
    st.error(
        "⚠️ GOOGLE_API_KEY not found in Streamlit secrets! Make sure to add it in the Streamlit Cloud dashboard."
    )
    st.stop()

# Configure API with error handling
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
except Exception as e:
    logging.error(f"Error configuring Gemini API: {e}")
    st.error(f"⚠️ Error configuring Gemini API: {str(e)}")
    st.stop()

# --- Main Title ---
st.markdown("<h1 class='main-title'>🤖</h1>", unsafe_allow_html=True)  # Changed title to just the robot emoji

# --- Subheader ---
st.markdown("<p class='subheader'>This bot uses multiple AI agents to analyze topics in depth with sophisticated reasoning.</p>", unsafe_allow_html=True)

# Initialize session state for storing analysis results and previous input
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

# Input section
topic = st.text_input(
    "Enter a topic or question:",
    placeholder='e.g. "Is the Ivory-billed woodpecker really extinct?"',
)

# Reset session state if input changes
if topic != st.session_state.previous_input:
    st.session_state.analysis_complete = False
    st.session_state.pdf_buffer = None
    st.session_state.final_analysis = None
    st.session_state.research_results = []
    st.session_state.tldr_summary = None
    st.session_state.refined_prompt = None
    st.session_state.framework = None
    st.session_state.previous_input = topic

# --- UI/UX - Add expander for prompt details ---
with st.expander("**☠️ Advanced Prompt Customization ☠️**"):
    # Agent Prompts
    agent1_prompt = st.text_area(
        "Agent 1 Prompt (Prompt Engineer)",
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
        key="agent1_prompt",
        height=300,
    )

    agent2_prompt = st.text_area(
        "Agent 2 Prompt (Researcher)",
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
        key="agent2_prompt",
        height=300,
    )

    agent3_prompt = st.text_area(
        "Agent 3 Prompt (Expert Analyst)",
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
        key="agent3_prompt",
        height=300,
    )

# Slider for research depth with descriptive options
loops = st.select_slider(
    "How deep should we dive?",
    options=["Puddle", "Lake", "Ocean", "Mariana Trench"],
    value="Lake",
)

# Create columns for button
_, _, button_col = st.columns([1, 1, 1])

with button_col:
    start_button_clicked = st.button("🌊 Dive In", key="start_button")

# Add progress bar placeholder before TL;DR
progress_placeholder = st.empty()

# Display previous results if they exist
if st.session_state.analysis_complete:
    if st.session_state.tldr_summary:
        with st.expander(f"**💡 TL;DR**", expanded=True):
            st.markdown(st.session_state.tldr_summary)
    
    if st.session_state.refined_prompt:
        with st.expander(f"**🎯 Refined Prompt**", expanded=False):
            st.markdown(st.session_state.refined_prompt)
    
    if st.session_state.framework:
        with st.expander(f"**🗺️ Investigation Framework**", expanded=False):
            st.markdown(st.session_state.framework)
    
    for title, content in st.session_state.research_results:
        with st.expander(f"**{title}**", expanded=False):
            st.markdown(content)
    
    if st.session_state.final_analysis:
        with st.expander(f"**📋 Final Report**", expanded=False):
            st.markdown(st.session_state.final_analysis)
        
        # Create columns for download button only
        _, download_col = st.columns([1, 2])
        with download_col:
            st.download_button(
                label="⬇️ Download Report as PDF",
                data=st.session_state.pdf_buffer,
                file_name=f"{topic}_analysis_report.pdf",
                mime="application/pdf",
                key="download_button",
                help="Download the complete analysis report as a PDF file",
                use_container_width=True
            )

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

if start_button_clicked:
    if topic:
        # Reset session state
        st.session_state.analysis_complete = False
        st.session_state.research_results = []
        
        # Initialize progress indicators
        progress_states = {
            "tldr": {"label": "TL;DR", "progress": 0, "status": "pending"},
            "refined_prompt": {"label": "Refined Prompt", "progress": 0, "status": "pending"},
            "framework": {"label": "Investigation Framework", "progress": 0, "status": "pending"},
            "research": {"label": "Research Phases", "progress": 0, "status": "pending"},
            "analysis": {"label": "Final Report", "progress": 0, "status": "pending"},
        }

        # Initialize overall progress bar
        progress_bar = progress_placeholder.progress(0)

        try:
            # Create placeholder for random facts
            facts_placeholder = st.empty()
            
            # Display initial random fact
            with facts_placeholder.container():
                with st.expander("**🎲 Random Fact**", expanded=True):
                    st.markdown(generate_random_fact(topic))
            
            # Start fact update loop in the background
            def update_fact():
                time.sleep(8)  # Wait 8 seconds before showing new facts
                while not st.session_state.analysis_complete:
                    with facts_placeholder.container():
                        with st.expander("**🎲 Random Fact**", expanded=True):
                            st.markdown(generate_random_fact(topic))
                    time.sleep(12)  # Show new fact every 12 seconds
            
            # Start the fact update loop in a separate thread
            import threading
            fact_thread = threading.Thread(target=update_fact)
            fact_thread.daemon = True
            fact_thread.start()

            # Quick Summary (TL;DR)
            tldr_summary = generate_quick_summary(topic)
            if tldr_summary:
                st.session_state.tldr_summary = tldr_summary
                with st.expander(f"**💡 {progress_states['tldr']['label']}**", expanded=True):
                    st.markdown(tldr_summary)
                progress_bar.progress(20)

            # Agent 1: Refine prompt and generate framework
            refined_prompt, framework = generate_refined_prompt_and_framework(topic)
            if refined_prompt and framework:
                st.session_state.refined_prompt = refined_prompt.lstrip(":\n").strip()
                st.session_state.framework = framework.lstrip(": **\n").strip()
                
                # Display refined prompt
                with st.expander(f"**🎯 {progress_states['refined_prompt']['label']}**", expanded=False):
                    st.markdown(st.session_state.refined_prompt)
                
                # Display framework
                with st.expander(f"**🗺️ {progress_states['framework']['label']}**", expanded=False):
                    st.markdown(st.session_state.framework)
                progress_bar.progress(40)

                # Agent 2: Conduct research through iterations
                current_analysis = ""
                aspects = []
                research_expanders = []

                # Extract aspects from framework
                if framework:
                    for line in framework.split("\n"):
                        if line.strip().startswith(("1.", "2.", "3.", "4.")):
                            aspects.append(line.strip())

                # Conduct research phases
                for i in range(loops_num):
                    current_aspect = random.choice(aspects) if aspects else "Current State and Trends"
                    research = conduct_research(refined_prompt, framework, current_analysis, current_aspect, i + 1)
                    
                    if research:
                        current_analysis += "\n\n" + research
                        research_lines = research.split("\n")
                        title = next((line for line in research_lines if line.strip()), current_aspect)
                        research_content = "\n".join(research_lines[1:])
                        # Add research emoji based on content
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

                # Display research phases
                for title, content in research_expanders:
                    with st.expander(f"**{title}**", expanded=False):
                        st.markdown(content)

                # Agent 3: Generate final analysis
                final_response = model.generate_content(
                    agent3_prompt.format(
                        refined_prompt=refined_prompt,
                        system_prompt=framework,
                        all_aspect_analyses=current_analysis,
                    ),
                    generation_config=agent3_config,
                )
                final_analysis = handle_response(final_response)

                # Create PDF buffer
                pdf_buffer = create_download_pdf(refined_prompt, framework, current_analysis, final_analysis)

                # Store research results in session state
                st.session_state.research_results = research_expanders
                
                # Store final analysis in session state
                st.session_state.final_analysis = final_analysis
                
                # Store PDF buffer in session state
                st.session_state.pdf_buffer = pdf_buffer
                
                # Mark analysis as complete
                st.session_state.analysis_complete = True

                # Display final report last
                with st.expander(f"**📋 {progress_states['analysis']['label']}**", expanded=False):
                    st.markdown(final_analysis)

                progress_bar.progress(100)

                # Update progress bar color based on progress
                progress_bar = progress_placeholder.progress(0)
                st.markdown(
                    f"""
                    <style>
                    .stProgress > div > div > div > div {{
                        background: linear-gradient(90deg, 
                            #007bff 0%, 
                            #007bff {min(progress_bar.progress, 100)}%, 
                            {('#28a745' if progress_bar.progress == 100 else '#007bff')} {min(progress_bar.progress, 100)}%, 
                            {('#28a745' if progress_bar.progress == 100 else '#007bff')} 100%
                        );
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True
                )

                # Create columns for download button only
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