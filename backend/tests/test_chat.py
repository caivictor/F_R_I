"""Unit and integration tests for chat and streaming endpoints."""

import json
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_chat_research_routing():
    """Test routing market news queries to the Research Agent."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"message": "What are today's top business news and market themes?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert "steps" in data
        assert any(step["agent"] == "research" for step in data["steps"])
        assert "Market Intelligence Briefing" in data["response"]


@pytest.mark.asyncio
async def test_chat_analysis_routing():
    """Test routing ticker analysis to Analysis Agent."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"message": "Analyze Apple fundamentals and moat"},
        )
        assert response.status_code == 200
        data = response.json()
        assert any(step["agent"] == "analysis" for step in data["steps"])
        assert "Long-Term Investment Dossier" in data["response"]
        assert "ROIC" in data["response"]
        assert "AAPL" in data["response"]


@pytest.mark.asyncio
async def test_chat_analysis_private_company_rejection():
    """Test that private companies like OpenAI or SpaceX are strictly rejected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"message": "Analyze OpenAI for me"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "Analysis Rejection" in data["response"]
        assert "private company" in data["response"]


@pytest.mark.asyncio
async def test_chat_analysis_non_us_otc_rejection():
    """Test that OTC or non-US listings are rejected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"message": "Analyze 0700.HK or TCEHY.PK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "Analysis Rejection" in data["response"]


@pytest.mark.asyncio
async def test_chat_portfolio_routing():
    """Test routing portfolio queries to Investment Agent."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"message": "What is my current portfolio balance and holdings?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert any(step["agent"] == "investment" for step in data["steps"])
        assert "Portfolio & Investment Summary" in data["response"]
        assert "Net Asset Value" in data["response"]


@pytest.mark.asyncio
async def test_chat_trade_two_step_confirmation_flow():
    """Test 2-step trade confirmation interlock for buy and execution."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Initiate trade order
        res1 = await client.post(
            "/api/chat",
            json={"message": "Buy 10 shares of NVDA"},
        )
        assert res1.status_code == 200
        data1 = res1.json()
        session_id = data1["session_id"]
        assert "Trade Order Confirmation Required" in data1["response"]
        assert "Confirm purchase? [Yes / No]" in data1["response"]

        # Step 2: Confirm trade order
        res2 = await client.post(
            "/api/chat",
            json={"message": "Yes, confirm purchase", "session_id": session_id},
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert "Trade Confirmation & Execution" in data2["response"]
        assert "Successfully purchased 10" in data2["response"]


@pytest.mark.asyncio
async def test_chat_trade_cancellation_flow():
    """Test declining a pending trade order."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Initiate trade
        res1 = await client.post(
            "/api/chat",
            json={"message": "Buy 5 shares of MSFT"},
        )
        session_id = res1.json()["session_id"]
        assert "Trade Order Confirmation Required" in res1.json()["response"]

        # Step 2: Reject trade
        res2 = await client.post(
            "/api/chat",
            json={"message": "No, cancel that", "session_id": session_id},
        )
        assert res2.status_code == 200
        assert "cancelled" in res2.json()["response"].lower()


@pytest.mark.asyncio
async def test_chat_trade_insufficient_cash_rejection():
    """Test pre-check failure when cash is insufficient."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/chat",
            json={"message": "Buy 100000 shares of NVDA"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "Trade Validation Failed" in data["response"]
        assert "Insufficient cash" in data["response"]


@pytest.mark.asyncio
async def test_chat_multi_turn_pronoun_resolution():
    """Test pronoun resolution (e.g. 'Analyze Apple' then 'Buy 5 shares of it')."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: Analyze Apple
        res1 = await client.post(
            "/api/chat",
            json={"message": "Analyze Apple"},
        )
        session_id = res1.json()["session_id"]
        assert "AAPL" in res1.json()["response"]

        # Turn 2: Buy shares of "it"
        res2 = await client.post(
            "/api/chat",
            json={"message": "Buy 5 shares of it", "session_id": session_id},
        )
        data2 = res2.json()
        assert "Trade Order Confirmation Required" in data2["response"]
        assert "AAPL" in data2["response"]


@pytest.mark.asyncio
async def test_chat_end_to_end_discovery_pipeline():
    """Test chaining Research -> Analysis -> Investment pipeline."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"message": "Find top tech stories and analyze promising stocks"},
        )
        assert response.status_code == 200
        data = response.json()
        agents_involved = [s["agent"] for s in data["steps"]]
        assert "research" in agents_involved
        assert "analysis" in agents_involved
        assert "investment" in agents_involved
        assert "Executive Investment Discovery Briefing" in data["response"]


@pytest.mark.asyncio
async def test_chat_streaming_endpoint():
    """Test Server-Sent Events (SSE) streaming endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat/stream",
            json={"message": "Analyze MSFT"},
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        events = []
        body_text = response.text
        for line in body_text.splitlines():
            if line.startswith("data: "):
                event_json = line[6:]
                events.append(json.loads(event_json))

        step_events = [e for e in events if e.get("type") == "step"]
        chunk_events = [e for e in events if e.get("type") == "chunk"]
        done_events = [e for e in events if e.get("type") == "done"]

        assert len(step_events) > 0
        assert len(chunk_events) > 0
        assert len(done_events) == 1
        assert "MSFT" in done_events[0]["response"]
