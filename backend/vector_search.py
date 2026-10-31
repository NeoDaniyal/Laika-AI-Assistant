"""
vector_search.py
================
Phase 3.1: In-Memory Vector Similarity math.
Phase 3.3: Vector Similarity Math and Top-K Similarity Search.
Phase 4.4: Vector Similarity Math and Top-K Filtering with Thresholding.
and Strict RAG Context Assembly.
"""

import math 
from typing import List, Dict, Any
from backend.embeddings import generate_embedding
from backend.database import db
from bson import ObjectId

chunks_collection = db["rag_chunks"]

def dot_product(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculate dot-product between two equal-length vectors."""
    if len(vec_a) != len(vec_b):
        raise ValueError(f"Vector dimension do not match: {len(vec_a)} vs {len(vec_b)}")
    return sum(a * b for a, b in zip(vec_a, vec_b))

def vector_magnitude(vec: List[float]) -> float:
    """Calculate the Euclidean norm (length) of a vector."""
    return math.sqrt(sum(x * x for x in vec))

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors:
    cos(theta) = (A.B)/ (|A| * |B|)
    Range: -1.0 (opposite) to 1.0 (identical direction)
    """
    mag_a = vector_magnitude(vec_a)
    mag_b = vector_magnitude(vec_b)

    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0

    return dot_product(vec_a, vec_b) / (mag_a * mag_b)


async def search_similar_chunks(
    query: str,
    user_id: str,
    top_k: int = 5,
    score_threshold: float = 0.0,
    document_ids: List[str] | None = None
) -> List[Dict[str, Any]]:
    """
    Generates an embedding for the query, compares it against stored chunk
    embeddings for a given user (optionally filtered by document IDs), ranks them by cosine similarity, and returns
    the Top-K highest scoring chunks.
    """
    db_query = {"user_id": user_id}

    if document_ids:
        try:
            object_ids = [ObjectId(doc_id) for doc_id in document_ids]
            db_query["document_id"] = {"$in": object_ids}
        except Exception as e:
            print(f"[RAG] Invalid document ID: {e}")
            return []

    # ----------------------------------
    # SUMMARY MODE
    # ----------------------------------
    summary_keywords = [
        "summarize",
        "summary",
        "summarise",
        "explain document",
        "give summary"
    ]

    if any(keyword in query.lower() for keyword in summary_keywords):
        stored_chunks = await chunks_collection.find(
            db_query
        ).sort("chunk_index", 1).to_list(length=100000)

        print(
            f"[RAG DEBUG] SUMMARY MODE: "
            f"Returning {len(stored_chunks)} chunks"
        )

        results = []

        for chunk in stored_chunks:
            results.append({
                "chunk_id": str(chunk["_id"]),
                "document_id": str(chunk["document_id"]),
                "user_id": chunk["user_id"],
                "chunk_index": chunk.get("chunk_index", 0),
                "filename": chunk.get("filename", "unknown"),
                "text": chunk["text"],
                "score": 1.0
            })

        return results

    # ----------------------------------
    # NORMAL VECTOR SEARCH MODE
    # ----------------------------------
    query_vector = generate_embedding(query)

    stored_chunks = await chunks_collection.find(
        db_query
    ).to_list(length=100000)

    print(f"[RAG DEBUG] MongoDB filter: {db_query}")
    print(f"[RAG DEBUG] Matched chunks: {len(stored_chunks)}")

    scored_chunks = []

    for chunk in stored_chunks:
        chunk_vector = chunk.get("embedding")

        if not chunk_vector:
            continue

        score = cosine_similarity(
            query_vector,
            chunk_vector
        )

        print(
            f"[RAG DEBUG] "
            f"File={chunk.get('filename')} "
            f"Chunk={chunk.get('chunk_index')} "
            f"Score={score:.4f}"
        )

        if score >= score_threshold:
            scored_chunks.append({
                "chunk_id": str(chunk["_id"]),
                "document_id": str(chunk["document_id"]),
                "user_id": chunk["user_id"],
                "chunk_index": chunk.get("chunk_index", 0),
                "filename": chunk.get("filename", "unknown"),
                "text": chunk["text"],
                "score": score
            })

    scored_chunks.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    results = scored_chunks[:top_k]

    print(f"[RAG DEBUG] Stored chunks: {len(stored_chunks)}")
    print(f"[RAG DEBUG] Above threshold: {len(scored_chunks)}")
    print(f"[RAG DEBUG] Retrieved chunks: {len(results)}")

    return results


async def fetch_all_document_chunks(
    user_id: str,
    document_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Fetches all chunks sequentially for specific document IDs, bypassing embeddings 
    entirely for reliable document summarization.
    """
    try:
        object_ids = [ObjectId(x) for x in document_ids]
    except Exception as e:
        print(f"[RAG] Invalid document ID for full fetch: {e}")
        return []

    chunks = await chunks_collection.find({
        "user_id": user_id,
        "document_id": {"$in": object_ids}
    }).sort("chunk_index", 1).to_list(length=100000)

    return [{
        "chunk_id": str(chunk["_id"]),
        "document_id": str(chunk["document_id"]),
        "user_id": chunk["user_id"],
        "chunk_index": chunk.get("chunk_index", 0),
        "filename": chunk.get("filename", "unknown"),
        "text": chunk["text"],
        "score": 1.0
    } for chunk in chunks]


def build_retrieval_context(
    retrieved_chunks: List[Dict[str, Any]]
) -> str:
    """
    Formats Top-K retrieved chunks into a single structured context block.
    """
    if not retrieved_chunks:
        return (
            "[NO RELEVANT DOCUMENTATION FOUND]\n"
            "No matching content was found."
        )

    context_blocks = []

    for idx, chunk in enumerate(retrieved_chunks, start=1):
        block = (
            f"--- [Document {idx}] ---\n"
            f"Source: {chunk.get('filename')}\n"
            f"Chunk: {chunk.get('chunk_index')}\n"
            f"Content:\n"
            f"{chunk.get('text', '')}\n\n"
        )

        context_blocks.append(block)

    return (
        "[START RETRIEVED KNOWLEDGE]\n"
        + "".join(context_blocks)
        + "\n[END RETRIEVED KNOWLEDGE]"
    )