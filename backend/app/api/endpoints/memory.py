from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any

from backend.app.api.deps import get_db, get_current_active_user
from backend.app.models.models import Memory, User, Conversation, Message
from backend.app.models.schemas import MemoryOut, MemoryCreate

router = APIRouter()

@router.get("/", response_model=List[MemoryOut])
async def list_memories(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Memory).where(Memory.user_id == user.id).order_by(Memory.created_at.desc()))
    return result.scalars().all()

@router.post("/", response_model=MemoryOut)
async def create_memory(
    memory_in: MemoryCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    memory = Memory(
        user_id=user.id,
        content=memory_in.content,
        category=memory_in.category
    )
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    return memory

@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Memory).where((Memory.id == memory_id) & (Memory.user_id == user.id)))
    memory = result.scalars().first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    await db.delete(memory)
    await db.commit()
    return {"status": "success", "message": "Memory deleted successfully."}

@router.get("/export")
async def export_user_data(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    """Compliance / User control: Export all personal information, conversations, and memories."""
    # 1. Fetch memories
    mem_res = await db.execute(select(Memory).where(Memory.user_id == user.id))
    memories = [{"id": m.id, "content": m.content, "category": m.category, "created_at": str(m.created_at)} for m in mem_res.scalars().all()]

    # 2. Fetch conversations and messages
    conv_res = await db.execute(select(Conversation).where(Conversation.user_id == user.id))
    conversations = []
    for conv in conv_res.scalars().all():
        msg_res = await db.execute(select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at))
        messages = [{"role": msg.role, "content": msg.content, "created_at": str(msg.created_at)} for msg in msg_res.scalars().all()]
        conversations.append({
            "id": conv.id,
            "title": conv.title,
            "created_at": str(conv.created_at),
            "messages": messages
        })

    return {
        "user_profile": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "created_at": str(user.created_at)
        },
        "memories": memories,
        "conversations": conversations
    }
