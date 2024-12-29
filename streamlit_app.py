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
.stProgress > div > div > div > div {
    background-color: #007bff !important; /* Match the slider blue color */
    border-radius: 20px;
    height: 38px; /* Match the height of the Dive In button */
}

.stProgress {
    background-color: rgba(0, 123, 255, 0.1);
    border-radius: 20px;
    padding: 0;
    margin-top: 3px; /* Align with button */
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

# Input section
topic = st.text_input(
    "Enter a topic or question:",
    placeholder="e.g., 'What are the impacts of AI on the economy?'",
)

# --- UI/UX - Add expander for prompt details ---
with st.expander("**Advanced Prompt Customization**"):
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

# Convert the depth selection to a numerical value
if loops == "Puddle":
    loops_num = 1
elif loops == "Lake":
    loops_num = random.randint(2, 3)
elif loops == "Ocean":
    loops_num = random.randint(4, 6)
elif loops == "Mariana Trench":
    loops_num = random.randint(7, 10)
else:
    loops_num = 2  # Default value

def handle_response(response):
    """Handle model response and extract text with more specific error handling."""
    try:
        if hasattr(response, "parts") and response.parts:
            if text_part := next(
                (part.text for part in response.parts if part.text), None
            ):
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


# Define default generation config
default_generation_config = genai.types.GenerationConfig(
    temperature=0.7, top_p=0.8, top_k=40, max_output_tokens=2048
)

# Create new GenerationConfig objects for other agents:
agent2_config = genai.types.GenerationConfig(
    temperature=0.5, top_p=0.7, top_k=40, max_output_tokens=2048
)

agent3_config = genai.types.GenerationConfig(
    temperature=0.3, top_p=0.7, top_k=20, max_output_tokens=4096
)

def generate_quick_summary(topic):
    """Generate a quick summary (TL;DR) using the model."""
    try:
        quick_summary_prompt = f"""
        Provide a very brief, one to two-sentence TL;DR (Too Long; Didn't Read) overview of the following topic, incorporating emojis where relevant:
        {topic}
        """
        response = model.generate_content(
            quick_summary_prompt,
            generation_config=default_generation_config,
        )
        summary = handle_response(response)
        # Ensure summary is within 1-2 sentences
        sentences = summary.split('.')
        if len(sentences) > 2:
            summary = '. '.join(sentences[:2]) + '.' if sentences[0] else ''
        return summary.strip()
    except Exception as e:
        logging.error(f"Failed to generate quick summary: {e}")
        return ""

def generate_refined_prompt_and_framework(topic):
    """Generate a refined prompt and investigation framework using Agent 1."""
    try:
        prompt_response = model.generate_content(
            agent1_prompt.format(topic=topic),
            generation_config=default_generation_config,
        )

        agent1_response = handle_response(prompt_response)

        # Extract refined prompt and framework from agent 1's response
        if agent1_response:
            parts = agent1_response.split("---")
            if len(parts) >= 2:
                # Clean up the refined prompt section
                refined_prompt = parts[0].replace("Refined Prompt", "").strip()

                # Clean up the framework section
                framework = parts[1].strip()
                if framework.startswith("Investigation Framework"):
                    framework = framework[len("Investigation Framework") :].strip()

                # Remove any stray colons from section headers
                framework = framework.replace(
                    "Core Question/Hypothesis:", "Core Question/Hypothesis"
                )
                framework = framework.replace(
                    "Key Areas Requiring Investigation:", "Key Areas Requiring Investigation"
                )

                # Further clean up for framework formatting
                framework_lines = framework.split("\n")
                cleaned_framework_lines = []
                for line in framework_lines:
                    # Ensure consistent indentation for bullet points
                    if line.lstrip().startswith("-"):
                        cleaned_framework_lines.append("   " + line.lstrip())
                    else:
                        cleaned_framework_lines.append(line)
                framework = "\n".join(cleaned_framework_lines)

                logging.info(
                    "Refined prompt and investigation framework generated successfully"
                )
                return refined_prompt, framework
            else:
                logging.warning(
                    "Could not properly split the response from Agent 1 into refined prompt and framework."
                )
        else:
            logging.warning("Agent 1 response was empty or invalid.")

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
            generation_config=agent2_config,
        )

        research = handle_response(prompt_response)
        if research:
            # Remove any iteration focus headers if they exist
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


def create_download_pdf(refined_prompt, framework, current_analysis, final_analysis):
    """Create a PDF for download with proper Unicode handling."""
    try:
        buffer = io.BytesIO()
        pdf = FPDF()
        pdf.add_page()

        # Set font and size for title
        pdf.set_font('Helvetica', '', 16)
        pdf.cell(0, 10, "Advanced Reasoning Bot Report", 0, 1, 'C')
        pdf.ln(10)

        # Set font for content
        pdf.set_font('Helvetica', '', 12)

        # Add framework
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, "Investigation Framework", 0, 1)
        pdf.set_font('Helvetica', '', 12)
        
        # Clean and encode text
        clean_framework = ''.join(char if ord(char) < 128 else '?' for char in framework)
        pdf.multi_cell(0, 10, clean_framework)
        pdf.ln(5)

        # Add research phases
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, "Research Phases", 0, 1)
        pdf.set_font('Helvetica', '', 12)
        
        # Clean and encode text
        clean_analysis = ''.join(char if ord(char) < 128 else '?' for char in current_analysis)
        pdf.multi_cell(0, 10, clean_analysis)
        pdf.ln(5)

        # Add final report
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, "Final Report", 0, 1)
        pdf.set_font('Helvetica', '', 12)
        
        # Clean and encode text
        clean_final = ''.join(char if ord(char) < 128 else '?' for char in final_analysis)
        pdf.multi_cell(0, 10, clean_final)

        pdf_output = pdf.output(dest='S').encode('latin-1')
        buffer = io.BytesIO(pdf_output)
        buffer.seek(0)
        return buffer

    except Exception as e:
        logging.error(f"Error creating PDF: {e}")
        # Return a simplified PDF with error message
        buffer = io.BytesIO()
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Helvetica', '', 12)
        pdf.cell(0, 10, "Error creating PDF report. Some characters could not be encoded.", 0, 1)
        pdf_output = pdf.output(dest='S').encode('latin-1')
        buffer = io.BytesIO(pdf_output)
        buffer.seek(0)
        return buffer

# Main Execution
# Create columns for buttons and progress bar
button_col, progress_col = st.columns([1, 2])

with button_col:
    start_button_clicked = st.button("🌊 Dive In", key="start_button")

with progress_col:
    progress_placeholder = st.empty()

if start_button_clicked:
    if topic:
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
            # Quick Summary (TL;DR)
            tldr_summary = generate_quick_summary(topic)
            if tldr_summary:
                with st.expander(f"**💡 {progress_states['tldr']['label']}**", expanded=True):
                    st.markdown(tldr_summary)
                progress_bar.progress(20)

            # Agent 1: Refine prompt and generate framework
            refined_prompt, framework = generate_refined_prompt_and_framework(topic)
            if refined_prompt and framework:
                # Display refined prompt
                with st.expander(f"**🎯 {progress_states['refined_prompt']['label']}**", expanded=False):
                    st.markdown(refined_prompt.lstrip(":\n").strip())
                
                # Display framework
                with st.expander(f"**🗺️ {progress_states['framework']['label']}**", expanded=False):
                    st.markdown(framework.lstrip(": **\n").strip())
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
                        if "economic" in title.lower() or "finance" in title.lower():
                            emoji = "📊"
                        elif "environment" in title.lower() or "climate" in title.lower():
                            emoji = "🌍"
                        elif "culture" in title.lower() or "social" in title.lower():
                            emoji = "🎭"
                        elif "history" in title.lower() or "heritage" in title.lower():
                            emoji = "📜"
                        elif "technology" in title.lower() or "innovation" in title.lower():
                            emoji = "💻"
                        elif "education" in title.lower() or "learning" in title.lower():
                            emoji = "📚"
                        elif "health" in title.lower() or "medical" in title.lower():
                            emoji = "🏥"
                        else:
                            emoji = "🔍"
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

                # Display final report last
                with st.expander(f"**📋 {progress_states['analysis']['label']}**", expanded=False):
                    st.markdown(final_analysis)

                progress_bar.progress(100)

                # Create columns for completion message and download button
                msg_col, download_col = st.columns([1, 2])
                with msg_col:
                    st.markdown("🥂 Analysis Complete")
                with download_col:
                    st.download_button(
                        label="⬇️ Download Report as PDF",
                        data=pdf_buffer,
                        file_name=f"{topic}_analysis_report.pdf",
                        mime="application/pdf",
                        key="download_button",
                        help="Download the complete analysis report as a PDF file",
                        use_container_width=True,
                        on_click=None  # Prevent rerun on click
                    )

        except Exception as e:
            st.error(f"Analysis failed: {str(e)}. Please try again.")
            logging.error(f"Analysis failed: {e}")

    else:
        st.warning("Please enter a topic to analyze.")