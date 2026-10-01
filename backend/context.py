"""
context.py
==========
Manages context window truncation, session summarization, query-relevant long-term memory retrieval,
and RAG document context injection.
"""

from typing import List, Dict, Any, Optional
from backend.summarizer import summarize_messages
from backend.memory import format_relevant_memories_for_prompt
from backend.vector_search import search_similar_chunks, build_retrieval_context


def estimate_tokens(text: str) -> int:
    return len(text) // 4


async def build_context(
    messages: List[Dict[str, str]], 
    existing_summary: str = "", 
    max_tokens: int = 3000,
    user_id: str = "default_user",
    retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
    score_threshold: float = 0.45,
    enable_rag: bool = True
) -> Dict[str, Any]:

    system_msg = next((m for m in messages if m["role"] == "system"), None)
    chat_messages = [m for m in messages if m["role"] != "system"]

    # Extract last user prompt to drive memory retrieval and RAG search
    last_user_prompt = ""
    for msg in reversed(chat_messages):
        if msg["role"] == "user":
            last_user_prompt = msg["content"]
            break

    # 1. Selectively retrieve relevant memories based on query
    memory_block = await format_relevant_memories_for_prompt(
        user_query=last_user_prompt, 
        user_id=user_id
    )

    # 2. Retrieve Top-K RAG chunks if enabled and not directly provided
    if enable_rag and retrieved_chunks is None and last_user_prompt:
        retrieved_chunks = await search_similar_chunks(
            query=last_user_prompt,
            top_k=2,
            user_id=user_id,
            score_threshold=score_threshold
        )

    final_messages = []
    if system_msg:
        final_messages.append(system_msg)

    # Inject Relevant Long-Term Memories
    if memory_block:
        final_messages.append({"role": "system", "content": memory_block})

    # Inject Active Session Summary
    if existing_summary:
        final_messages.append({"role": "system", "content": f"[Active Session Summary]: {existing_summary}"})

    # Inject RAG Document Knowledge
    if enable_rag and last_user_prompt:
        rag_context = build_retrieval_context(retrieved_chunks or [])
        final_messages.append({
            "role": "system", 
            "content": (
                "RAG KNOWLEDGE INSTRUCTION:\n"
                "When answering using retrieved documentation, prioritize the retrieved information.\n"
                "Do not invent facts or sources.\n"
                "If relevant documentation was retrieved, mention the source filename when relying on that information.\n"
                "If '[NO RELEVANT DOCUMENTATION FOUND]' is present, do not pretend that the retrieved documents contain an answer.\n\n"
                f"{rag_context}"
            )
        })

    # Token counting & window management
    total_tokens = sum(estimate_tokens(m["content"]) for m in final_messages) + sum(estimate_tokens(m["content"]) for m in chat_messages)

    if total_tokens <= max_tokens or len(chat_messages) <= 4:
        final_messages.extend(chat_messages)
        return {
            "messages": final_messages,
            "summary": existing_summary,
            "summarized_new_chunks": False,
            "retrieved_chunks": retrieved_chunks or []
        }

    # Context threshold exceeded: Split and summarize older turns
    recent_messages = chat_messages[-4:]
    old_messages = chat_messages[:-4]

    if existing_summary:
        old_messages.insert(0, {"role": "user", "content": f"Prior Context Summary: {existing_summary}"})

    new_summary = summarize_messages(old_messages)

    if new_summary:
        final_messages.append({"role": "system", "content": f"[Active Session Summary]: {new_summary}"})

    final_messages.extend(recent_messages)

    return {
        "messages": final_messages,
        "summary": new_summary,
        "summarized_new_chunks": True,
        "retrieved_chunks": retrieved_chunks or []
    }