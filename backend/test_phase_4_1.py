"""
test_phase_4_1.py
==================
Test harness for Phase 4.1: Context Formatting for LLM Injection.
"""

import asyncio
from backend.vector_search import build_retrieval_context


def test_context_building():
    print("=" * 65)
    print("RUNNING PHASE 4.1: BUILD RETRIEVAL CONTEXT")
    print("=" * 65)

    # Mock Top-K retrieved chunks from Phase 3.3
    mock_chunks = [
        {
            "chunk_id": "650f1a2b3c4d5e6f7a8b9c0d",
            "chunk_index": 2,
            "filename": "fastapi_guide.txt",
            "text": "FastAPI relies on Pydantic for data validation and Starlette for tooling. Data validation is automatic via standard Python type hints.",
            "score": 0.8912
        },
        {
            "chunk_id": "650f1a2b3c4d5e6f7a8b9c0e",
            "chunk_index": 0,
            "filename": "fastapi_guide.txt",
            "text": "FastAPI is a modern, high-performance web framework for building APIs with Python 3.8+.",
            "score": 0.7450
        }
    ]

    print("\n--- Test 1: Standard Retrieval Input ---")
    context_str = build_retrieval_context(mock_chunks)
    print(context_str)

    print("\n--- Test 2: Empty Retrieval Edge Case ---")
    empty_context = build_retrieval_context([])
    print(empty_context)

    # Validations
    assert "[START RETRIEVED KNOWLEDGE]" in context_str
    assert "FastAPI relies on Pydantic" in context_str
    assert "Source: fastapi_guide.txt" in context_str
    assert empty_context == "No relevant background information found."

    print("\n" + "=" * 65)
    print("✅ PHASE 4.1 TEST PASSED")
    print("=" * 65)


if __name__ == "__main__":
    test_context_building()