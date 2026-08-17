import uuid
import datetime
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional
from app.ai import get_llm_provider
from app.rag.vector_index import search_index
from app.tools.registry import tool_registry
from app.models.database_models import Message, AuditLog
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings

logger = logging.getLogger("jarvis.orchestrator")

pending_actions = {}

class AIOrchestrator:
    def __init__(self, db: AsyncSession, user_id: int, username: str, user_role: str):
        self.db = db
        self.user_id = user_id
        self.username = username
        self.user_role = user_role
        self.llm = get_llm_provider()

    async def build_context(self, prompt: str, conversation_id: str) -> Dict[str, Any]:
        context = {}
        citations = []
        rag_results = search_index(prompt, top_k=2)
        if rag_results:
            rag_context = "\n\n--- RETRIEVED DOCUMENT CONTEXT ---\n"
            for r in rag_results:
                rag_context += f"From Source File: '{r['filename']}' (Relevance: {r['score']:.2f}):\n{r['content']}\n\n"
                citations.append({
                    "filename": r["filename"],
                    "excerpt": r["content"][:200],
                    "score": r["score"]
                })
            context["rag_context"] = rag_context
        else:
            context["rag_context"] = ""

        context["citations"] = citations
        return context

    async def detect_and_run_tool(
        self,
        prompt: str,
        conversation_id: str,
        sse_callback: Optional[callable] = None
    ) -> Optional[Dict[str, Any]]:
        p_lower = prompt.lower()
        tool_name = None
        tool_args = {}

        if "weather" in p_lower or "cuaca" in p_lower:
            tool_name = "get_weather"
            words = prompt.split()
            loc = "Kuala Lumpur"
            if "in" in words:
                idx = words.index("in")
                if idx + 1 < len(words):
                    loc = " ".join(words[idx+1:]).strip("?.!")
            tool_args = {"location": loc}

        elif any(x in p_lower for x in ["calculate", "kira", "+", "-", "*", "/"]):
            tool_name = "calculator"
            expr = "".join([c for c in prompt if c in "0123456789+-*/(). "]).strip()
            if not expr or len(expr) < 3:
                expr = "40 + 2"
            tool_args = {"expression": expr}

        elif "status" in p_lower or "health" in p_lower or "kesihatan" in p_lower:
            tool_name = "get_system_health"

        elif "select" in p_lower or "db query" in p_lower or "senaraikan" in p_lower:
            tool_name = "read_only_database_query"
            sql = prompt
            if "select" not in sql.lower():
                sql = "SELECT username, email, role FROM users LIMIT 5;"
            tool_args = {"sql_query": sql}

        elif "delete files" in p_lower or "purge temporary" in p_lower or "padam fail" in p_lower:
            tool_name = "delete_user_session_files"

        if not tool_name:
            return None

        tool = tool_registry.get_tool(tool_name)
        if not tool:
            return None

        if tool.permission_level == "admin" and self.user_role != "admin":
            error_msg = f"Security Exception: Role '{self.user_role}' is unauthorized to run Tool '{tool_name}'."
            if sse_callback:
                await sse_callback("error", {"detail": error_msg})
            return {"error": error_msg}

        if tool.requires_confirmation:
            action_id = str(uuid.uuid4())
            pending_actions[action_id] = {
                "action_id": action_id,
                "user_id": self.user_id,
                "conversation_id": conversation_id,
                "tool_name": tool_name,
                "args": tool_args,
                "expires_at": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
            }
            return {
                "status": "pending_confirmation",
                "action_id": action_id,
                "tool_name": tool_name,
                "args": tool_args
            }

        if sse_callback:
            await sse_callback("tool_start", {"tool_name": tool_name})

        ctx_inject = {"db": self.db}
        try:
            start_time = datetime.datetime.utcnow()
            result = await tool_registry.execute(tool_name, tool_args, context=ctx_inject)
            latency = (datetime.datetime.utcnow() - start_time).total_seconds()

            log_entry = AuditLog(
                user_id=self.user_id,
                action=f"execute_tool:{tool_name}",
                details=f"Arguments: {tool_args}, Latency: {latency:.2f}s",
                status="success"
            )
            self.db.add(log_entry)
            await self.db.commit()

            if sse_callback:
                await sse_callback("tool_result", {"tool_name": tool_name, "result": result})

            return {"status": "success", "tool_name": tool_name, "result": result}
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            if sse_callback:
                await sse_callback("error", {"detail": f"Tool execution failed: {str(e)}"})
            return {"error": str(e)}

    async def execute_pending_action(self, action_id: str, approved: bool) -> Dict[str, Any]:
        action = pending_actions.get(action_id)
        if not action:
            return {"error": "Action expired or invalid."}

        del pending_actions[action_id]

        if not approved:
            log_entry = AuditLog(
                user_id=self.user_id,
                action=f"reject_action:{action['tool_name']}",
                details=f"Rejected action_id: {action_id}",
                status="rejected"
            )
            self.db.add(log_entry)
            await self.db.commit()
            return {"status": "rejected", "message": "Action execution rejected by user."}

        tool_name = action["tool_name"]
        tool_args = action["args"]
        try:
            start_time = datetime.datetime.utcnow()
            result = await tool_registry.execute(tool_name, tool_args, context={"db": self.db})
            latency = (datetime.datetime.utcnow() - start_time).total_seconds()

            log_entry = AuditLog(
                user_id=self.user_id,
                action=f"confirm_and_execute:{tool_name}",
                details=f"Approved action_id: {action_id}, Latency: {latency:.2f}s, Args: {tool_args}",
                status="success"
            )
            self.db.add(log_entry)
            await self.db.commit()

            return {"status": "success", "tool_name": tool_name, "result": result}
        except Exception as e:
            return {"error": f"Execution error: {str(e)}"}

    async def generate_response_stream(
        self,
        prompt: str,
        conversation_id: str,
        sse_callback: callable
    ):
        await sse_callback("message_start", {"conversation_id": conversation_id})

        context = await self.build_context(prompt, conversation_id)
        citations = context.get("citations", [])
        if citations:
            await sse_callback("citation", {"citations": citations})

        tool_resp = await self.detect_and_run_tool(prompt, conversation_id, sse_callback)
        if tool_resp:
            if tool_resp.get("status") == "pending_confirmation":
                await sse_callback("tool_start", {
                    "tool_name": tool_resp["tool_name"],
                    "requires_confirmation": True,
                    "action_id": tool_resp["action_id"],
                    "args": tool_resp["args"]
                })
                await sse_callback("message_complete", {
                    "content": f"Manual confirmation is required to run the action '{tool_resp['tool_name']}'. Please approve to proceed.",
                    "status": "pending_confirmation"
                })
                return

            if "error" in tool_resp:
                await sse_callback("message_complete", {
                    "content": f"I was unable to proceed due to an authorization or security error: {tool_resp['error']}",
                    "status": "error"
                })
                return

            tool_context = f"\n\n--- TOOL EXECUTION RESULTS ---\nTool Name: {tool_resp['tool_name']}\nOutput: {tool_resp['result']}\n"
        else:
            tool_context = ""

        sys_prompt = (
            f"You are {settings.APP_NAME}, a highly advanced personal/organizational AI assistant. "
            "Respond in a polished, highly responsive, helpful style. "
            "Maintain context using user references where available.\n"
            f"{context['rag_context']}"
            f"{tool_context}"
        )

        full_response = ""
        try:
            async for token in self.llm.generate_stream(prompt, sys_prompt, []):
                full_response += token
                await sse_callback("message_delta", {"content": token})

            new_msg = Message(
                conversation_id=conversation_id,
                sender="assistant",
                content=full_response,
                citations=citations if citations else None,
                tool_calls=[{"tool_name": tool_resp["tool_name"], "result": tool_resp["result"]}] if tool_resp else None
            )
            self.db.add(new_msg)
            await self.db.commit()

            await sse_callback("message_complete", {"content": full_response, "citations": citations})
        except Exception as e:
            logger.error(f"Error during response streaming: {str(e)}")
            await sse_callback("error", {"detail": f"AI Engine stream failure: {str(e)}"})
