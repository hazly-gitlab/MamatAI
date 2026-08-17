import uuid
import json
import logging
import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, AsyncGenerator
from app.core.database import get_db
from app.models.database_models import Conversation, Message, Document, AuditLog
from app.models.schemas import ConversationResponse, MessageResponse
from app.security.auth import require_user, require_write_user, require_admin
from app.services.orchestrator import AIOrchestrator
from app.rag.extractors import extract_text_from_file
from app.rag.vector_index import add_to_index
from app.core.config import settings

router = APIRouter(prefix="/conversations", tags=["Conversations"])
logger = logging.getLogger("jarvis.api.conversations")

@router.post("", response_model=ConversationResponse)
async def create_conversation(
    title: str = "New Chat",
    user=Depends(require_write_user),
    db: AsyncSession = Depends(get_db)
):
    cid = str(uuid.uuid4())
    conv = Conversation(id=cid, title=title, user_id=user.id)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    user=Depends(require_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    user=Depends(require_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    )
    conv = result.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user=Depends(require_write_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    )
    conv = result.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conv)
    await db.commit()
    return {"status": "success", "message": "Conversation successfully removed."}


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    conversation_id: str,
    user=Depends(require_user),
    db: AsyncSession = Depends(get_db)
):
    result_conv = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    )
    if not result_conv.scalars().first():
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    return result.scalars().all()


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def create_message(
    conversation_id: str,
    content: str,
    sender: str = "user",
    audio_url: Optional[str] = None,
    image_url: Optional[str] = None,
    user=Depends(require_write_user),
    db: AsyncSession = Depends(get_db)
):
    result_conv = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    )
    if not result_conv.scalars().first():
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg = Message(
        conversation_id=conversation_id,
        sender=sender,
        content=content,
        audio_url=audio_url,
        image_url=image_url
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


@router.post("/{conversation_id}/messages/stream")
async def stream_ai_message(
    conversation_id: str,
    prompt: str = Form(...),
    image: Optional[UploadFile] = File(None),
    user=Depends(require_write_user),
    db: AsyncSession = Depends(get_db)
):
    result_conv = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    )
    conv = result_conv.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    image_url = None
    if image:
        import os
        filename = f"{uuid.uuid4()}_{image.filename}"
        filepath = os.path.join(settings.UPLOAD_DIR, filename)
        with open(filepath, "wb") as buffer:
            buffer.write(await image.read())
        image_url = f"/api/uploads/{filename}"

    user_msg = Message(
        conversation_id=conversation_id,
        sender="user",
        content=prompt,
        image_url=image_url
    )
    db.add(user_msg)
    await db.commit()

    orchestrator = AIOrchestrator(
        db=db,
        user_id=user.id,
        username=user.username,
        user_role=user.role
    )

    async def sse_generator() -> AsyncGenerator[str, None]:
        queue = asyncio.Queue()

        async def sse_callback(event_type: str, data: dict):
            await queue.put((event_type, data))

        stream_task = asyncio.create_task(
            orchestrator.generate_response_stream(
                prompt=prompt if not image_url else f"[Vision Screenshot Context: {image_url}] {prompt}",
                conversation_id=conversation_id,
                sse_callback=sse_callback
            )
        )

        while not stream_task.done() or not queue.empty():
            try:
                event_type, data = await asyncio.wait_for(queue.get(), timeout=1.0)
                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
                queue.task_done()
            except asyncio.TimeoutError:
                if stream_task.done() and queue.empty():
                    break

        if stream_task.exception():
            err_detail = f"Internal orchestrator error: {str(stream_task.exception())}"
            logger.error(err_detail)
            yield f"event: error\ndata: {json.dumps({'detail': err_detail})}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@router.post("/action/confirm")
async def confirm_action(
    action_id: str,
    approved: bool,
    user=Depends(require_write_user),
    db: AsyncSession = Depends(get_db)
):
    orchestrator = AIOrchestrator(
        db=db,
        user_id=user.id,
        username=user.username,
        user_role=user.role
    )
    res = await orchestrator.execute_pending_action(action_id, approved)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res
