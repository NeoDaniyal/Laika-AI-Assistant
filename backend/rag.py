"""
rag.py
=====
RAG Phase 1: Document Injection, Extraction, Cleaning, Chunking, and Storage.
"""

import re
from typing import List, Dict, Any
from datetime import datetime
import PyPDF2
import docx
from backend.database import db

document_collection = db["rag_documents"]
chunks_collection = db["rag_chunks"]

def extract_text_from_file(file_path: str, file_type: str) -> str:
    """Extract raw text context based on file extension."""
    file_type = file_type.lower()

    if file_type == "txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
            
    elif file_type == "pdf":
        text= ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text +=f"\n--- Page {page_num + 1} ---\n" + page_text
        return text
    elif file_type in ["docx", "doc"]:
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    else:
        raise ValueError(f"Unsupported File Format: {file_type}")
#Text Cleaning for better analysis
def clean_text(text: str) -> str:
    """Clean whitespace, Linebreak, and formatting noise."""

    text = re.sub(r'\r\n|\r', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def chunk_text(text: str, chunk_size: int=500, chunk_overlap: int =100) -> List[Dict[str, Any]]:
    """
    Splits text into overlaping word chunks.
    Overlap prevents losing context across split boundaries."""
    words = text.split(" ")
    chunks = []
    start = 0
    chucks_index = 0

    if len(words) <= chunk_size:
        return [{"chunk_index": 0, "text": text, "word_count": len(words)}]

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunk_str = " ".join(chunk_words)

        chunks.append({
            "chunk_index": chucks_index,
            "text": chunk_str,
            "word_count": len(chunk_words)
        })

        chucks_index += 1

        start += (chunk_size - chunk_overlap)

        if end == len(words):
            break
    return chunks

async def ingest_document(file_path: str, filename: str, file_type: str, user_id: str ="default_user")-> Dict[str, Any]:
    """Extracts, cleans, chunks, and persists a document int MongoDB."""

    raw_text = extract_text_from_file(file_path, file_type)
    cleaned = clean_text(raw_text)

    chunks = chunk_text(cleaned, chunk_size=300, chunk_overlap=50)

    doc_meta = {
        "user_id": user_id,
        "filename": filename,
        "file_type": file_type,
        "total_chunks": len(chunks),
        "total_characters": len(cleaned),
        "uploaded_at": datetime.utcnow()
    }
    doc_result = await document_collection.insert_one(doc_meta)
    doc_id = doc_result.inserted_id

    chunk_docs = []
    for c in chunks:
        chunk_docs.append({
            "document_id": doc_id,
            "user_id": user_id,
            "filename": filename,
            "chunk_index": c["chunk_index"],
            "text": c["text"],
            "word_count": c["word_count"],
            "embedding": None
        })
    if chunk_docs:
        await chunks_collection.insert_many(chunk_docs)

    return {
        "document_id": str(doc_id),
        "filename": filename,
        "total_chunks": len(chunks)
    }