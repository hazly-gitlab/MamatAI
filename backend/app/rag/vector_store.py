import math
from typing import List, Dict, Any, Optional
import numpy as np

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """Slices a long string into overlapping chunk paragraphs."""
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

def string_to_vector(text: str, dimensions: int = 128) -> List[float]:
    """
    Generate a deterministic high-fidelity mock vector representation of a string
    using a hash-based term-frequency algorithm.
    This enables full vector database operations and cosine similarity sorting on CPU
    without external API keys or heavy local neural network downloads.
    """
    vec = np.zeros(dimensions)
    words = text.lower().split()
    if not words:
        # Return random but normalized vector
        vec[0] = 1.0
        return vec.tolist()

    for word in words:
        # Compute simple hash code
        h = sum(ord(c) * (i + 1) for i, c in enumerate(word))
        index = h % dimensions
        vec[index] += 1.0

    # L2 Normalization
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm

    return vec.tolist()

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    arr1 = np.array(v1)
    arr2 = np.array(v2)
    dot = np.dot(arr1, arr2)
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot / (norm1 * norm2))

async def get_embedding(text: str) -> List[float]:
    """Generates a text embedding. Swappable with cloud API if desired."""
    # For robust local deployment, we default to string_to_vector
    return string_to_vector(text)
