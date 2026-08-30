"""Unit tests verifying fixes for DEF-001 through DEF-005."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.agents.investment import InvestmentAgent
from backend.app.agents.manager import ManagerAgent, SessionState


@pytest.mark.asyncio
async def test_def_001_word_boundary_confirmation_and_unrelated_invalidation():
    """DEF-001: Strict regex word-boundary matching and clearing pending_trade on unrelated queries."""
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

        # Step 2: Send query with 'ok' as substring in 'tokenomics' - must NOT confirm trade and should clear pending
        res2 = await client.post(
            "/api/chat",
            json={"message": "Is tokenomics important for valuation?", "session_id": session_id},
        )
        assert res2.status_code == 200
        data2 = res2.json()
        # Must not have executed trade
        assert "Trade Confirmation & Execution" not in data2["response"]

        # Step 3: Now send "ok thank you" - should NOT execute the pending trade since it was invalidated
        res3 = await client.post(
            "/api/chat",
            json={"message": "ok thank you", "session_id": session_id},
        )
        assert res3.status_code == 200
        data3 = res3.json()
        assert "Trade Confirmation & Execution" not in data3["response"]

        # Step 4: Verify normal explicit confirmation works when pending
        res4 = await client.post(
            "/api/chat",
            json={"message": "Buy 5 shares of AAPL", "session_id": session_id},
        )
        assert "Trade Order Confirmation Required" in res4.json()["response"]

        res5 = await client.post(
            "/api/chat",
            json={"message": "yes proceed", "session_id": session_id},
        )
        assert res5.status_code == 200
        assert "Trade Confirmation & Execution" in res5.json()["response"]


@pytest.mark.asyncio
async def test_def_002_zero_quantity_trade_rejected_and_cash_reported():
    """DEF-002: Ensure quantity > 0 in trade validation, failed trades report actual cash balance."""
    inv = InvestmentAgent()

    # Pre-validation for 0 quantity
    estimate_zero = inv.estimate_trade("SELL", "TSLA", 0)
    assert not estimate_zero["can_execute"]
    assert "greater than 0" in estimate_zero["reason"]

    # Pre-validation for negative quantity
    estimate_neg = inv.estimate_trade("BUY", "AAPL", -5)
    assert not estimate_neg["can_execute"]
    assert "greater than 0" in estimate_neg["reason"]

    # Execution failure reporting actual cash balance
    exec_zero = inv.execute_trade("SELL", "TSLA", 0)
    assert exec_zero["status"] == "error"
    assert exec_zero["cash_remaining"] == inv.get_cash_balance()
    assert exec_zero["cash_remaining"] > 0

    # API chat test: "Sell 0 shares of TSLA" must fail validation and not prompt confirmation
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/chat",
            json={"message": "Sell 0 shares of TSLA"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "Trade Validation Failed" in data["response"]
        assert "greater than 0" in data["response"]
        assert "Trade Order Confirmation Required" not in data["response"]


@pytest.mark.asyncio
async def test_def_003_zero_nav_calculation_no_zero_division():
    """DEF-003: Check if net_asset_value == 0 before division in investment.py get_portfolio_status."""
    inv = InvestmentAgent()
    # Simulate zero cash balance and zero active stock holdings
    inv._cash_balance = 0.0
    inv._positions = {}
    inv._initial_cash = 0.0

    status = await inv.get_portfolio_status()
    assert status["status"] == "success"
    assert status["net_asset_value"] == 0.0
    assert status["cash_balance"] == 0.0
    assert "0.00% of portfolio" in status["summary_markdown"]


@pytest.mark.asyncio
async def test_def_004_persona_validation_bounds_and_agent_names():
    """DEF-004: Validate agent name and persona string length (10 to 10000 chars) in routers/personas.py with HTTP 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Empty persona string
        res_empty = await client.post(
            "/api/personas",
            json={"agent": "manager", "persona": ""},
        )
        assert res_empty.status_code == 400
        assert "between 10 and 10,000" in res_empty.json()["detail"]

        # Persona string shorter than 10 characters
        res_short = await client.post(
            "/api/personas",
            json={"agent": "manager", "persona": "too short"},
        )
        assert res_short.status_code == 400
        assert "between 10 and 10,000" in res_short.json()["detail"]

        # Persona string exceeding 10,000 characters
        res_large = await client.post(
            "/api/personas",
            json={"agent": "manager", "persona": "A" * 10001},
        )
        assert res_large.status_code == 400
        assert "between 10 and 10,000" in res_large.json()["detail"]

        # Invalid agent name
        res_invalid_agent = await client.post(
            "/api/personas",
            json={"agent": "nonexistent_bot", "persona": "This is a valid length persona text."},
        )
        assert res_invalid_agent.status_code == 400
        assert "Unknown agent" in res_invalid_agent.json()["detail"]

        # Invalid agent on reset
        res_reset_invalid = await client.post(
            "/api/personas/reset",
            json={"agent": "invalid_agent"},
        )
        assert res_reset_invalid.status_code == 400
        assert "Unknown agent" in res_reset_invalid.json()["detail"]

        # Valid persona update
        valid_prompt = "You are an expert Manager Agent with deep investment knowledge."
        res_valid = await client.post(
            "/api/personas",
            json={"agent": "manager", "persona": valid_prompt},
        )
        assert res_valid.status_code == 200
        assert res_valid.json()["personas"]["manager"] == valid_prompt

        # Clean up by resetting manager
        res_reset = await client.post(
            "/api/personas/reset",
            json={"agent": "manager"},
        )
        assert res_reset.status_code == 200


def test_def_005_pronoun_resolution_regex_special_characters():
    """DEF-005: Use re.escape or string replace / callable in _resolve_entities_and_pronouns in manager.py."""
    mgr = ManagerAgent()
    session = SessionState(session_id="test_session")

    # Ticker containing backslash group references like \99, \g<1>, etc.
    session.last_ticker = r"\99_SPECIAL_\g<1>"

    # Should not raise re.PatternError
    resolved = mgr._resolve_entities_and_pronouns("What is its balance and should I buy it?", session)
    assert r"\99_SPECIAL_\g<1>" in resolved

    # Also test trade parameter extraction with this ticker
    session.last_ticker = r"NVDA"
    resolved_trade = mgr._resolve_entities_and_pronouns("Buy 10 shares of it", session)
    assert "NVDA" in resolved_trade
