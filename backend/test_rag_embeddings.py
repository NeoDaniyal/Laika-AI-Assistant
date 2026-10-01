"""
test_rag_embeddings.py
======================
Test harness for varifying Phase 2.2: Chunk vector embeding storage in MongoDB.
"""

import asyncio
import os
from backend.rag import ingest_document, chunks_collection, document_collection


async def test_chunk_embedding():
    print("="*60)
    print("RUNNING RAG PHASE 2.2: CHUNK EMBEDDING TEST")
    print("="*60)

    test_user_id = "test_rag_phase_2_user"

    await document_collection.delete_many({"user_id": test_user_id})
    await chunks_collection.delete_many({"user_id": test_user_id})

    sample_path = "backend/sample_fastapi_doc.txt"
    sample_content = (
        "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.8+ based on standard Python type hints. "
        "The key features are: Fast to code, Fewer bugs, Intuitive, Easy, Short, Robust, and Standards-based. "
        "FastAPI relies on Pydantic for data validation and Starlette for tooling. "
        "Concurrency and async/await are fully supported out of the box."
    ) * 15

    with open(sample_path, "w", encoding="utf-8") as f:
        f.write(sample_content)

    print(f"\nIngesting document and generating embeddings...")
    result = await ingest_document(
        file_path=sample_path,
        filename="fastapi_guide.txt",
        file_type="txt",
        user_id=test_user_id
    )

    print(f"Document Saved ID: {result['document_id']}")
    print(f"Found {result['total_chunks']} chunks\n")

    # 2. Retrieve chunks from MongoDB and verify embedding storage
    stored_chunks = await chunks_collection.find({"user_id": test_user_id}).to_list(length=100)

    assert len(stored_chunks) > 0, "Failed: No chunks stored in MongoDB."

    for chunk in stored_chunks:
        c_idx = chunk["chunk_index"]
        print(f"Embedding Chunk {c_idx}...")
        
        vector = chunk.get("embedding")
        assert vector is not None, f"Failed: Chunk {c_idx} missing embedding."
        assert isinstance(vector, list), f"Failed: Embedding in Chunk {c_idx} is not a list."
        assert len(vector) == 384, f"Failed: Expected 384 dimensions, got {len(vector)}."

    print("\nAll embeddings generated and persisted successfully!\n")

    for chunk in stored_chunks:
        vector = chunk["embedding"]
        print(f"Chunk {chunk['chunk_index']} → {len(vector)} dimensions | First 3 values: {[round(x, 4) for x in vector[:3]]}")

    # Cleanup local sample file
    if os.path.exists(sample_path):
        os.remove(sample_path)

    print("\n✅ RAG EMBEDDING STORAGE TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_chunk_embedding())