import google.generativeai as genai

genai.configure(api_key="AIzaSyA3szOv69RF7vT9qOLsZyRygoQWOdnc760")
model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-1219")

# Agent 1: Creates sophisticated prompt structure (low temperature for focused, consistent output)
print("Agent 1: Let me gather some information from you.")
topic = input("What topic should we explore? ")
loops = int(input("How many reasoning iterations? "))

print("\nAgent 1: Formulating analysis framework...")
prompt_response = model.generate_content(
    f"""Create a detailed system prompt for analyzing '{topic}'. 
    Include instructions for examining multiple perspectives, potential implications, and interconnected aspects.
    Be specific but concise.""",
    generation_config=genai.types.GenerationConfig(
        temperature=0.3
    ),
    stream=True
)

system_prompt = ""
for chunk in prompt_response:
    system_prompt += chunk.text
    print(chunk.text, end='', flush=True)

# Agent 2: Reasoning agent (high temperature for creative insights)
full_analysis = []
context = topic
for i in range(loops):
    print(f"\n\nReasoning Loop {i+1}/{loops}:")
    response = model.generate_content(
        f"""{system_prompt}
        
        Previous context: {context}
        Analyze this topic as if you were a Nobel Prize winner in the relevant field, drawing upon deep expertise and groundbreaking insights. Provide fresh analysis following the framework above.""",
        generation_config=genai.types.GenerationConfig(
            temperature=1.0
        ),
        stream=True
    )
    context = ""
    loop_content = ""
    for chunk in response:
        context += chunk.text
        loop_content += chunk.text
        print(chunk.text, end='', flush=True)
    full_analysis.append(loop_content)
    print("\n" + "-"*50)

# Agent 3: Summarization agent (very low temperature for consistent, focused summary)
print("\n\nAgent 3: Final Summary")
summary = model.generate_content(
    f"""Synthesize the findings from the analysis loops about '{topic}' into a clear, comprehensive summary in simple language bulleting key points and crafting a concise summary paragraph. Finally, suggest 3 follow-up questions, 1 that digs deeper into a key aspect of the topic, 1 that explores a related topic, and 1 that investigates unexpected connections to the topic:

    {' '.join(full_analysis)}""",
    generation_config=genai.types.GenerationConfig(
        temperature=0.1
    ),
    stream=True
)

for chunk in summary:
    print(chunk.text, end='', flush=True)

