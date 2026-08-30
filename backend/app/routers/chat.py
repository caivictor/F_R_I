"""Router for conversational multi-agent chat and streaming endpoints."""

import json
import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.app.agents.manager import manager_agent

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Incoming chat request payload."""

    message: str = Field(..., description="User prompt or instruction")
    session_id: Optional[str] = Field(default=None, description="Optional conversational session ID")


class ChatResponse(BaseModel):
    """Non-streaming chat response model."""

    response: str
    session_id: str
    steps: List[Dict[str, Any]]
    agent_data: Optional[Dict[str, Any]] = None


@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Non-streaming conversational multi-agent chat endpoint."""
    result = await manager_agent.process_message(
        user_message=request.message,
        session_id=request.session_id,
    )
    return ChatResponse(
        response=result["response"],
        session_id=result["session_id"],
        steps=result["steps"],
        agent_data=result.get("agent_data"),
    )


@router.post("/stream")
async def chat_stream_endpoint(request: ChatRequest) -> StreamingResponse:
    """Server-Sent Events (SSE) streaming chat endpoint."""
    queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

    async def step_callback(step: Dict[str, Any]) -> None:
        await queue.put({"type": "step", "agent": step.get("agent", "manager"), "message": step.get("message", "")})

    async def background_task() -> None:
        try:
            result = await manager_agent.process_message(
                user_message=request.message,
                session_id=request.session_id,
                progress_callback=step_callback,
            )
            # Emit token chunks for response text
            full_response = result["response"]
            chunk_size = 64
            for i in range(0, len(full_response), chunk_size):
                chunk = full_response[i:i + chunk_size]
                await queue.put({"type": "chunk", "content": chunk})
                await asyncio.sleep(0.01)

            # Emit done event
            await queue.put({
                "type": "done",
                "response": full_response,
                "session_id": result["session_id"],
                "agent_data": result.get("agent_data"),
            })
        except Exception as e:
            await queue.put({
                "type": "error",
                "message": str(e),
            })
        finally:
            await queue.put({"type": "__END__"})

    async def event_generator() -> AsyncGenerator[str, None]:
        task = asyncio.create_task(background_task())
        try:
            while True:
                item = await queue.get()
                if item.get("type") == "__END__":
                    break
                yield f"data: {json.dumps(item)}\n\n"
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
