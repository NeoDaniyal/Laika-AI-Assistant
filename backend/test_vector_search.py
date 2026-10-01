"""
test_vector_search.py
=====================
Test harness for Phase 3.1: Cosine Similarity Verification.
"""

from backend.embeddings import generate_embedding
from backend.vector_search import cosine_similarity

def test_local_cosine_similarity():
    print("="*60)
    print("RUNNNING RAG PHASE 3.1: LOCAL COSINE SIMILARY TEST")
    print("="*60)

    documents = [
        {"id": 1, "text": "FastAPI uses Pydantic for data validation."},
        {"id": 2, "text": "Python is a high-level general-purpose programming language."},
        {"id": 3, "text": "FastAPI is a fast web framework for building REST APIs in Python."}
    ]

    query = "How does FastAPI validate incoming data?"

    print(f"\nQUERY: \"{query}\"\n")
    print("Generating embeddings...")

    query_embedding = generate_embedding(query)

    results = []
    for doc in documents:
        doc_embedding = generate_embedding(doc["text"])
        score = cosine_similarity(query_embedding, doc_embedding)
        results.append({
            "id": doc["id"],
            "text": doc["text"],
            "score": score
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    print("-"*65)
    print("RANKED SEARCH RESULTS (Higest Similary First)")
    print("-"*65)

    for rank, res in enumerate(results, 1):
        print(f"Rank {rank}| Score: {res['score']:.4f}")
        print(f"           Text: \"{res['text']}\"\n")

    top_result = results[0]
    unrelated_result = [r for r in results if r["id"] == 2][0]

    assert top_result["id"] == 1,(
        f"Expected Document 1 (Pydantic validation) to be the top rank, got Document {top_result["id"]} instead."
    )
    assert top_result["score"] > unrelated_result["score"],(
        f"Validation doc score ({top_result['score']:.4f}) should be higher than unrelated doc score ({unrelated_result['score']:.4f})"
    )

    print("="*60)
    print("✅ RAG PHASE 3.1 TEST PASSED: Validation text scored highest!")
    print("="*60)

if __name__ == "__main__":
    test_local_cosine_similarity()