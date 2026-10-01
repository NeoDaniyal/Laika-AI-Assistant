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

chunks_collection = db["rag_chunks"]

def dot_product(vec_a: List[float], vec_b: List[float])->float:
    """Calculate dot-product between two equal-length vectors."""
    if len(vec_a) != len(vec_b):
        raise ValueError(f"Vector dimension do not match: {len(vec_a)} vs {len(vec_b)}")
    return sum(a*b for a,b in zip(vec_a, vec_b))

def vector_magnitude(vec: List[float])-> float:
    """Calculate the Euclidean norm ((length)) of a vector."""
    return math.sqrt(sum(x*x for x in vec))

def cosine_similarity(vec_a: List[float], vec_b: List[float])->float:
    """
    Calculate cosine similarity between two vectors:
    cos(theta) = (A.B)/ (|A| * |B|)
    Range: -1.0 (opposite) to 1.0 (identical direction)
    """
    mag_a = vector_magnitude(vec_a)
    mag_b = vector_magnitude(vec_b)

    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0

    return dot_product(vec_a, vec_b)/(mag_a*mag_b)

async def search_similar_chunks(query: str, top_k: int=2, score_threshold: float=0.45, user_id: str= "default_user")-> List[Dict[str, Any]]:
    """
    Generates an embedding for the query, compares it against ALL stored chunk
    embeddings for a given user, ranks them by cosine similarity, and returns
    the Top-K highest scoring chunks.
    """

    query_vector = generate_embedding(query)
    stored_chunks = await chunks_collection.find({"user_id": user_id}).to_list(length=100000)

    scored_chunks = []
    for chunk in stored_chunks:
        chunk_vector = chunk.get("embedding")
        if chunk_vector:
            score = cosine_similarity(query_vector, chunk_vector)
            if score >= score_threshold:
                scored_chunks.append({
                    "chunk_id": str(chunk["_id"]),
                    "chunk_index": chunk["chunk_index"],
                    "filename": chunk.get("filename", "unknown"),
                    "text": chunk["text"],
                    "score": score
                })

    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k]

def build_retrieval_context(retrieved_chunks: List[Dict[str, Any]]) -> str:
    """
    Phase 4.1: Formats Top-K retrieved chunks into a single, structured
    context block ready for LLM prompt injection.

    Phase 4.4: Formats Top-K retrieved chunks into a single structured context block.
    If no chunks meet the relevance threshold, returns an explicit rejection instruction.
    """
    if not retrieved_chunks:
        return (
            "[NO RELEVANT DOCUMENTATION FOUND]\n"
            "None of the stored document chunks met the minimum relevance threshold for this query. "
            "If the user is asking a question specifically about uploaded documents, state clearly "
            "that the retrieved documents do not contain this information."
        )

    context_blocks = []
    for idx, chunk in enumerate(retrieved_chunks, start=1):
        filename = chunk.get("filename", "Unknown Source")
        chunk_idx = chunk.get("chunk_index", "N/A")
        score = chunk.get("score", 0.0)
        text = chunk.get("text", "").strip()

        block = (
            f"--- [Document {idx}] ---\n"
            f"Source: {filename}\n"
            f"Chunk: {chunk_idx}\n"
            f"Relevance Score: {score:.4f}\n"
            f"Content:\n{text}\n"
        )
        context_blocks.append(block)

    formatted_context = (
        "[START RETRIEVED KNOWLEDGE]\n"
        + "\n".join(context_blocks)
        + "[END RETRIEVED KNOWLEDGE]"
    )
    
    return formatted_context