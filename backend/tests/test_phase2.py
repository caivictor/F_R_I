"""Unit and integration tests for Phase 2: Research, Analysis, and Manager Self-Healing Engine."""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.agents.analysis import AnalysisAgent, analysis_agent
from backend.app.agents.manager import ManagerAgent, manager_agent
from backend.app.agents.research import ResearchAgent, research_agent
from backend.app.main import app


# ---------------------------------------------------------------------------
# 1. Research Agent Tests (Google News RSS, BS4 HTML Clean, Top 3-5 Ranking)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_research_agent_html_cleaning():
    """Verify BeautifulSoup strips HTML tags from news summary snippets."""
    agent = ResearchAgent()
    raw_html = "<ol><li><a href='https://example.com'><b>NVIDIA</b></a> reports record data center revenue.</li></ol>"
    cleaned = agent._clean_html(raw_html)
    assert "<" not in cleaned
    assert ">" not in cleaned
    assert "NVIDIA reports record data center revenue." in cleaned


def test_research_agent_publisher_extraction():
    """Verify publisher parsing from Google News title strings."""
    agent = ResearchAgent()
    title1, pub1 = agent._parse_publisher("Fed Signals Rate Path - Wall Street Journal", None)
    assert title1 == "Fed Signals Rate Path"
    assert pub1 == "Wall Street Journal"

    title2, pub2 = agent._parse_publisher("Tech Rally Continues", "Bloomberg")
    assert title2 == "Tech Rally Continues"
    assert pub2 == "Bloomberg"


@pytest.mark.asyncio
async def test_research_agent_rss_parsing_mock():
    """Verify RSS parsing and metadata extraction on sample feed data."""
    agent = ResearchAgent()
    sample_articles = [
        {
            "title": "NVIDIA Blackwell Ultra Demand Accelerates - Reuters",
            "publisher": "Reuters",
            "url": "https://news.google.com/articles/1",
            "timestamp": "2026-08-29 12:00:00 GMT",
            "summary": "NVIDIA GPU cloud demand outpaces supply across hyperscalers.",
        },
        {
            "title": "Apple Intelligence Expands Services Revenue - WSJ",
            "publisher": "WSJ",
            "url": "https://news.google.com/articles/2",
            "timestamp": "2026-08-29 12:05:00 GMT",
            "summary": "Apple ecosystem monetization drives recurring high-margin subscriptions.",
        },
        {
            "title": "Microsoft Azure Cloud Workloads Surge - Bloomberg",
            "publisher": "Bloomberg",
            "url": "https://news.google.com/articles/3",
            "timestamp": "2026-08-29 12:10:00 GMT",
            "summary": "Microsoft enterprise Copilot adoption fuels commercial seat expansion.",
        },
    ]

    with patch.object(agent, "fetch_rss_feed", new_callable=AsyncMock, return_value=sample_articles):
        result = await agent.gather_market_news()
        assert result["status"] == "success"
        assert len(result["top_companies"]) >= 3
        assert len(result["top_companies"]) <= 5
        tickers = [c["ticker"] for c in result["top_companies"]]
        assert "NVDA" in tickers
        assert "AAPL" in tickers
        assert "MSFT" in tickers
        assert "### Market Intelligence Briefing" in result["summary_markdown"]
        assert "Key Market Themes" in result["summary_markdown"]


def test_research_agent_ranking_batch_cap():
    """Verify ranking enforces the 3 to 5 company batch cap."""
    agent = ResearchAgent()
    articles = [
        {"title": "Tesla Robotaxi Fleet Update - CNBC", "publisher": "CNBC", "url": "https://...", "timestamp": "...", "summary": "Tesla TSLA unveils fleet."},
        {"title": "Meta Open Source AI Models - TechCrunch", "publisher": "TechCrunch", "url": "https://...", "timestamp": "...", "summary": "Meta releases Llama next-gen."},
        {"title": "Amazon AWS Cloud Capex - WSJ", "publisher": "WSJ", "url": "https://...", "timestamp": "...", "summary": "Amazon AMZN expands data centers."},
        {"title": "Alphabet Google DeepMind Advancements - Verge", "publisher": "Verge", "url": "https://...", "timestamp": "...", "summary": "Google GOOGL search integration."},
        {"title": "NVIDIA GPU Shipment Milestones - Reuters", "publisher": "Reuters", "url": "https://...", "timestamp": "...", "summary": "NVDA ships next generation."},
        {"title": "Palantir Enterprise Contract Wins - Barron's", "publisher": "Barron's", "url": "https://...", "timestamp": "...", "summary": "PLTR wins government AIP deal."},
    ]

    ranked = agent.rank_prominent_companies(articles, limit=5)
    assert len(ranked) == 5
    assert len(ranked) >= 3
    assert len(ranked) <= 5


@pytest.mark.asyncio
async def test_research_agent_empty_feed_fallback():
    """Verify Research Agent returns structured briefing with fallback leaders when feed has no articles."""
    agent = ResearchAgent()
    with patch.object(agent, "fetch_rss_feed", return_value=[]):
        result = await agent.gather_market_news()
        assert result["status"] == "success"
        assert len(result["top_companies"]) >= 3
        assert "Market Intelligence Briefing" in result["summary_markdown"]


@pytest.mark.asyncio
async def test_research_agent_exception_propagates_for_self_healing():
    """Verify Research Agent raises exception on network failure so Manager self-healing can retry."""
    agent = ResearchAgent()
    with patch.object(agent, "fetch_rss_feed", side_effect=ConnectionError("Network unreachable")):
        with pytest.raises(ConnectionError):
            await agent.gather_market_news()


# ---------------------------------------------------------------------------
# 2. Analysis Agent Tests (yfinance Metrics, Guardrails, Previous Close)
# ---------------------------------------------------------------------------

def test_analysis_agent_private_company_guardrail():
    """Verify strict rejection of private companies per PRD guardrails."""
    agent = AnalysisAgent()
    for priv in ["OpenAI", "SpaceX", "Stripe", "ByteDance", "Anthropic", "Databricks", "Canva", "Epic Games", "Discord"]:
        rejection = agent._check_eligibility(priv)
        assert rejection is not None
        assert "Analysis Rejection" in rejection
        assert "private company" in rejection


def test_analysis_agent_non_us_otc_guardrail():
    """Verify rejection of non-US exchanges and OTC symbols."""
    agent = AnalysisAgent()
    for symbol in ["TCEHY.PK", "BABA.OB", "0700.HK", "RY.TO", "NESN.SW", "VOW3.DE"]:
        rejection = agent._check_eligibility(symbol)
        assert rejection is not None
        assert "Analysis Rejection" in rejection
        assert "non-US" in rejection or "OTC" in rejection


def test_analysis_agent_ticker_resolution():
    """Verify resolving aliases and cleaning prompt phrases to tickers."""
    agent = AnalysisAgent()
    assert agent._resolve_ticker("Analyze Apple fundamentals") == "AAPL"
    assert agent._resolve_ticker("Microsoft and moat") == "MSFT"
    assert agent._resolve_ticker("NVIDIA") == "NVDA"
    assert agent._resolve_ticker("$AMZN") == "AMZN"
    assert agent._resolve_ticker("Google") == "GOOGL"


@pytest.mark.asyncio
async def test_analysis_agent_metrics_computation():
    """Verify extraction and calculation of all PRD required financial metrics."""
    agent = AnalysisAgent()

    mock_info = {
        "shortName": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "currency": "USD",
        "currentPrice": 220.00,
        "previousClose": 218.50,
        "marketCap": 3300000000000,
        "returnOnEquity": 1.45,
        "grossMargins": 0.46,
        "operatingMargins": 0.31,
        "freeCashflow": 105000000000,
        "debtToEquity": 140.0,
        "currentRatio": 1.05,
        "quickRatio": 0.85,
        "revenueGrowth": 0.08,
        "trailingPE": 33.5,
        "forwardPE": 29.0,
        "pegRatio": 2.4,
        "enterpriseToEbitda": 25.0,
        "dividendYield": 0.005,
    }

    mock_ticker_obj = MagicMock()
    mock_ticker_obj.info = mock_info
    mock_ticker_obj.fast_info = None
    mock_ticker_obj.financials = None

    with patch("yfinance.Ticker", return_value=mock_ticker_obj):
        data = agent._extract_yfinance_metrics_sync("AAPL")
        assert data["ticker"] == "AAPL"
        assert data["name"] == "Apple Inc."
        assert data["current_price"] == 220.00
        assert data["previous_close"] == 218.50
        assert data["market_cap"] == "$3.30T"
        assert data["roe"] == "145.0%"
        assert data["gross_margin"] == "46.0%"
        assert data["operating_margin"] == "31.0%"
        assert data["fcf"] == "$105.00B"
        assert "3.2%" in data["fcf_yield"]
        assert data["debt_to_equity"] == "1.40x"
        assert data["current_ratio"] == "1.05x"
        assert data["quick_ratio"] == "0.85x"
        assert data["trailing_pe"] == "33.5x"
        assert data["forward_pe"] == "29.0x"
        assert data["peg_ratio"] == "2.40x"


@pytest.mark.asyncio
async def test_analysis_agent_off_hours_previous_close_pricing():
    """Verify previous close pricing is used when real-time quote is unavailable (off-hours)."""
    agent = AnalysisAgent()

    mock_info = {
        "shortName": "Tesla, Inc.",
        "currency": "USD",
        "currentPrice": None,
        "regularMarketPrice": None,
        "previousClose": 215.00,
        "regularMarketPreviousClose": 215.00,
        "marketCap": 700000000000,
        "returnOnEquity": 0.20,
    }

    mock_ticker_obj = MagicMock()
    mock_ticker_obj.info = mock_info
    mock_ticker_obj.fast_info = None

    with patch("yfinance.Ticker", return_value=mock_ticker_obj):
        data = agent._extract_yfinance_metrics_sync("TSLA")
        assert data["current_price"] == 215.00
        assert data["previous_close"] == 215.00


@pytest.mark.asyncio
async def test_analysis_agent_dossier_markdown_format():
    """Verify Long-Term Investment Dossier markdown format and sections."""
    agent = AnalysisAgent()
    result = await agent.analyze_company("NVDA")
    assert result["status"] == "success"
    assert result["is_eligible"] is True
    md = result["summary_markdown"]
    assert "## Long-Term Investment Dossier" in md
    assert "Financial Health Scorecard" in md
    assert "Economic Moat & Competitive Advantage" in md
    assert "Long-Term Investment Thesis" in md
    assert "Bull vs. Bear Risk Assessment" in md


# ---------------------------------------------------------------------------
# 3. Manager Agent Self-Healing Engine (3x Retry, Dynamic Adaptation)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_manager_self_healing_retry_recovers_on_second_attempt():
    """Verify Manager retries failed sub-agent task and recovers on attempt 2."""
    manager = ManagerAgent()
    call_count = 0

    async def flaky_task(param: Any) -> dict:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise TimeoutError("External request timeout")
        return {"status": "success", "data": f"Success on param: {param}"}

    steps: list = []
    success, result = await manager._execute_subagent_with_healing(
        agent_name="research",
        task_func=flaky_task,
        initial_param="raw query",
        progress_callback=None,
        steps_accumulator=steps,
        max_attempts=3,
    )

    assert success is True
    assert call_count == 2
    assert result["status"] == "success"
    assert any("Retrying (2/3)" in s["message"] for s in steps)


@pytest.mark.asyncio
async def test_manager_self_healing_exhausts_3_retries_graceful_error():
    """Verify Manager retries 3 times before returning graceful error report."""
    manager = ManagerAgent()
    call_count = 0

    async def failing_task(param: Any) -> dict:
        nonlocal call_count
        call_count += 1
        raise ConnectionError("Service unreachable")

    steps: list = []
    success, result = await manager._execute_subagent_with_healing(
        agent_name="analysis",
        task_func=failing_task,
        initial_param="XYZ",
        progress_callback=None,
        steps_accumulator=steps,
        max_attempts=3,
    )

    assert success is False
    assert call_count == 3
    assert result["status"] == "failed"
    assert "Execution failed after 3 attempts" in result["reason"]
    assert any("failed after 3 attempts" in s["message"] for s in steps)


@pytest.mark.asyncio
async def test_manager_process_message_with_self_healing_failure():
    """Verify Manager handles complete sub-agent failure gracefully in chat response."""
    manager = ManagerAgent()
    with patch.object(
        manager,
        "_execute_subagent_with_healing",
        new_callable=AsyncMock,
        return_value=(False, {"reason": "Persistent network timeout after 3 attempts."}),
    ):
        result = await manager.process_message("What is the latest market news?")
        assert "Execution Failure" in result["response"]
        assert "Persistent network timeout" in result["response"]
        assert "Action Required" in result["response"]


# ---------------------------------------------------------------------------
# 4. End-to-End Multi-Agent Discovery & Integration
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_phase2_e2e_research_to_analysis_pipeline():
    """Verify End-to-End discovery chains Research -> Analysis -> Investment."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"message": "Discover top tech stories and analyze promising stocks"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "Executive Investment Discovery Briefing" in data["response"]
        assert "Market Research Findings" in data["response"]
        assert "Quantitative & Fundamental Analysis" in data["response"]
        assert "Portfolio Allocation & Capital Capacity" in data["response"]
        
        agents_involved = [s["agent"] for s in data["steps"]]
        assert "research" in agents_involved
        assert "analysis" in agents_involved
        assert "investment" in agents_involved
