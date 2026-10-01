"""
test_phase_4_5.py
==================
Test harness for Phase 4.5: Multi-Document RAG Retrieval & Context Filtering.
"""

import asyncio
import os
from backend.rag import ingest_document, chunks_collection, document_collection
from backend.context import build_context
from backend.llm import ask_llm_stream


async def run_multi_doc_query(query: str, user_id: str, test_title: str):
    print(f"\n" + "=" * 65)
    print(f"[{test_title}]")
    print(f"QUERY: \"{query}\"")
    print("=" * 65)

    messages_payload = [
        {"role": "system", "content": "You are Laika, a helpful AI assistant. Answer user questions strictly based on retrieved documents when available."},
        {"role": "user", "content": query}
    ]

    # 1. Retrieve & Assemble Context via build_context
    context_result = await build_context(
        messages=messages_payload,
        user_id=user_id,
        score_threshold=0.45,
        enable_rag=True
    )

    assembled_messages = context_result["messages"]
    retrieved_chunks = context_result["retrieved_chunks"]

    print(f"Retrieved {len(retrieved_chunks)} chunk(s) across documents:")
    for chunk in retrieved_chunks:
        print(f" - Source: {chunk.get('filename')} (Score: {chunk.get('score'):.4f})")

    print("\nGenerating answer from LLM...\n" + "-" * 65 + "\nLAIKA: ")

    # 2. Stream Response from LLM
    full_response = ""
    try:
        async for token in ask_llm_stream(assembled_messages):
            full_response += token
            print(token, end="", flush=True)
    except TypeError:
        for token in ask_llm_stream(assembled_messages):
            full_response += token
            print(token, end="", flush=True)

    print("\n" + "-" * 65)
    return full_response, retrieved_chunks


async def test_phase_4_5():
    print("=" * 65)
    print("RUNNING PHASE 4.5: MULTI-DOCUMENT RAG RETRIEVAL TEST")
    print("=" * 65)

    test_user_id = "test_phase_4_5_user"

    # 1. Clean previous database state
    await document_collection.delete_many({"user_id": test_user_id})
    await chunks_collection.delete_many({"user_id": test_user_id})

    # 2. Ingest Document A: FastAPI Guide
    doc_a_path = "backend/sample_doc_fastapi.txt"
    doc_a_content = (
        "FastAPI relies on Pydantic for data validation and Starlette for tooling. "
        "It supports async and await out of the box for lightweight concurrency."
    ) * 10

    with open(doc_a_path, "w", encoding="utf-8") as f:
        f.write(doc_a_content)

    print("Ingesting Document A (fastapi_guide.txt)...")
    await ingest_document(
        file_path=doc_a_path,
        filename="fastapi_guide.txt",
        file_type="txt",
        user_id=test_user_id
    )

    # 3. Ingest Document B: Docker Guide
    doc_b_path = "backend/sample_doc_docker.txt"
    doc_b_content = (
        "Docker allows containerization of applications. "
        "A Dockerfile uses EXPOSE 8000 to specify port mapping and CMD Gunicorn with Uvicorn workers "
        "for production deployments inside a container."
    ) * 10

    with open(doc_b_path, "w", encoding="utf-8") as f:
        f.write(doc_b_content)

    print("Ingesting Document B (docker_guide.txt)...")
    await ingest_document(
        file_path=doc_b_path,
        filename="docker_guide.txt",
        file_type="txt",
        user_id=test_user_id
    )
    print("Ingestion complete.\n")

    # ------------------------------------------------------------------
    # TEST 1: Query specifically targeting Document A (FastAPI)
    # ------------------------------------------------------------------
    query_a = "How does FastAPI handle data validation?"
    resp_a, chunks_a = await run_multi_doc_query(query_a, test_user_id, "TEST 1: Document A Retrieval")

    # Verify retrieval comes from Document A
    assert len(chunks_a) > 0, "Test 1 Failed: No chunks retrieved."
    assert all(c["filename"] == "fastapi_guide.txt" for c in chunks_a), \
        "Test 1 Failed: Retrieved chunks contained documents other than fastapi_guide.txt."

    # ------------------------------------------------------------------
    # TEST 2: Query specifically targeting Document B (Docker)
    # ------------------------------------------------------------------
    query_b = "How should we configure the container port in Docker?"
    resp_b, chunks_b = await run_multi_doc_query(query_b, test_user_id, "TEST 2: Document B Retrieval")

    # Verify retrieval comes from Document B
    assert len(chunks_b) > 0, "Test 2 Failed: No chunks retrieved."
    assert all(c["filename"] == "docker_guide.txt" for c in chunks_b), \
        "Test 2 Failed: Retrieved chunks contained documents other than docker_guide.txt."

    # Clean up local mock files
    for path in [doc_a_path, doc_b_path]:
        if os.path.exists(path):
            os.remove(path)

    print("\n" + "=" * 65)
    print("✅ PHASE 4.5 TEST PASSED")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(test_phase_4_5())