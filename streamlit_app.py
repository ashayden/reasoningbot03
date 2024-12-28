import streamlit as st
import google.generativeai as genai
import json
import re
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
loops = st.slider("How many reasoning iterations per aspect?", min_value=1, max_value=3, value=2)

# Agent Prompts
agent1_prompt = """You are a JSON generator. Output a JSON object analyzing: {topic}

ONLY output the JSON structure below:

{
    "direct_answer": "A clear yes/no/uncertain answer followed by one sentence explanation",
    "aspects": {
        "What are the key components or elements of {topic}?": [
            "First key component with brief explanation",
            "Second key component with brief explanation"
        ],
        "How does {topic} impact or influence its domain?": [
            "First major impact or influence",
            "Second major impact or influence"
        ],
        "What are the future implications or developments of {topic}?": [
            "First future implication or trend",
            "Second future implication or trend"
        ]
    }
}

CRITICAL:
- Output ONLY the JSON above
- Start with { and end with }
- Use " for all strings
- No comments or explanation
- No markdown formatting
- No extra text before or after"""

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

# Enhanced JSON Parsing and Validation

def clean_and_extract_json(raw_response):
    """
    Cleans and extracts a JSON object from a raw string response.

    Args:
        raw_response: The raw string response from the model.

    Returns:
        A dictionary representing the parsed JSON object, or None if parsing fails.
    """
    logging.info("Starting JSON extraction")

    # 1. Find the start and end of the JSON object
    json_start = raw_response.find('{')
    json_end = raw_response.rfind('}') + 1

    if json_start == -1 or json_end == 0:
        logging.error("No JSON object found")
        return None

    json_string = raw_response[json_start:json_end]

    # 2. Remove all newlines and extra whitespace
    json_string = json_string.replace('\n', '').replace('\\n', '')
    json_string = re.sub(r'\s+', ' ', json_string)

    # 3. Remove any trailing commas before closing braces/brackets
    json_string = re.sub(r',\s*}', '}', json_string)
    json_string = re.sub(r',\s*]', ']', json_string)

    # 4. Escape unescaped double quotes inside strings
    json_string = re.sub(r'(?<!\\)"(?=[^":]*":)', '\\"', json_string)

    # 5. Attempt to parse the cleaned JSON string
    try:
        parsed_json = json.loads(json_string)
        logging.info("JSON parsed successfully")
        return parsed_json
    except json.JSONDecodeError as e:
        logging.error(f"JSON parsing failed: {str(e)}")
        return None

# Simplify Agent 1 Prompt
agent1_prompt = """You are a JSON generator. Output a JSON object analyzing: {topic}

ONLY output the JSON structure below:

{
    "direct_answer": "A clear yes/no/uncertain answer followed by one sentence explanation",
    "aspects": {
        "What are the key components or elements of {topic}?": [
            "First key component with brief explanation",
            "Second key component with brief explanation"
        ],
        "How does {topic} impact or influence its domain?": [
            "First major impact or influence",
            "Second major impact or influence"
        ],
        "What are the future implications or developments of {topic}?": [
            "First future implication or trend",
            "Second future implication or trend"
        ]
    }
}

CRITICAL:
- Output ONLY the JSON above
- Start with { and end with }
- Use " for all strings
- No comments or explanation
- No markdown formatting
- No extra text before or after"""

# Streamline Response Handling

def handle_response(response):
    """Handle model response and extract text."""
    if hasattr(response, 'parts'):
        return response.parts[0].text.strip()
    return response.text.strip()

# Add UI Feedback
st.spinner("Processing...")

# Refactor Code Structure

def generate_framework(topic):
    """Generate analysis framework using Agent 1."""
    max_retries = 3
    retry_count = 0
    framework = None
    raw_response = None

    while retry_count < max_retries and framework is None:
        try:
            prompt_response = model.generate_content(
                agent1_prompt.format(topic=topic),
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    top_p=0.1,
                    top_k=1,
                    max_output_tokens=2048,
                    stop_sequences=["\n\n", "```"]
                )
            )

            raw_response = handle_response(prompt_response)
            framework = clean_and_extract_json(raw_response)

            if framework is None:
                raise ValueError("Failed to clean and extract JSON")

            # Validate structure
            if not isinstance(framework, dict):
                raise ValueError("Response is not a dictionary")
            if "direct_answer" not in framework:
                raise ValueError("Missing 'direct_answer' field")
            if "aspects" not in framework:
                raise ValueError("Missing 'aspects' field")
            if not isinstance(framework["aspects"], dict):
                raise ValueError("'aspects' is not a dictionary")
            if len(framework["aspects"]) != 3:
                raise ValueError("Wrong number of aspects")

            # Validate each aspect
            for aspect, data_points in framework["aspects"].items():
                if not isinstance(data_points, list):
                    raise ValueError(f"Data points for '{aspect}' is not a list")
                if len(data_points) != 2:
                    raise ValueError(f"Wrong number of data points for '{aspect}'")

            logging.info("Framework generated successfully")
            return framework

        except Exception as e:
            retry_count += 1
            logging.warning(f"Retry {retry_count}/{max_retries}: {str(e)}")
            time.sleep(1)

    logging.error("Failed to generate valid framework after retries")
    return None

# Main Execution
if st.button("Start Analysis"):
    if topic:
        framework = generate_framework(topic)
        if framework is None:
            st.error("Failed to generate a valid framework. Analysis cannot continue.")
            st.stop()

        # Continue with Agent 2, 3, and 4 logic...
        # (Refactor similar to Agent 1)

    else:
        st.warning("Please enter a topic to analyze.")