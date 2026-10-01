"""
test_phase_4_4.py
==================
Test harness for Phase 4.4: Relevance Thresholding & Strict Rejection Verification.
"""

import asyncio
import os
from backend.rag import ingest_document, chunks_collection, document_collection
from backend.context import build_context
from backend.llm import ask_llm_stream


async def test_phase_4_4():
    print("=" * 65)
    print("RUNNING PHASE 4.4: RELEVANCE THRESHOLD & GROUNDEDNESS VERIFICATION")
    print("=" * 65)

    test_user_id = "test_phase_4_4_user"

    await document_collection.delete_many({"user_id": test_user_id})
    await chunks_collection.delete_many({"user_id": test_user_id})

    # Sample Document about FastAPI
    sample_path = "backend/sample_phase_4_4_doc.txt"
    sample_content = (
        "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.8+ based on standard Python type hints. "
        "FastAPI relies on Pydantic for data validation and Starlette for tooling."
    ) * 10

    with open(sample_path, "w", encoding="utf-8") as f:
        f.write(sample_content)

    print("Ingesting test document...")
    await ingest_document(
        file_path=sample_path,
        filename="fastapi_guide.txt",
        file_type="txt",
        user_id=test_user_id
    )
    print("Ingestion complete.\n")

    # ------------------------------------------------------------------
    # TEST 1: Irrelevant Query (Should yield 0 chunks after thresholding)
    # ------------------------------------------------------------------
    irrelevant_query = "What is the capital of France and what is its climate like?"
    print(f"QUERY: \"{irrelevant_query}\"")

    messages_payload = [
        {"role": "system", "content": "You are Laika, a helpful AI assistant."},
        {"role": "user", "content": irrelevant_query}
    ]

    context_result = await build_context(
        messages=messages_payload,
        user_id=test_user_id,
        score_threshold=0.45,
        enable_rag=True
    )

    retrieved_chunks = context_result["retrieved_chunks"]
    assembled_messages = context_result["messages"]

    print(f"Retrieved Chunks (Score >= 0.45): {len(retrieved_chunks)}")
    assert len(retrieved_chunks) == 0, "Failed: Low-relevance chunks were not filtered out."

    print("\nGenerating LLM Response...\n" + "-" * 65 + "\nLAIKA: ")
    full_response = ""
    try:
        for token in ask_llm_stream(assembled_messages):
            full_response += token
            print(token, end="", flush=True)
    except TypeError:
        for token in ask_llm_stream(assembled_messages):
            full_response += token
            print(token, end="", flush=True)

    print("\n" + "-" * 65)

    if os.path.exists(sample_path):
        os.remove(sample_path)

    print("\n" + "=" * 65)
    print("✅ PHASE 4.4 TEST PASSED")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(test_phase_4_4())