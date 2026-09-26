"""
test_memory.py
==============
Test harness for verifying Long-Term Memory extraction and cross-session retrieval using asyncio.
"""

import asyncio
from backend.context import build_context
from backend.memory import (
    extract_and_store_memories,
    memories_collection,
)


async def test_memory_pipeline():
    print("=" * 60)
    print("RUNNING LONG-TERM MEMORY PIPELINE TEST")
    print("=" * 60)

    test_user_id = "test_user_daniyal"
    
    # 1. Clean up previous test entries
    await memories_collection.delete_many({"user_id": test_user_id})

    # --- PHASE 1: Memory Extraction ---
    print("\n--- Phase 1: Extracting Memory from User Exchange ---")
    sample_user_msg = "My favorite programming language is Python and I am building an app named Laika in Pune."
    sample_ai_msg = "That sounds like an exciting project, Daniyal! Python is great for AI development."

    print(f"[Input User Msg]: '{sample_user_msg}'")
    
    # Run async memory extraction
    await extract_and_store_memories(
        user_message=sample_user_msg,
        assistant_response=sample_ai_msg,
        user_id=test_user_id
    )

    # Fetch MongoDB entries using async cursor
    cursor = memories_collection.find({"user_id": test_user_id})
    saved_docs = await cursor.to_list(length=100)

    print(f"\n[Extracted Memories in MongoDB]: {len(saved_docs)} records found")
    for doc in saved_docs:
        print(f"  • Key: {doc['key']:<30} | Value: {doc['value']}")

    assert len(saved_docs) > 0, "Failed: No memories were extracted and stored."

    # --- PHASE 2: Cross-Session Context Injection ---
    print("\n--- Phase 2: Simulating BRAND NEW Chat Session ---")
    
    fresh_chat_messages = [
        {"role": "system", "content": "You are Laika Assistant, created by Daniyal."},
        {"role": "user", "content": "What programming language do I prefer and what app am I building?"}
    ]

    context_output = await build_context(
        messages=fresh_chat_messages,
        existing_summary="",
        max_tokens=3000,
        user_id=test_user_id
    )

    payload = context_output["messages"]

    print("\n[Final Context Window Payload Passed to LLM]:")
    for idx, msg in enumerate(payload):
        role_label = f"[{msg['role'].upper()}]"
        preview = msg['content'].replace("\n", " ")
        print(f"  {idx + 1}. {role_label:<12} {preview}")

    # --- PHASE 3: Assertions ---
    memory_system_msg = next((m for m in payload if "User Long-Term Memory" in m.get("content", "")), None)
    
    assert memory_system_msg is not None, "Failed: Memory block was not injected into system prompt."
    assert "Python" in memory_system_msg["content"], "Failed: 'Python' preference missing from injected memory."
    assert "Laika" in memory_system_msg["content"], "Failed: 'Laika' project missing from injected memory."

    print("\n✅ TEST PASSED: Long-Term Memory extraction & cross-session injection fully functional!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_memory_pipeline())