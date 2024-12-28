import streamlit as st
import google.generativeai as genai
import time
import logging

# Configure logging with debug level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Get API key from Streamlit secrets
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception as e:
    st.error("⚠️ GOOGLE_API_KEY not found in Streamlit secrets! Make sure to add it in the Streamlit Cloud dashboard.")
    st.stop()

# Configure API with error handling
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-1219")  
except Exception as e:
    st.error(f"⚠️ Error configuring Gemini API: {str(e)}")
    st.stop()

# Streamlit UI
st.title("🤔 Advanced Reasoning Bot")
st.write("This bot uses multiple AI agents to analyze topics in depth with sophisticated reasoning.")

# Input section
topic = st.text_input("What topic should we explore?")
loops = st.slider("How many reasoning iterations per aspect?", min_value=1, max_value=10, value=2)

# Agent Prompts
agent1_prompt = '''You are an expert analyst. Your task is to analyze this topic: {topic}

Direct Answer:
- Your answer here

Key Components or Elements:
- Your first point here
- Your second point here

Impact or Influence:
- Your first point here
- Your second point here

Future Implications or Developments:
- Your first point here
- Your second point here

RULES:
1. Keep the section headings EXACTLY as shown
2. Start each section with the heading and a colon
3. Start each point with a hyphen
4. Include at least one point per section
5. Do not add any other text

EXAMPLE OUTPUT:

Direct Answer:
- Yes, artificial intelligence is transforming our world through its ability to automate complex tasks.

Key Components or Elements:
- Machine Learning algorithms that enable systems to learn from experience
- Neural Networks designed to process information like biological brains

Impact or Influence:
- Automation of routine tasks increasing efficiency across industries
- Enhanced decision-making through data analysis

Future Implications or Developments:
- Integration of AI into healthcare for improved diagnosis
- Development of autonomous transportation systems

END OF EXAMPLE

Remember: Use the EXACT same format for {topic}. Keep the section headings identical.'''

agent2_prompt = """As an Analysis Refiner, provide a detailed analysis of the following:

FOCUS AREA: {current_aspect}
# [Rephrase this aspect using natural language, focusing on the core concept]

PREVIOUS INSIGHTS:
{previous_analysis}

Structure your analysis as follows:

*[MAIN TITLE]*

1. [Descriptive Heading]
   Detailed explanation with supporting evidence

2. [Descriptive Heading]
   Detailed explanation with supporting evidence

3. [Descriptive Heading]
   Detailed explanation with supporting evidence

Each point should:
- Build upon the previous analysis
- Add NEW information and insights
- Include specific data or examples where relevant
- Connect to the broader implications for the subject"""

agent3_prompt = """As an Expert Response Generator, synthesize this comprehensive analysis:

SUBJECT MATTER:
[Naturally rephrase {topic} to focus on the core concept]

FRAMEWORK:
{system_prompt}

DETAILED ANALYSIS:
{all_aspect_analyses}

Your response should follow this EXACT format:

### Comprehensive Analysis

**OVERVIEW:**
[2-3 sentences introducing the core concept and its significance]

**DETAILED ANALYSIS:**

Key Factors Driving [Topic]:
• [Factor 1]
• [Factor 2]
• [Factor 3]
• [Factor 4]
• [Factor 5]

Impact on [Domain]:
• [Impact 1]: [Brief explanation]
• [Impact 2]: [Brief explanation]
• [Impact 3]: [Brief explanation]
• [Impact 4]: [Brief explanation]

**IMPLICATIONS AND FUTURE OUTLOOK:**
• [Implication 1]
• [Implication 2]
• [Implication 3]
• [Implication 4]

Maintain:
- Clear, authoritative voice
- Bullet points with consistent formatting
- Bold section headers
- One line spacing between sections
- Proper indentation for sub-points"""

agent4_prompt = """As a Concise Overview Generator, provide a structured summary of this expert analysis:

SUBJECT:
[Naturally rephrase {topic} to focus on the core concept]

EXPERT ANALYSIS:
{expert_text}

Structure your response in THREE parts:

TL;DR:
 [If the user asked a question answer it with"✅ Yes" / "❌ No" / "❓ Uncertain"] + [One sentence that directly answers the core question or summarizes the key finding]

KEY TAKEAWAYS:
• [Action] + [Specific Detail] + [Impact/Significance]
• Include 5-7 bullet points
• Focus on concrete facts, numbers, and examples
• Start each point with a clear action verb
• Maintain consistent bullet point formatting

EXECUTIVE SUMMARY:
[Two paragraphs that:
- Synthesize the main ideas into a coherent narrative
- Explain the significance of the core concept
- Highlight the most significant implications
- Use clear, professional language]"""

# Streamline Response Handling

def handle_response(response):
    """Handle model response and extract text."""
    if hasattr(response, 'parts'):
        return response.parts[0].text.strip()
    return response.text.strip()

def parse_structured_text(raw_response):
    """
    Parses the structured text response into sections.
    
    Args:
        raw_response: The raw text response from the model.
        
    Returns:
        A dictionary containing the parsed sections, or None if parsing fails.
    """
    try:
        sections = {}
        current_section = None
        current_points = []
        
        for line in raw_response.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check if line is a section header
            if line.endswith(':'):
                if current_section and current_points:
                    sections[current_section] = current_points
                current_section = line[:-1]  # Remove the colon
                current_points = []
            # Check if line is a bullet point
            elif line.startswith('- '):
                current_points.append(line[2:])  # Remove the "- " prefix
                
        # Add the last section
        if current_section and current_points:
            sections[current_section] = current_points
            
        logging.info("Successfully parsed structured text")
        return sections
        
    except Exception as e:
        logging.error(f"Failed to parse structured text: {str(e)}")
        return None

def generate_analysis(topic):
    """Generate structured analysis using Agent 1."""
    max_retries = 3
    retry_count = 0
    analysis = None
    raw_response = None

    while retry_count < max_retries and analysis is None:
        try:
            # Add safety rails to generation parameters
            prompt_response = model.generate_content(
                agent1_prompt.format(topic=topic),
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    top_p=0.1,
                    top_k=1,
                    max_output_tokens=2048,
                    candidate_count=1,
                    stop_sequences=["\n\n\n"]
                )
            )

            raw_response = handle_response(prompt_response)
            
            # Log the raw response for debugging
            logging.debug(f"Raw response:\n{raw_response}")
            
            analysis = parse_structured_text(raw_response)
            
            if analysis is None:
                raise ValueError("Failed to parse structured text response")

            # Log the parsed sections for debugging
            logging.debug(f"Parsed sections: {list(analysis.keys())}")

            # Validate sections
            required_sections = [
                "Direct Answer",
                "Key Components or Elements",
                "Impact or Influence",
                "Future Implications or Developments"
            ]
            
            for section in required_sections:
                if section not in analysis:
                    logging.debug(f"Missing section: {section}")
                    logging.debug(f"Available sections: {list(analysis.keys())}")
                    raise ValueError(f"Missing required section: {section}")
                if not analysis[section]:
                    raise ValueError(f"No points found in section: {section}")

            logging.info("Analysis generated successfully")
            return analysis

        except Exception as e:
            retry_count += 1
            logging.warning(f"Retry {retry_count}/{max_retries}: {str(e)}")
            if raw_response:
                logging.debug(f"Failed response:\n{raw_response}")
            time.sleep(1)

    logging.error("Failed to generate valid analysis after retries")
    return None

# Main Execution
if st.button("Start Analysis"):
    if topic:
        with st.spinner("Generating analysis..."):
            analysis = generate_analysis(topic)
            
            if analysis is None:
                st.error("Failed to generate analysis. Please try again.")
                st.stop()
            
            # Display the analysis
            st.success("Analysis complete!")
            
            for section, points in analysis.items():
                st.markdown(f"### {section}")
                for point in points:
                    st.markdown(f"- {point}")
                st.markdown("")  # Add spacing between sections

            # Continue with Agent 2, 3, and 4 logic...
            # (Update these to work with the new structured format)

    else:
        st.warning("Please enter a topic to analyze.")