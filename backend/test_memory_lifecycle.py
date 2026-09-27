"""
test_memory_lifecycle.py
========================
Tests memory updates (Python -> Rust), deduplication, and selective retrieval.
"""

import asyncio
from backend.context import build_context
from backend.memory import (
    extract_and_store_memories,
    memories_collection,
)


async def test_lifecycle():
    print("=" * 60)
    print("RUNNING MEMORY LIFECYCLE & RETRIEVAL TEST")
    print("=" * 60)

    test_user_id = "test_user_lifecycle"
    await memories_collection.delete_many({"user_id": test_user_id})

    # 1. Initial State: User prefers Python and works in Pune
    print("\n--- 1. Initial Memory Extraction ---")
    await extract_and_store_memories(
        user_message="My favorite language is Python and I build apps in Pune.",
        assistant_response="Got it! Python in Pune.",
        user_id=test_user_id
    )

    # 2. Conflict/Update State: User switches to Rust
    print("\n--- 2. Update Memory (Python -> Rust) ---")
    await extract_and_store_memories(
        user_message="Actually, I recently switched to Rust and it is now my favorite language.",
        assistant_response="Rust is a powerful language!",
        user_id=test_user_id
    )

    # Verify MongoDB record update (No duplicates)
    docs = await memories_collection.find({"user_id": test_user_id}).to_list(length=10)
    print(f"\n[MongoDB Memory Count]: {len(docs)} (Expected: Deduplicated records)")
    for d in docs:
        print(f"  • {d['key']}: {d['value']}")

    # Assert no duplicate keys exist
    keys = [d['key'] for d in docs]
    assert len(keys) == len(set(keys)), "Failed: Duplicate keys detected!"

    # 3. Test Selective Retrieval on Language Query
    print("\n--- 3. Testing Selective Retrieval for Language Query ---")
    messages = [
        {"role": "system", "content": "You are Laika Assistant."},
        {"role": "user", "content": "What programming language do I prefer?"}
    ]

    context = await build_context(messages=messages, user_id=test_user_id)
    payload = context["messages"]

    memory_msg = next((m["content"] for m in payload if "Relevant User Memory" in m.get("content", "")), "")
    print(f"\n[Injected Memory for Language Query]:\n{memory_msg}")

    assert "Rust" in memory_msg, "Failed: Updated language 'Rust' missing."
    assert "Python" not in memory_msg, "Failed: Stale language 'Python' still present."

    print("\n✅ LIFECYCLE TEST PASSED: Conflict resolution, deduplication, and selective retrieval verified!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_lifecycle())