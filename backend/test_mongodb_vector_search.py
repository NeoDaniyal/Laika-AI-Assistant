"""
test_mongodb_vector_search.py
==============================
Test harness for Phase 3.2: Semantic Vector Search over MongoDB Chunks.
"""

import asyncio
from backend.embeddings import generate_embedding
from backend.vector_search import cosine_similarity
from backend.rag import chunks_collection, document_collection, ingest_document


async def test_mongodb_vector_search():
    print("=" * 65)
    print("RUNNING RAG PHASE 3.2: MONGODB VECTOR SEARCH")
    print("=" * 65)

    test_user_id = "test_rag_search_user"
    
    # 1. Prepare clean test collection
    await document_collection.delete_many({"user_id": test_user_id})
    await chunks_collection.delete_many({"user_id": test_user_id})

    # 2. Ingest test sample document
    sample_path = "backend/sample_fastapi_doc.txt"
    sample_content = (
        "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.8+ based on standard Python type hints. "
        "The key features are: Fast to code, Fewer bugs, Intuitive, Easy, Short, Robust, and Standards-based. "
        "FastAPI relies on Pydantic for data validation and Starlette for tooling. "
        "Concurrency and async/await are fully supported out of the box."
    ) * 15

    with open(sample_path, "w", encoding="utf-8") as f:
        f.write(sample_content)

    print("Ingesting sample document into MongoDB...")
    await ingest_document(
        file_path=sample_path,
        filename="fastapi_guide.txt",
        file_type="txt",
        user_id=test_user_id
    )

    # 3. Formulate Query
    query = "How does FastAPI perform data validation?"
    print(f"\nQUERY: \"{query}\"\n")

    # Generate Query Embedding
    print("Generating query vector...")
    query_vector = generate_embedding(query)

    # 4. Fetch stored chunks from MongoDB
    stored_chunks = await chunks_collection.find({"user_id": test_user_id}).to_list(length=100)
    print(f"Searching {len(stored_chunks)} stored chunks in MongoDB...\n")

    # 5. Compute Cosine Similarity for every stored chunk
    search_results = []
    for chunk in stored_chunks:
        chunk_vector = chunk.get("embedding")
        if chunk_vector:
            score = cosine_similarity(query_vector, chunk_vector)
            search_results.append({
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
                "score": score
            })

    # 6. Sort results descending by score
    search_results.sort(key=lambda x: x["score"], reverse=True)

    # Print Ranked Results
    print("-" * 65)
    for rank, res in enumerate(search_results, 1):
        print(f"Rank {rank} | Score: {res['score']:.4f} | Chunk {res['chunk_index']}")
        preview_text = res['text'][:120].replace('\n', ' ')
        print(f"Text: \"{preview_text}...\"\n")
    print("-" * 65)

    # Assertions
    assert len(search_results) > 0, "Failed: Search results are empty."
    assert search_results[0]["score"] > 0.3, f"Failed: Top score ({search_results[0]['score']}) is too low."

    print("\n✅ MONGODB VECTOR SEARCH TEST PASSED")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(test_mongodb_vector_search())