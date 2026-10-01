"""
embeddings.py
==============
RAG Phase 2.1: Vector Embedding Generation using SentenceTransformers.
"""
from typing import List
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def generate_embedding(text: str)-> List[float]:
    """
    Generates a 384-dimensional vector embeddding for given text string.
    Converts numpy.ndarray to Python float list for native MongoDB storage.
    """
    if not text or not text.strip():
        return []

    vector = model.encode(text)

    return vector.tolist()