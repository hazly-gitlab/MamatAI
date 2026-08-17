import os
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.models.database_models import Document, AuditLog
from app.models.schemas import DocumentResponse
from app.security.auth import require_write_user, require_user
from app.rag.extractors import extract_text_from_file
from app.rag.vector_index import add_to_index, delete_document_from_index
from app.core.config import settings

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = logging.getLogger("jarvis.api.documents")

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    user=Depends(require_write_user),
    db: AsyncSession = Depends(get_db)
):
    content_length = 0
    filename = file.filename or "unknown"
    filepath = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4()}_{filename}")

    try:
        with open(filepath, "wb") as buffer:
            chunk_size = 1024 * 1024
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                content_length += len(chunk)
                if content_length > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                    raise HTTPException(status_code=413, detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB.")
                buffer.write(chunk)
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=500, detail=f"Failed to write file to disk: {str(e)}")

    file_ext = os.path.splitext(filename)[1].lower().strip(".")

    doc = Document(
        filename=filename,
        filepath=filepath,
        file_type=file_ext,
        file_size=content_length,
        status="processing",
        user_id=user.id
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    try:
        extracted_text = extract_text_from_file(filepath, file_ext)
        if extracted_text.startswith("Error"):
            raise ValueError(extracted_text)

        add_to_index(doc.id, filename, extracted_text)

        doc.status = "ready"
        db.add(doc)

        log = AuditLog(
            user_id=user.id,
            action="upload_document",
            details=f"File {filename} indexed successfully. Size: {content_length} bytes",
            status="success"
        )
        db.add(log)
        await db.commit()
    except Exception as ex:
        doc.status = "failed"
        doc.error_message = str(ex)
        db.add(doc)

        log = AuditLog(
            user_id=user.id,
            action="upload_document",
            details=f"File {filename} index failed: {str(ex)}",
            status="failed"
        )
        db.add(log)
        await db.commit()

    return doc


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    user=Depends(require_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).where(Document.user_id == user.id))
    return result.scalars().all()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    user=Depends(require_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user.id)
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    user=Depends(require_write_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user.id)
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if os.path.exists(doc.filepath):
        try:
            os.remove(doc.filepath)
        except Exception as e:
            logger.error(f"Failed to remove document file: {str(e)}")

    delete_document_from_index(doc.id)

    await db.delete(doc)
    await db.commit()
    return {"status": "success", "message": "Document successfully deleted."}
