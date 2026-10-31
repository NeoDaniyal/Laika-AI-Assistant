"""
context.py
==========
Manages context window truncation, session summarization, query-relevant long-term memory retrieval,
and RAG document context injection with strict user ownership isolation.
"""

from typing import List, Dict, Any, Optional
from backend.summarizer import summarize_messages
from backend.memory import format_relevant_memories_for_prompt
from backend.vector_search import search_similar_chunks, build_retrieval_context


def estimate_tokens(text: str) -> int:
    return len(text) // 4


async def build_context(
    messages: List[Dict[str, str]], 
    user_id: str,
    existing_summary: str = "", 
    max_tokens: int = 3000,
    retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
    score_threshold: float = 0.45,
    enable_rag: bool = True
) -> Dict[str, Any]:

    is_guest = (user_id == "guest_user")

    # Fail closed: never inject pre-supplied chunks without matching ownership metadata.
    if retrieved_chunks is not None:
        retrieved_chunks = [
            chunk
            for chunk in retrieved_chunks
            if chunk.get("user_id") == user_id
        ]

    system_msg = next((m for m in messages if m["role"] == "system"), None)
    chat_messages = [m for m in messages if m["role"] != "system"]

    # Extract last user prompt to drive memory retrieval and RAG search
    last_user_prompt = ""
    for msg in reversed(chat_messages):
        if msg["role"] == "user":
            last_user_prompt = msg["content"]
            break

    # 1. Selectively retrieve relevant memories based on query (Skip for guests)
    memory_block = ""
    if not is_guest:
        memory_block = await format_relevant_memories_for_prompt(
            user_query=last_user_prompt, 
            user_id=user_id
        )

    # 2. Retrieve Top-K RAG chunks if enabled and not directly provided (Skip for guests)
    document_ids = []
    if not is_guest:
        for msg in reversed(chat_messages):
            if msg.get("role") == "user":
                document_ids = msg.get("document_ids") or []
                break

        # Smart fallback: Auto-target the user's latest uploaded document for summary queries if none provided
        if not document_ids and last_user_prompt:
            is_summary_query = any(kw in last_user_prompt.lower() for kw in ["summarize", "summary", "overview", "what is this document about"])
            if is_summary_query:
                from backend.rag import document_collection
                latest_doc = await document_collection.find_one({"user_id": user_id}, sort=[("uploaded_at", -1)])
                if latest_doc:
                    document_ids = [str(latest_doc["_id"])]
                    print(f"[RAG DEBUG] Auto-targeted latest document ID: {document_ids[0]} ({latest_doc.get('filename')})")

    print(f"[RAG DEBUG] User ID: {user_id} | Is Guest: {is_guest}")
    print(f"[RAG DEBUG] Last user prompt: {last_user_prompt}")
    print(f"[RAG DEBUG] Selected document IDs: {document_ids}")

    if enable_rag and not is_guest and retrieved_chunks is None and last_user_prompt:
        is_summary_query = any(kw in last_user_prompt.lower() for kw in ["summarize", "summary", "overview", "what is this document about"])

        effective_top_k = 10 if (is_summary_query and document_ids) else 2
        effective_threshold = 0.05 if is_summary_query else score_threshold
        
        retrieved_chunks = await search_similar_chunks(
            query=last_user_prompt,
            user_id=user_id,
            top_k=effective_top_k,
            score_threshold=effective_threshold,
            document_ids=document_ids
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

    # Inject RAG Document Knowledge (Only if RAG chunks are present and user is authenticated)
    if enable_rag and not is_guest and retrieved_chunks:
        rag_context = build_retrieval_context(retrieved_chunks)
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

    new_summary = await summarize_messages(old_messages)

    if new_summary:
        final_messages.append({"role": "system", "content": f"[Active Session Summary]: {new_summary}"})

    final_messages.extend(recent_messages)

    return {
        "messages": final_messages,
        "summary": new_summary,
        "summarized_new_chunks": True,
        "retrieved_chunks": retrieved_chunks or []
    }