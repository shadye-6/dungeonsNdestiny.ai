from llm.story_engine import generate_response


def summarize_for_memory(text: str) -> str:
    """Compress a DM response into 1-2 sentences for long-term memory storage."""
    prompt = f"""You are an assistant summarizing events in a tabletop RPG.
Summarize the following text in 1-2 sentences, preserving key characters, locations, and events.

Text:
{text}

Summary:"""

    try:
        summary = generate_response(prompt)
        return summary.strip().replace("\n", " ")
    except Exception:
        # Fallback: truncate the original text rather than crashing
        return text[:200].strip()
