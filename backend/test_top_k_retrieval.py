"""
test_top_k_retrieval.py
=======================
Test harness for Phase 3.3: Top-K Vector Search Verification.
"""
import asyncio
import os
from backend.rag import ingest_document, chunks_collection, document_collection
from backend.vector_search import search_similar_chunks

async def test_top_k_retrieval():
    print("="*60)
    print("RUNNING PHASE 3.3: TOP-K RETRIEVAL")
    print("="*60)

    test_user_id = "test_top_k_user"

    await document_collection.delete_many({"user_id": test_user_id})
    await chunks_collection.delete_many({"user_id": test_user_id})

    sample_path = "backend/sample_top_k_doc.txt"
    sample_content = (
        "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.8+ based on standard Python type hints. "
        "The key features are: Fast to code, Fewer bugs, Intuitive, Easy, Short, Robust, and Standards-based. "
        "FastAPI relies on Pydantic for data validation and Starlette for tooling. "
        "Concurrency and async/await are fully supported out of the box."
    ) * 15

    with open(sample_path, "w", encoding="utf-8") as f:
        f.write(sample_content)

    print("Ingesting test document...")
    ingest_meta = await ingest_document(file_path=sample_path, filename="fastapi_guide.txt", file_type="txt", user_id=test_user_id)

    total_chunks = ingest_meta["total_chunks"]
    print(f"Ingestion complete. Total chunks created: {total_chunks}\n")

    query = "How does FastAPI  perform data validation?"
    requested_k = 2

    print(f"QUERY:\n\"{query}\"\n")
    print(f"Requested Top-K: {requested_k}\n")

    results = await search_similar_chunks(query=query, top_k=requested_k, user_id=test_user_id)

    print("-"*60)
    for rank, item in enumerate(results, 1):
        preview = item["text"][:120].replace("\n", " ")
        print(f"Rank {rank}| Score: {item['score']:.4f} | Chunk {item['chunk_index']}")
        print(f"Text: \"{preview}...\"\n")
    print("-"*60)

    print(f"Retrieved: {len(results)} chunks")
    print(f"Expected: {requested_k} chunks\n")

    assert len(results) == requested_k, f"Failed: Expected {requested_k} chunks, got {len(results)}."
    assert results[0]["score"] >= results[1]["score"], "Failed: Results are not sorted in descending order."

    if os.path.exists(sample_path):
        os.remove(sample_path)

    print("✅ TOP-K RETRIEVAL TEST PASSED")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(test_top_k_retrieval())