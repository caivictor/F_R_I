"""Unit and integration tests for SQLite chat session persistence and cross-session continuity."""

import pytest
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.db.database import db
from backend.app.agents.manager import ManagerAgent, SessionState


@pytest.mark.asyncio
async def test_session_persistence_crud_and_endpoints():
    """Verify chat sessions are persisted in SQLite and accessible via REST API."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Start a new chat session via /api/chat
        res1 = await client.post(
            "/api/chat",
            json={"message": "Analyze Microsoft fundamentals"},
        )
        assert res1.status_code == 200
        data1 = res1.json()
        session_id = data1["session_id"]
        assert session_id is not None

        # 2. List sessions via GET /api/chat/sessions
        list_res = await client.get("/api/chat/sessions")
        assert list_res.status_code == 200
        sessions = list_res.json()
        assert len(sessions) >= 1
        found = [s for s in sessions if s["session_id"] == session_id]
        assert len(found) == 1
        assert found[0]["last_ticker"] == "MSFT"

        # 3. Get session details via GET /api/chat/sessions/{session_id}
        det_res = await client.get(f"/api/chat/sessions/{session_id}")
        assert det_res.status_code == 200
        details = det_res.json()
        assert details["session_id"] == session_id
        assert len(details["messages"]) >= 2
        assert details["memory"]["last_ticker"] == "MSFT"

        # 4. Continue conversation in same session (pronoun continuity across turns)
        res2 = await client.post(
            "/api/chat",
            json={"message": "What is its current valuation multiple?", "session_id": session_id},
        )
        assert res2.status_code == 200
        assert "MSFT" in res2.json()["response"]

        # 5. Delete session via DELETE /api/chat/sessions/{session_id}
        del_res = await client.delete(f"/api/chat/sessions/{session_id}")
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "deleted"

        # Verify it is no longer present
        det_after = await client.get(f"/api/chat/sessions/{session_id}")
        assert det_after.status_code == 404


@pytest.mark.asyncio
async def test_session_state_restoration_across_restarts():
    """Verify ManagerAgent restores SessionState from SQLite DB when an existing session_id is presented."""
    session_id = "test_restoration_sess_99"
    # Clean up first if exists
    db.delete_session(session_id)

    db.create_or_update_session(session_id=session_id, title="Discovery Session")
    db.save_chat_message(session_id=session_id, role="user", content="Discover top tech stocks")
    db.save_chat_message(session_id=session_id, role="assistant", content="Found NVDA, AAPL, MSFT")
    db.save_conversation_memory(
        session_id=session_id,
        last_ticker="NVDA",
        last_discovered_companies=[{"ticker": "NVDA", "name": "NVIDIA"}, {"ticker": "AAPL", "name": "Apple"}],
        last_discovered_tickers=["NVDA", "AAPL"],
        summary="Prior discovery completed for NVDA and AAPL",
    )

    # Instantiate a fresh ManagerAgent (simulating server restart)
    fresh_manager = ManagerAgent()
    restored_session = fresh_manager.get_or_create_session(session_id)

    assert restored_session.session_id == session_id
    assert restored_session.last_ticker == "NVDA"
    assert restored_session.last_discovered_tickers == ["NVDA", "AAPL"]
    assert len(restored_session.messages) == 2
    assert "Prior discovery" in (restored_session.summary or "")

    # Clean up
    db.delete_session(session_id)
