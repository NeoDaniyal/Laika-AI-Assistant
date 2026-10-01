"""
test_embeddings.py
==================
Test harness for verifying Phase 2.1 vector embedding generation. 
"""

from backend.embeddings import generate_embedding

def test_embedding_generation():
    print("="*60)
    print("RUNNING RAG PHASE 2: EMBEDDING TEST")
    print("="*60)

    sample_text = "FastAPI is a modern, fast web framework for buiding APIs with python."
    print(f"\n[Sample Text]: \"{sample_text}\"")

    embedding = generate_embedding(sample_text)

    # Verify vector output
    print(f"\nEmbedding generated successfully!")
    print(f"Type: {type(embedding)}")
    print(f"Dimensions: {len(embedding)}")
    print(f"First 5 values: {[round(x, 4) for x in embedding[:5]]}")

    # Assertions
    assert isinstance(embedding, list), "Failed: Embedding is not a Python list."
    assert len(embedding) == 384, f"Failed: Expected 384 dimensions, got {len(embedding)}."

    print("\n✅ EMBEDDING TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_embedding_generation()