import uuid
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.api.deps import get_db, get_current_active_user
from app.models.models import User, Conversation, Message, ToolSetting
from app.models.schemas import ConversationOut, ConversationDetail, MessageOut
from app.ai.providers import get_llm_provider
from app.ai.orchestrator import build_messages_with_context
from app.tools.registry import execute_tool
from app.api.endpoints.documents import search_relevant_chunks

router = APIRouter()

@router.get("/conversations", response_model=List[ConversationOut])
async def get_conversations(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
    )
    return result.scalars().all()

@router.post("/conversations", response_model=ConversationOut)
async def create_conversation(
    title: Optional[str] = "New Chat",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    conv_id = str(uuid.uuid4())
    conv = Conversation(
        id=conv_id,
        user_id=user.id,
        title=title
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv

@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation_details(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(Conversation)
        .where((Conversation.id == conversation_id) & (Conversation.user_id == user.id))
    )
    conv = result.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Load messages
    msg_res = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = msg_res.scalars().all()

    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
        "messages": messages
    }

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(Conversation)
        .where((Conversation.id == conversation_id) & (Conversation.user_id == user.id))
    )
    conv = result.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conv)
    await db.commit()
    return {"status": "success", "message": "Conversation deleted."}

@router.post("/conversations/{conversation_id}/send")
async def send_message(
    conversation_id: str,
    content: str,
    attachments: Optional[Dict[str, Any]] = None, # Path/type/OCR details of images or document contents
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    """
    Main conversational gateway.
    Handles message history, RAG context search, tool intent recognition, and executes actions.
    """
    # 1. Fetch conversation
    conv_result = await db.execute(
        select(Conversation)
        .where((Conversation.id == conversation_id) & (Conversation.user_id == user.id))
    )
    conv = conv_result.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 2. Add user message
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=content,
        attachments=attachments,
        created_at=datetime.utcnow()
    )
    db.add(user_msg)

    # Update conversation updated_at
    conv.updated_at = datetime.utcnow()

    # Auto-title conversation if it's default
    if conv.title == "New Chat" and len(content) > 1:
        conv.title = content[:40] + "..." if len(content) > 40 else content

    await db.commit()

    # 2b. Check if user intent matches a registered Autonomous Skill
    from app.skills.engine import SkillEngine
    skill_engine = SkillEngine()
    skill_result = await skill_engine.handle_conversational_skill(content, db, user)

    if skill_result:
        if skill_result.get("status") == "pending_confirmation":
            pending_msg_text = (
                f"JARVIS wishes to execute the Autonomous Skill '{skill_result['skill_name']}' with parameters:\n"
                f"```json\n{json.dumps(skill_result['parameters'], indent=2)}\n```\n"
                f"This sensitive action requires your explicit confirmation below."
            )
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=pending_msg_text,
                attachments={
                    "pending_skill": skill_result["skill_name"],
                    "audit_id": skill_result["audit_id"],
                    "requires_approval": True
                },
                created_at=datetime.utcnow()
            )
            db.add(assistant_msg)
            await db.commit()
            return {"status": "pending_confirmation", "message": assistant_msg}
        else:
            assistant_msg_text = (
                f"Executed Autonomous Skill: **{skill_result['skill_name']} v{skill_result.get('version', '1.0.0')}**\n"
                f"Execution status: **{skill_result.get('status')}** ({skill_result.get('execution_time_ms', 0):.1f}ms)\n\n"
                f"```json\n{json.dumps(skill_result.get('trace', []), indent=2)}\n```"
            )
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_msg_text,
                attachments={"skill_executed": skill_result["skill_name"], "trace": skill_result.get("trace")},
                created_at=datetime.utcnow()
            )
            db.add(assistant_msg)
            await db.commit()
            return {"status": "success", "message": assistant_msg}

    # 3. Search RAG document knowledge base for contextual documents
    rag_matches = await search_relevant_chunks(user.id, content, db)
    rag_context = ""
    citations = []
    if rag_matches:
        rag_context = "\n".join([f"Source [{m['filename']}]: {m['content']}" for m in rag_matches if m['similarity'] > 0.15])
        citations = [{
            "filename": m["filename"],
            "snippet": m["content"][:200] + "...",
            "similarity": m["similarity"]
        } for m in rag_matches if m['similarity'] > 0.15]

    # 4. Extract attachment metadata if any (e.g. image OCR text)
    vision_context = ""
    if attachments and "ocr" in attachments:
        vision_context = attachments["ocr"]

    # 5. Load full history of current conversation
    history_res = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    history_messages = [{"role": m.role, "content": m.content} for m in history_res.scalars().all()]

    # 6. Build system prompts and messages list
    llm_messages = build_messages_with_context(
        history=history_messages,
        rag_context=rag_context,
        vision_context=vision_context
    )

    # 7. Get LLM provider and execute
    provider = get_llm_provider()

    assistant_content = ""
    tool_triggered = None
    tool_call_details = None

    async for chunk in provider.chat_completion(llm_messages, stream=False):
        if chunk["type"] == "content":
            assistant_content += chunk["data"]
        elif chunk["type"] == "tool_calls":
            # An LLM tool call intent was triggered
            tool_call = chunk["data"][0]
            func_name = tool_call["function"]["name"]
            func_args = json.loads(tool_call["function"]["arguments"])

            tool_triggered = func_name
            tool_call_details = func_args

    # Handle Tool Trigger
    if tool_triggered:
        # Check if tool requires confirmation
        tool_set_res = await db.execute(select(ToolSetting).where(ToolSetting.name == tool_triggered))
        tool_setting = tool_set_res.scalars().first()

        # Default settings if tool not in DB yet
        requires_confirmation = tool_setting.requires_confirmation if tool_setting else False

        if requires_confirmation:
            # We must pause the AI and request user confirmation.
            # Return a special payload to the frontend.
            pending_response_content = (
                f"JARVIS wishes to run the tool '{tool_triggered}' with arguments:\n"
                f"```json\n{json.dumps(tool_call_details, indent=2)}\n```\n"
                f"Please confirm or deny this action below."
            )

            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=pending_response_content,
                attachments={
                    "pending_tool": tool_triggered,
                    "arguments": tool_call_details,
                    "requires_approval": True
                },
                created_at=datetime.utcnow()
            )
            db.add(assistant_msg)
            await db.commit()

            return {
                "status": "pending_confirmation",
                "message": assistant_msg,
                "citations": citations
            }
        else:
            # Execute tool directly
            try:
                tool_result = await execute_tool(tool_triggered, tool_call_details)
                assistant_response_text = (
                    f"Successfully executed tool '{tool_triggered}'.\n"
                    f"Result:\n```json\n{json.dumps(tool_result, indent=2)}\n```"
                )
            except Exception as e:
                assistant_response_text = f"Failed to execute tool '{tool_triggered}': {str(e)}"

            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_response_text,
                attachments={"tool_executed": tool_triggered, "result": tool_result if 'tool_result' in locals() else None},
                created_at=datetime.utcnow()
            )
            db.add(assistant_msg)
            await db.commit()

            return {
                "status": "success",
                "message": assistant_msg,
                "citations": citations
            }

    # Add regular assistant message to history
    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_content or "Hello! Let me know how I can help.",
        attachments={"citations": citations} if citations else None,
        created_at=datetime.utcnow()
    )
    db.add(assistant_msg)
    await db.commit()

    return {
        "status": "success",
        "message": assistant_msg,
        "citations": citations
    }

@router.get("/conversations/{conversation_id}/send/stream")
async def send_message_stream(
    conversation_id: str,
    content: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    """
    Server-Sent Events (SSE) dynamic streaming completions endpoint.
    Streams incremental response tokens to the web client instantly.
    """
    async def sse_event_generator():
        provider = get_llm_provider()
        # Build simple mock query list
        messages_list = [{"role": "system", "content": "You are JARVIS"}, {"role": "user", "content": content}]

        async for chunk in provider.chat_completion(messages_list, stream=True):
            if chunk["type"] == "content":
                yield f"data: {json.dumps({'token': chunk['data']})}\n\n"
                await asyncio.sleep(0.02)
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_event_generator(), media_type="text/event-stream")
