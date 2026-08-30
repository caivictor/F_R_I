"""Unit tests for /api/personas endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.agents.personas import persona_manager


@pytest.mark.asyncio
async def test_get_personas():
    """Test fetching all active and default personas."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/personas")
        assert response.status_code == 200
        data = response.json()
        assert "personas" in data
        assert "defaults" in data
        assert "manager" in data["personas"]
        assert "research" in data["personas"]
        assert "analysis" in data["personas"]
        assert "investment" in data["personas"]


@pytest.mark.asyncio
async def test_update_and_reset_persona():
    """Test updating a specific agent persona and resetting it."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Update research persona
        custom_prompt = "You are a specialized quant research agent focused on high-growth equities."
        res = await client.post("/api/personas", json={"agent": "research", "persona": custom_prompt})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["personas"]["research"] == custom_prompt

        # Verify updated via GET
        get_res = await client.get("/api/personas")
        assert get_res.json()["personas"]["research"] == custom_prompt

        # Test updating an invalid agent
        invalid_res = await client.post("/api/personas", json={"agent": "nonexistent_agent", "persona": "prompt"})
        assert invalid_res.status_code == 400

        # Reset single agent persona
        reset_res = await client.post("/api/personas/reset", json={"agent": "research"})
        assert reset_res.status_code == 200
        assert reset_res.json()["personas"]["research"] == reset_res.json()["personas"]["research"]

        # Reset all personas
        reset_all_res = await client.post("/api/personas/reset", json={})
        assert reset_all_res.status_code == 200
