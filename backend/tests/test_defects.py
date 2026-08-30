"""Unit tests verifying fixes for DEF-001 through DEF-009."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.agents.analysis import AnalysisAgent, analysis_agent
from backend.app.agents.investment import InvestmentAgent
from backend.app.agents.manager import ManagerAgent, SessionState
from backend.app.agents.research import ResearchAgent, research_agent
from backend.app.main import app


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


def test_def_006_private_company_word_boundary_and_valid_tickers():
    """DEF-006: Word-boundary matching allows public tickers DIS, V, CAN, RE, OPEN while rejecting private companies."""
    agent = AnalysisAgent()

    # Legitimate public tickers that previously collided with substrings of private companies
    valid_tickers = ["DIS", "V", "CAN", "RE", "OPEN", "Disney", "The Walt Disney Company"]
    for ticker in valid_tickers:
        rejection = agent._check_eligibility(ticker)
        assert rejection is None, f"Expected {ticker} to be eligible, but got rejection: {rejection}"

    # Verify query phrases containing these tickers
    for query in [
        "Analyze DIS fundamentals and moat",
        "Analyze V",
        "Analyze CAN",
        "Analyze RE",
        "Analyze OPEN",
    ]:
        rejection = agent._check_eligibility(query)
        assert rejection is None, f"Expected query '{query}' to be eligible, but got rejection: {rejection}"

    # Verify actual private companies are strictly rejected
    private_companies = [
        "OpenAI", "SpaceX", "Stripe", "ByteDance", "Anthropic",
        "Databricks", "Canva", "Epic Games", "Discord", "Revolut",
        "Plaid", "Valve", "Shein", "$SPACEX", "analyze openai"
    ]
    for priv in private_companies:
        rejection = agent._check_eligibility(priv)
        assert rejection is not None, f"Expected {priv} to be rejected as private company"
        assert "private company" in rejection


@pytest.mark.asyncio
async def test_def_007_subagents_propagate_errors_for_manager_self_healing():
    """DEF-007: Sub-agents do not swallow errors into fake success data, triggering Manager 3x retry self-healing."""
    # 1. AnalysisAgent raises ValueError for non-existent ticker
    with pytest.raises(ValueError):
        analysis_agent._extract_yfinance_metrics_sync("FAKE_NONEXISTENT_TICKER_999")

    # 2. ResearchAgent raises on fetch failure
    with patch.object(research_agent, "fetch_rss_feed", side_effect=ConnectionError("RSS connection failed")):
        with pytest.raises(ConnectionError):
            await research_agent.gather_market_news("market news")

    # 3. Manager self-healing catches analysis failure and attempts 3 retries
    manager = ManagerAgent()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Patch fetch_financial_metrics to simulate 3 failing attempts
        with patch.object(analysis_agent, "fetch_financial_metrics", side_effect=ValueError("No financial data found")):
            res = await client.post("/api/chat", json={"message": "Analyze FAKE_TICKER_XYZ"})
            assert res.status_code == 200
            data = res.json()
            assert "Analysis Agent Execution Failure" in data["response"]
            assert "after 3 automated attempts" in data["response"]
            assert "No financial data found" in data["response"]
            # Verify steps recorded retries
            retry_steps = [s for s in data["steps"] if "Retrying" in s.get("message", "")]
            assert len(retry_steps) >= 2


@pytest.mark.asyncio
async def test_def_008_rss_parser_handles_null_title_and_summary():
    """DEF-008: RSS parser gracefully handles None or missing title and summary without TypeError."""
    agent = ResearchAgent()

    # Unit check for _parse_publisher with None
    title, pub = agent._parse_publisher(None, None)
    assert title == "Untitled Article"
    assert pub == "Google News"

    title2, pub2 = agent._parse_publisher(None, "Custom Publisher")
    assert title2 == "Untitled Article"
    assert pub2 == "Custom Publisher"

    # Unit check for _clean_html with None
    clean_html = agent._clean_html(None)
    assert clean_html == ""

    # Integration test with mocked feedparser returning null fields
    mock_feed = MagicMock()
    mock_feed.entries = [
        {
            "title": None,
            "summary": None,
            "source": {"title": None},
            "link": "https://news.google.com/rss/articles/123",
            "published": None,
        },
        {
            "title": "Fed Holds Benchmark Rates - Reuters",
            "summary": "<p>Federal reserve announcement summary.</p>",
            "source": None,
            "link": "https://news.google.com/rss/articles/456",
            "published": "2026-08-29 12:00:00 UTC",
        }
    ]

    with patch("backend.app.agents.research.httpx.AsyncClient.get") as mock_get, \
         patch("backend.app.agents.research.feedparser.parse", return_value=mock_feed):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.text = "<rss></rss>"
        mock_get.return_value = mock_response

        articles = await agent.fetch_rss_feed()
        assert len(articles) == 2
        assert articles[0]["title"] == "Untitled Article"
        assert articles[0]["publisher"] == "Google News"
        assert articles[0]["summary"] == "Untitled Article"
        assert articles[1]["title"] == "Fed Holds Benchmark Rates"
        assert articles[1]["publisher"] == "Reuters"


@pytest.mark.asyncio
async def test_def_009_trade_eligibility_guardrail_rejects_private_and_non_us():
    """DEF-009: Manager rejects private and non-US stocks before trade confirmation estimate."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Private company trade attempt
        res_spacex = await client.post(
            "/api/chat",
            json={"message": "Buy 10 shares of SpaceX"},
        )
        assert res_spacex.status_code == 200
        data_spacex = res_spacex.json()
        assert "Trade Validation Failed" in data_spacex["response"]
        assert "SpaceX is a private company" in data_spacex["response"]
        assert "Trade Order Confirmation Required" not in data_spacex["response"]

        # Private company trade attempt with Stripe
        res_stripe = await client.post(
            "/api/chat",
            json={"message": "Buy 5 shares of Stripe"},
        )
        assert res_stripe.status_code == 200
        data_stripe = res_stripe.json()
        assert "Trade Validation Failed" in data_stripe["response"]
        assert "Stripe is a private company" in data_stripe["response"]
        assert "Trade Order Confirmation Required" not in data_stripe["response"]

        # Non-US equity trade attempt
        res_foreign = await client.post(
            "/api/chat",
            json={"message": "Buy 100 shares of 0700.HK"},
        )
        assert res_foreign.status_code == 200
        data_foreign = res_foreign.json()
        assert "Trade Validation Failed" in data_foreign["response"]
        assert "non-US or OTC listing" in data_foreign["response"]
        assert "Trade Order Confirmation Required" not in data_foreign["response"]

        # Confirming after a rejected trade should not execute any trade
        session_id = data_spacex["session_id"]
        res_confirm = await client.post(
            "/api/chat",
            json={"message": "yes proceed", "session_id": session_id},
        )
        assert res_confirm.status_code == 200
        assert "Trade Confirmation & Execution" not in res_confirm.json()["response"]

        # Valid US equity trade should proceed to confirmation
        res_valid = await client.post(
            "/api/chat",
            json={"message": "Buy 5 shares of AAPL", "session_id": session_id},
        )
        assert res_valid.status_code == 200
        assert "Trade Order Confirmation Required" in res_valid.json()["response"]
