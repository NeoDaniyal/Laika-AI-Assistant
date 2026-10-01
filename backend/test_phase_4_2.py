"""
test_phase_4_2.py
==================
Test harness for Phase 4.2: Context Assembly with RAG Injection via build_context().
"""

import asyncio
import os
from backend.rag import ingest_document, chunks_collection, document_collection
from backend.context import build_context


async def test_rag_context_assembly():
    print("=" * 65)
    print("RUNNING PHASE 4.2: RAG CONTEXT INJECTION TEST")
    print("=" * 65)

    test_user_id = "test_phase_4_2_user"

    # 1. Clean previous database state for test user
    await document_collection.delete_many({"user_id": test_user_id})
    await chunks_collection.delete_many({"user_id": test_user_id})

    # 2. Setup mock document file and ingest into MongoDB
    sample_path = "backend/sample_phase_4_2_doc.txt"
    sample_content = (
        "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.8+ based on standard Python type hints. "
        "The key features are: Fast to code, Fewer bugs, Intuitive, Easy, Short, Robust, and Standards-based. "
        "FastAPI relies on Pydantic for data validation and Starlette for tooling. "
        "Concurrency and async/await are fully supported out of the box."
    ) * 15

    with open(sample_path, "w", encoding="utf-8") as f:
        f.write(sample_content)

    print("1. Ingesting test document into MongoDB...")
    await ingest_document(
        file_path=sample_path,
        filename="fastapi_guide.txt",
        file_type="txt",
        user_id=test_user_id
    )
    print("   Ingestion complete.\n")

    # 3. Simulate chat conversation payload
    messages_payload = [
        {"role": "system", "content": "You are Laika, a helpful AI assistant."},
        {"role": "user", "content": "What framework are we using?"},
        {"role": "assistant", "content": "We are using FastAPI for our backend."},
        {"role": "user", "content": "How does FastAPI perform data validation?"}
    ]

    print("2. Assembling context via build_context()...")
    context_result = await build_context(
        messages=messages_payload,
        existing_summary="User is asking technical questions about FastAPI.",
        user_id=test_user_id,
        enable_rag=True
    )

    assembled_messages = context_result["messages"]
    retrieved_chunks = context_result["retrieved_chunks"]

    # 4. Display Assembled Context Output
    print("\n[ASSEMBLED LLM CONTEXT MESSAGES]\n")
    for idx, msg in enumerate(assembled_messages, 1):
        role_label = msg["role"].upper()
        content_preview = msg["content"]
        print(f"Message {idx} | Role: [{role_label}]")
        print(f"{content_preview}\n" + "-" * 60)

    # Clean up local mock file
    if os.path.exists(sample_path):
        os.remove(sample_path)

    # 5. Assertions
    assert len(retrieved_chunks) > 0, "Failed: No RAG chunks retrieved."
    assert any("[START RETRIEVED KNOWLEDGE]" in m["content"] for m in assembled_messages), \
        "Failed: RAG context missing from assembled system messages."
    assert assembled_messages[-1]["content"] == "How does FastAPI perform data validation?", \
        "Failed: Last message is not the active user prompt."

    print("Retrieved Chunks Count:", len(retrieved_chunks))
    print("Assembled System Messages Count:", sum(1 for m in assembled_messages if m["role"] == "system"))
    print("\n✅ PHASE 4.2 TEST PASSED")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(test_rag_context_assembly())