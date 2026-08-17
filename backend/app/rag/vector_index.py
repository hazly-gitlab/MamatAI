import numpy as np
from typing import List, Dict, Any

vector_store_db: List[Dict[str, Any]] = []

def get_simple_hash_embedding(text: str) -> List[float]:
    emb = [0.0] * 128
    for i, char in enumerate(text[:256]):
        emb[i % 128] += ord(char)
    norm = np.linalg.norm(emb) or 1.0
    emb = [float(x / norm) for x in emb]
    return emb

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
        if len(chunk_words) < chunk_size:
            break
    return chunks or [text]

def add_to_index(document_id: int, filename: str, text: str):
    chunks = chunk_text(text)
    for i, chunk in enumerate(chunks):
        embedding = get_simple_hash_embedding(chunk)
        vector_store_db.append({
            "doc_id": document_id,
            "filename": filename,
            "chunk_index": i,
            "content": chunk,
            "embedding": embedding
        })

def search_index(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    if not vector_store_db:
        return []

    query_emb = np.array(get_simple_hash_embedding(query))
    scored_chunks = []

    for item in vector_store_db:
        item_emb = np.array(item["embedding"])
        similarity = float(np.dot(query_emb, item_emb))
        scored_chunks.append((similarity, item))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, item in scored_chunks[:top_k]:
        if score > 0.1:
            results.append({
                "score": score,
                "filename": item["filename"],
                "content": item["content"],
                "doc_id": item["doc_id"]
            })
    return results

def delete_document_from_index(document_id: int):
    global vector_store_db
    vector_store_db = [item for item in vector_store_db if item["doc_id"] != document_id]
