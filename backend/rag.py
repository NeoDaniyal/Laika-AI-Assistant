"""
rag.py
======
RAG System: Document Ingestion, Cleaning, Overlapping Chunking,
and Vector Embedding Storage.
"""

import re
from typing import List, Dict, Any
from datetime import datetime
import PyPDF2
import docx
from backend.database import db
from backend.embeddings import generate_embedding

document_collection = db["rag_documents"]
chunks_collection = db["rag_chunks"]


# ------------------------------------------------------------------
# 1. Text Extraction & Cleaning
# ------------------------------------------------------------------
def extract_text_from_file(file_path: str, file_type: str) -> str:
    file_type = file_type.lower()
    if file_type == "txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    elif file_type == "pdf":
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {page_num + 1} ---\n" + page_text
        return text

    elif file_type in ["docx", "doc"]:
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

    else:
        raise ValueError(f"Unsupported file format: {file_type}")


def clean_text(text: str) -> str:
    text = re.sub(r'\r\n|\r', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 300, chunk_overlap: int = 50) -> List[Dict[str, Any]]:
    words = text.split(" ")
    chunks = []
    start = 0
    chunk_index = 0

    if len(words) <= chunk_size:
        return [{"chunk_index": 0, "text": text, "word_count": len(words)}]

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunk_str = " ".join(chunk_words)

        chunks.append({
            "chunk_index": chunk_index,
            "text": chunk_str,
            "word_count": len(chunk_words)
        })

        chunk_index += 1
        start += (chunk_size - chunk_overlap)
        if end == len(words):
            break

    return chunks


# ------------------------------------------------------------------
# 2. Ingestion & Embedding Storage
# ------------------------------------------------------------------
async def ingest_document(file_path: str, filename: str, file_type: str, user_id: str = "default_user") -> Dict[str, Any]:
    raw_text = extract_text_from_file(file_path, file_type)
    cleaned = clean_text(raw_text)
    chunks = chunk_text(cleaned, chunk_size=300, chunk_overlap=50)

    # 1. Save Document Record
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

    # 2. Generate Vector Embeddings and Save Chunks
    chunk_docs = []
    for c in chunks:
        vector = generate_embedding(c["text"])
        
        chunk_docs.append({
            "document_id": doc_id,
            "user_id": user_id,
            "filename": filename,
            "chunk_index": c["chunk_index"],
            "text": c["text"],
            "word_count": c["word_count"],
            "embedding": vector
        })

    if chunk_docs:
        await chunks_collection.insert_many(chunk_docs)

    return {
        "document_id": str(doc_id),
        "filename": filename,
        "total_chunks": len(chunks)
    }


async def embed_existing_unembedded_chunks(user_id: str = "default_user") -> int:
    """Finds chunks with embedding: None or missing embedding and updates them."""
    cursor = chunks_collection.find({
        "user_id": user_id,
        "$or": [{"embedding": None}, {"embedding": {"$exists": False}}]
    })
    unembedded = await cursor.to_list(length=500)

    for chunk in unembedded:
        vector = generate_embedding(chunk["text"])
        await chunks_collection.update_one(
            {"_id": chunk["_id"]},
            {"$set": {"embedding": vector}}
        )

    return len(unembedded)