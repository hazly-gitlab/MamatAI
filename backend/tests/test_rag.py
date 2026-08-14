import pytest
from backend.app.rag.vector_store import chunk_text, string_to_vector, cosine_similarity
from backend.app.rag.reader import extract_document_text
import tempfile
import os

def test_chunking_and_vectors():
    text = "This is a very simple document that we want to slice into multiple overlapping sections."
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 20

    vec1 = string_to_vector("Kuala Lumpur is sunny")
    vec2 = string_to_vector("Kuala Lumpur is warm and sunny")
    vec3 = string_to_vector("Python is a programming language")

    sim_similar = cosine_similarity(vec1, vec2)
    sim_different = cosine_similarity(vec1, vec3)

    assert sim_similar > sim_different
    assert sim_similar <= 1.0

def test_text_reader():
    # Write a temporary text file
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"Hello world from JARVIS RAG testing system.")
        temp_name = f.name

    try:
        extracted = extract_document_text(temp_name, "text/plain")
        assert "JARVIS" in extracted
    finally:
        os.remove(temp_name)
