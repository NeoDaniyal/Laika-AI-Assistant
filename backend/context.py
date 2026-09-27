"""
context.py
==========
Manages context window truncation, session summarization, and query-relevant long-term memory retrieval.
"""

from typing import List, Dict
from backend.summarizer import summarize_messages
from backend.memory import format_relevant_memories_for_prompt


def estimate_tokens(text: str) -> int:
    return len(text) // 4


async def build_context(
    messages: List[Dict[str, str]], 
    existing_summary: str = "", 
    max_tokens: int = 3000,
    user_id: str = "default_user"
) -> Dict[str, any]:

    system_msg = next((m for m in messages if m["role"] == "system"), None)
    chat_messages = [m for m in messages if m["role"] != "system"]

    # Extract last user prompt to drive memory retrieval
    last_user_prompt = ""
    for msg in reversed(chat_messages):
        if msg["role"] == "user":
            last_user_prompt = msg["content"]
            break

    # Selectively retrieve relevant memories based on query
    memory_block = await format_relevant_memories_for_prompt(
        user_query=last_user_prompt, 
        user_id=user_id
    )

    final_messages = []
    if system_msg:
        final_messages.append(system_msg)

    # 1. Inject Relevant Memories
    if memory_block:
        final_messages.append({"role": "system", "content": memory_block})

    # 2. Inject Active Session Summary
    if existing_summary:
        final_messages.append({"role": "system", "content": f"[Active Session Summary]: {existing_summary}"})

    total_tokens = sum(estimate_tokens(m["content"]) for m in final_messages) + sum(estimate_tokens(m["content"]) for m in chat_messages)

    if total_tokens <= max_tokens or len(chat_messages) <= 4:
        final_messages.extend(chat_messages)
        return {
            "messages": final_messages,
            "summary": existing_summary,
            "summarized_new_chunks": False
        }

    # Context threshold exceeded: Split and summarize older turns
    recent_messages = chat_messages[-4:]
    old_messages = chat_messages[:-4]

    if existing_summary:
        old_messages.insert(0, {"role": "user", "content": f"Prior Context Summary: {existing_summary}"})

    new_summary = summarize_messages(old_messages)

    if new_summary:
        final_messages.append({"role": "system", "content": f"[Active Session Summary]: new_summary"})

    final_messages.extend(recent_messages)

    return {
        "messages": final_messages,
        "summary": new_summary,
        "summarized_new_chunks": True
    }