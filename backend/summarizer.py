"""
summarizer.py
=============
Generates concise summaries of truncated conversation history
to preserve key context without exceeding token limits.
"""

from typing import List, Dict
from backend.llm import ask_llm_stream

SUMMARIZE_PROMPT = """You are a helpful AI system maintaining conversation memory.
Summarize the following conversation history concisely.

Focus specifically on preserving:
1. Key facts about the user (e.g., name, preferences, project specifics).
2. Major topics discussed or conclusions reached.
3. Any open questions or explicit constraints mentioned by the user.

Keep the summary under 150 words. Do NOT include greetings or meta-commentary.

Conversation History to Summarize:
"""

def summarize_messages(messages: List[Dict[str, str]]) -> str:
    """Takes a list of message dicts and generates a concise summary string."""
    if not messages:
        return ""

    formatted_history = ""
    for msg in messages:
        role = "User" if msg["role"] == "user" else "Assistant"
        formatted_history += f"{role}: {msg['content']}\n"

    prompt = [
        {"role": "system", "content": "You are a concise summarizer."},
        {"role": "user", "content": f"{SUMMARIZE_PROMPT}\n{formatted_history}"},
    ]

    try:
        # Collect and join all streaming tokens yielded by ask_llm_stream
        summary_text = "".join(list(ask_llm_stream(prompt)))
        return summary_text.strip()
    except Exception as e:
        print(f"[Summarization Error]: {e}")
        return ""