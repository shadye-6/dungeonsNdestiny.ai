# memory/summarizer.py
from llm.story_engine import generate_response

def summarize_for_memory(text: str) -> str:
    """
    Summarizes a DM response into a concise form suitable for persistent memory.
    """
    prompt = f"""
You are an AI assistant tasked with summarizing game events.
Summarize the following text into 1-2 sentences, preserving key characters, events, and locations:

Text:
{text}

Summary:
"""
    summary = generate_response(prompt)
    # Optional: clean text
    summary = summary.strip().replace("\n", " ")
    return summary
