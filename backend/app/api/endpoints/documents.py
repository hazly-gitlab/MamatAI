import os
import shutil
import tempfile
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_active_user
from app.models.models import Document, DocumentChunk, User
from app.models.schemas import DocumentOut
from app.rag.reader import extract_document_text
from app.rag.vector_store import chunk_text, get_embedding, cosine_similarity

router = APIRouter()

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".xls", ".csv", ".txt", ".md", ".markdown"}

@router.get("/", response_model=List[DocumentOut])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Document).where(Document.user_id == user.id).order_by(Document.created_at.desc()))
    return result.scalars().all()

@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read/spool file content to check file size limit
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size limit of {MAX_FILE_SIZE // (1024*1024)}MB."
        )

    # Write to a persistent storage or temp directory
    upload_dir = "/tmp/jarvis_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{user.id}_{file.filename}")

    with open(file_path, "wb") as f:
        f.write(contents)

    # Create DB entry
    document = Document(
        user_id=user.id,
        filename=file.filename,
        file_path=file_path,
        file_size=len(contents),
        content_type=file.content_type or "application/octet-stream",
        status="processing"
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Process text extraction & vector chunking asynchronously
    try:
        text = extract_document_text(file_path, file.content_type or "")
        chunks = chunk_text(text)

        for i, text_chunk in enumerate(chunks):
            vector = await get_embedding(text_chunk)
            db_chunk = DocumentChunk(
                document_id=document.id,
                content=text_chunk,
                chunk_index=i,
                embedding={"vector": vector}
            )
            db.add(db_chunk)

        # Optional: Generate simple summary
        document.summary = text[:300] + "..." if len(text) > 300 else text
        document.status = "ready"
        await db.commit()
        await db.refresh(document)
    except Exception as e:
        document.status = "error"
        document.summary = f"Processing error: {str(e)}"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {str(e)}"
        )

    return document

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Document).where((Document.id == document_id) & (Document.user_id == user.id)))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or access denied.")

    # Delete from filesystem if exists
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    await db.delete(doc)
    await db.commit()
    return {"status": "success", "message": "Document and its semantic indices deleted successfully."}

async def search_relevant_chunks(
    user_id: int,
    query: str,
    db: AsyncSession,
    limit: int = 4
) -> List[dict]:
    """Retrieve top matches from the vector database using cosine-similarity."""
    query_vector = await get_embedding(query)

    # Load all chunks belonging to user's documents
    stmt = (
        select(DocumentChunk, Document.filename)
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(Document.user_id == user_id)
    )
    res = await db.execute(stmt)
    all_chunks = res.all()

    matches = []
    for chunk, filename in all_chunks:
        if chunk.embedding and "vector" in chunk.embedding:
            similarity = cosine_similarity(query_vector, chunk.embedding["vector"])
            matches.append({
                "content": chunk.content,
                "filename": filename,
                "similarity": similarity,
                "chunk_index": chunk.chunk_index
            })

    # Sort by similarity descending
    matches.sort(key=lambda x: x["similarity"], reverse=True)
    return matches[:limit]
