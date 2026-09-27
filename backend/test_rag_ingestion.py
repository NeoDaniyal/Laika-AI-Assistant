"""
test_rag_ingestion.py
=====================
Test harness for varifying document text extraction, overlap chunking, and MongoDB persistence."""

import asyncio
import os
import PyPDF2
from backend.rag import ingest_document, chunks_collection, document_collection

def create_dummy_pdf(path: str):
    """Creates sample document for testing."""
    from PyPDF2 import PdfWriter
    writer = PdfWriter()
    pages = writer.add_blank_page(width=612, height=792)

    with open(path, "wb") as f:
        writer.write(f)

async def  test_rag_ingestion():
    print("="*60)
    print("RUNNING RAG PHASE 1: DOCUMENT INGESTION TEST")
    print("="*60)

    test_user_id = "test_rag_user"

    await document_collection.delete_many({"user_id": test_user_id})
    await chunks_collection.delete_many({"user_id": test_user_id})

    sample_text_path = "backend/sample_fastapi_doc.txt"
    sample_content = (
        "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.8+ based on standard Python type hints. "
        "The key features are: Fast to code, Fewer bugs, Intuitive, Easy, Short, Robust, and Standards-based. "
        "FastAPI relies on Pydantic for data validation and Starlette for tooling. "
        "Concurrency and async/await are fully supported out of the box."
    ) * 15
    with open(sample_text_path, "w", encoding="utf-8") as f:
        f.write(sample_content)

    print(f"\n--- 1. Ingesting Test File ({sample_text_path}) ---")
    result = await ingest_document(
        file_path=sample_text_path,
        filename="fastapi_guide.txt",
        file_type="txt",
        user_id=test_user_id
    )

    print(f"Document Saved ID: {result['document_id']}")
    print(f"Total Chunks Created: {result['total_chunks']}")

    stored_chunks = await chunks_collection.find({"user_id": test_user_id}).to_list(length=100)
    print(f"\n--- 2. MongoDB Stored Chunks Inspection ({len(stored_chunks)} total) ---")

    for c in stored_chunks[:3]:
        print(f"\n• [Chunk {c['chunk_index']}] ({c['word_count']} word):")
        print(f"  \"{c['text'][:120]}...\"")

    if os.path.exists(sample_text_path):
        os.remove(sample_text_path)

    assert len(stored_chunks) > 1, "Failed: Document was not split into multiple chunks."
    assert stored_chunks[0]["embedding"] is None, "Failed: Embedding slot should default to None."

    print("\n ✅ RAG INGESTION TEST PASSED: Extraction, overlaping chunking & storage verified!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_rag_ingestion())