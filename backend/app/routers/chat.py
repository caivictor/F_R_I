"""Router for conversational multi-agent chat and streaming endpoints."""

import json
import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.app.agents.manager import manager_agent
from backend.app.db.database import db

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


class ChatMessageItem(BaseModel):
    """Chat message history item."""

    role: str
    content: str
    timestamp: str


class SessionSummaryItem(BaseModel):
    """Session summary overview item."""

    session_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0
    last_ticker: Optional[str] = None
    summary: Optional[str] = None


class SessionDetailResponse(BaseModel):
    """Detailed chat session response including full message history and memory."""

    session_id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[ChatMessageItem]
    memory: Optional[Dict[str, Any]] = None


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


# --- Session Listing and Conversation Continuity Endpoints ---


@router.get("/sessions", response_model=List[SessionSummaryItem])
async def list_chat_sessions(limit: int = Query(default=50, ge=1, le=200)) -> List[SessionSummaryItem]:
    """Retrieve all persisted chat sessions with metadata and entity summaries."""
    sessions = db.list_sessions(limit=limit)
    return [SessionSummaryItem(**s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_chat_session_details(session_id: str) -> SessionDetailResponse:
    """Retrieve a specific chat session with full message history and conversation memory."""
    sess = db.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Chat session '{session_id}' not found.")
    return SessionDetailResponse(**sess)


@router.get("/sessions/{session_id}/memory")
async def get_chat_session_memory(session_id: str) -> Dict[str, Any]:
    """Retrieve the stored entity memory, active ticker, and compression summary for a session."""
    mem = db.get_conversation_memory(session_id)
    if not mem:
        return {"session_id": session_id, "memory": None}
    return {"session_id": session_id, "memory": mem}


@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str) -> Dict[str, Any]:
    """Delete a chat session and all associated messages and memory."""
    success = manager_agent.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found or could not be deleted.")
    return {"status": "deleted", "session_id": session_id}


@router.delete("/sessions")
async def delete_all_chat_sessions() -> Dict[str, Any]:
    """Delete all chat sessions and clear session memory."""
    manager_agent.delete_all_sessions()
    return {"status": "all_sessions_cleared"}
