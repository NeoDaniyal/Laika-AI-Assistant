"""
test_phase_4_3.py
==================
Test harness for Phase 4.3: End-to-End RAG + LLM Answering Verification.
"""

import asyncio
import os
from backend.rag import ingest_document, chunks_collection, document_collection
from backend.context import build_context
from backend.llm import ask_llm_stream


async def run_rag_query(query: str, user_id: str, test_title: str):
    print(f"\n" + "=" * 65)
    print(f"[{test_title}]")
    print(f"QUERY: \"{query}\"")
    print("=" * 65)

    messages_payload = [
        {"role": "system", "content": "You are Laika, a helpful AI assistant. Answer user questions accurately based on provided knowledge."},
        {"role": "user", "content": query}
    ]

    # 1. Retrieve & Assemble Context via build_context
    context_result = await build_context(
        messages=messages_payload,
        user_id=user_id,
        enable_rag=True
    )

    assembled_messages = context_result["messages"]
    retrieved_chunks = context_result["retrieved_chunks"]

    print(f"Retrieved {len(retrieved_chunks)} relevant chunk(s).\n")
    print("Generating answer from LLM...\n" + "-" * 65 + "\nLAIKA: ")

    # 2. Stream Response from LLM
    full_response = ""
    for token in ask_llm_stream(assembled_messages):
        full_response += token
        print(token, end="", flush=True)

    print("\n" + "-" * 65)
    return full_response, retrieved_chunks


async def test_phase_4_3():
    print("=" * 65)
    print("RUNNING PHASE 4.3: RAG + LLM ANSWER VERIFICATION")
    print("=" * 65)

    test_user_id = "test_phase_4_3_user"

    # 1. Clean previous state
    await document_collection.delete_many({"user_id": test_user_id})
    await chunks_collection.delete_many({"user_id": test_user_id})

    # 2. Ingest Sample FastAPI Document
    sample_path = "backend/sample_phase_4_3_doc.txt"
    sample_content = (
        "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.8+ based on standard Python type hints. "
        "The key features are: Fast to code, Fewer bugs, Intuitive, Easy, Short, Robust, and Standards-based. "
        "FastAPI relies on Pydantic for data validation and Starlette for tooling. "
        "Concurrency and async/await are fully supported out of the box."
    ) * 10

    with open(sample_path, "w", encoding="utf-8") as f:
        f.write(sample_content)

    print("Ingesting test document into MongoDB...")
    await ingest_document(
        file_path=sample_path,
        filename="fastapi_guide.txt",
        file_type="txt",
        user_id=test_user_id
    )
    print("Ingestion complete.\n")

    # ------------------------------------------------------------------
    # TEST A: Question Answerable by Document
    # ------------------------------------------------------------------
    query_a = "How does FastAPI perform data validation?"
    response_a, chunks_a = await run_rag_query(query_a, test_user_id, "TEST A: Answerable Question")

    # Assertions for Test A
    assert len(chunks_a) > 0, "Test A Failed: No chunks retrieved."
    assert "pydantic" in response_a.lower(), "Test A Failed: LLM answer did not mention Pydantic from document."

    # ------------------------------------------------------------------
    # TEST B: Question NOT Answerable by Document
    # ------------------------------------------------------------------
    query_b = "What internal database engine does FastAPI use?"
    response_b, chunks_b = await run_rag_query(query_b, test_user_id, "TEST B: Unanswerable Question")

    # Clean up local file
    if os.path.exists(sample_path):
        os.remove(sample_path)

    print("\n" + "=" * 65)
    print("✅ PHASE 4.3 TEST PASSED")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(test_phase_4_3())