"""
context.py
==========
Manages context window truncation and summary injection.
"""

from typing import List, Dict
from backend.summarizer import summarize_messages
from backend.memory import format_memories_for_prompt

def estimate_tokens(text: str) -> int:
    """Rough token estimation (~4 characters per token)."""
    return len(text) // 4


def build_context(
    messages: List[Dict[str, str]], 
    existing_summary: str = "", 
    max_tokens: int = 3000,
    user_id: str = "default_user"
) -> Dict[str, any]:
    """
    Builds context window. If messages exceed max_tokens:
    1. Splits history into 'old' (to summarize) and 'recent' (to keep raw).
    2. Generates an updated summary.
    3. Assembles final payload: System Prompt + Summary + Recent Messages.
    """
    system_msg = next((m for m in messages if m["role"] == "system"), None)
    chat_messages = [m for m in messages if m["role"] != "system"]

    # Calculate current total tokens
    total_tokens = sum(estimate_tokens(m["content"]) for m in messages)
    if existing_summary:
        total_tokens += estimate_tokens(existing_summary)

    # If within limits, return original context
    if total_tokens <= max_tokens or len(chat_messages) <= 4:
        final_history = messages[:]
        if existing_summary and system_msg:
            # Inject existing summary right after system message
            summary_msg = {
                "role": "system", 
                "content": f"[Previous Conversation Summary]: {existing_summary}"
            }
            final_history.insert(1, summary_msg)
        return {
            "messages": final_history, 
            "summary": existing_summary, 
            "summarized_new_chunks": False
        }

    # Context threshold exceeded: Split history
    # Keep last 4 messages raw, summarize everything older
    recent_messages = chat_messages[-4:]
    old_messages = chat_messages[:-4]

    # Include existing summary in new summarization batch if present
    if existing_summary:
        old_messages.insert(0, {
            "role": "user", 
            "content": f"Prior Context Summary: {existing_summary}"
        })

    new_summary = summarize_messages(old_messages)

    # Construct active context payload
    final_messages = []
    if system_msg:
        final_messages.append(system_msg)

    if new_summary:
        final_messages.append({
            "role": "system", 
            "content": f"[Conversation Summary]: {new_summary}"
        })

    final_messages.extend(recent_messages)

    return {
        "messages": final_messages,
        "summary": new_summary,
        "summarized_new_chunks": True
    }