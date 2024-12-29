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

# Update input section with embedded button
col1, col2 = st.columns([4, 1])
with col1:
    topic = st.text_input(
        "Enter a topic or question:",
        placeholder='e.g. "Is the Ivory-billed woodpecker really extinct?"',
        key="topic_input",
        on_change=lambda: setattr(st.session_state, 'start_button_clicked', True) if st.session_state.topic_input else None
    )
with col2:
    start_button_clicked = st.button("🌊 Dive In", key="start_button", use_container_width=True)

# Add random fact placeholder at the top of analysis section
fact_placeholder = st.empty()

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

def create_download_pdf(refined_prompt, framework, research_analysis, final_analysis):
    """Create a PDF report from the analysis results."""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Set font
        pdf.set_font("Helvetica", size=12)
        
        # Add title
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Analysis Report", ln=True, align="C")
        pdf.ln(10)
        
        # Add refined prompt section
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Refined Prompt", ln=True)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, refined_prompt)
        pdf.ln(10)
        
        # Add framework section
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Investigation Framework", ln=True)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, framework)
        pdf.ln(10)
        
        # Add research analysis section
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Research Analysis", ln=True)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, research_analysis)
        pdf.ln(10)
        
        # Add final analysis section
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Final Analysis", ln=True)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, final_analysis)
        
        # Return PDF as bytes
        return pdf.output(dest='S').encode('latin-1')
        
    except Exception as e:
        logging.error(f"Failed to create PDF: {e}")
        # Create a simple PDF with error message
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 10, "Error creating PDF report. Please try again.", ln=True)
        return pdf.output(dest='S').encode('latin-1')

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
        
        # Extract refined prompt and framework from agent 1's response
        if agent1_response:
            parts = agent1_response.split("---")
            if len(parts) >= 2:
                # Clean up the refined prompt section
                refined_prompt = parts[0].replace("Refined Prompt", "").strip()
                
                # Clean up the framework section
                framework = parts[1].strip()
                if framework.startswith("Investigation Framework"):
                    framework = framework[len("Investigation Framework"):].strip()
                
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
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,
                top_p=0.7,
                top_k=40,
                max_output_tokens=2048,
            ),
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

if start_button_clicked or st.session_state.get('start_button_clicked', False):
    if topic:
        # Reset session state
        st.session_state.analysis_complete = False
        st.session_state.research_results = []
        
        # Initialize progress bar
        progress_bar = st.progress(0)
        
        try:
            # Display initial random fact
            with fact_placeholder.container():
                with st.expander("🎲 Random Fact", expanded=True):
                    st.markdown(generate_random_fact(topic))
            
            # Start fact update loop in the background
            def update_fact():
                while not st.session_state.analysis_complete:
                    time.sleep(8)  # Wait before showing new facts
                    with fact_placeholder.container():
                        with st.expander("🎲 Random Fact", expanded=True):
                            st.markdown(generate_random_fact(topic))
            
            # Start the fact update thread
            import threading
            fact_thread = threading.Thread(target=update_fact)
            fact_thread.daemon = True
            fact_thread.start()

            # Quick Summary (TL;DR)
            tldr_summary = generate_quick_summary(topic)
            if tldr_summary:
                progress_bar.progress(20)
                st.session_state.tldr_summary = tldr_summary
                with st.expander("💡 TL;DR", expanded=True):
                    st.markdown(tldr_summary)

            # Agent 1: Refine prompt and generate framework
            refined_prompt, framework = generate_refined_prompt_and_framework(topic)
            if refined_prompt and framework:
                st.session_state.refined_prompt = refined_prompt.lstrip(":\n").strip()
                st.session_state.framework = framework.lstrip(": **\n").strip()
                
                # Display refined prompt
                with st.expander(f"**🎯 Refined Prompt**", expanded=False):
                    st.markdown(st.session_state.refined_prompt)
                
                # Display framework
                with st.expander(f"**🗺️ Investigation Framework**", expanded=False):
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
                with st.expander(f"**📋 Final Report**", expanded=False):
                    st.markdown(final_analysis)

                progress_bar.progress(100)

                # Update progress bar color when complete
                if st.session_state.analysis_complete:
                    st.markdown(
                        """
                        <style>
                        .stProgress > div > div > div > div {
                            background-color: #28a745 !important;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True
                    )

                # Update download button to be simpler text
                if st.session_state.analysis_complete:
                    _, download_col = st.columns([1, 2])
                    with download_col:
                        st.download_button(
                            label="⬇️ Download Report",
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