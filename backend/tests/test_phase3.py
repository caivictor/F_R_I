"""Unit and integration tests for Phase 3: Portfolio Tracking, SQLite Persistence, and Two-Step Execution."""

import os
import tempfile
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.agents.investment import InvestmentAgent, investment_agent
from backend.app.agents.manager import ManagerAgent, manager_agent
from backend.app.db.database import Database
from backend.app.main import app


# ---------------------------------------------------------------------------
# 1. SQLite Database Persistence Layer Tests
# ---------------------------------------------------------------------------

def test_db_initial_bootstrap_state():
    """Verify SQLite database initializes with $100,000 baseline cash and initial transaction."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        test_db = Database(db_path=db_path)
        summary = test_db.get_portfolio_summary()
        assert summary["cash_balance"] == 100000.0
        assert summary["initial_cash"] == 100000.0
        assert summary["realized_pl"] == 0.0
        assert summary["total_deposits"] == 100000.0
        assert summary["total_withdrawals"] == 0.0
        assert summary["total_dividends"] == 0.0

        positions = test_db.get_positions()
        assert len(positions) == 0

        transactions = test_db.get_transactions()
        assert len(transactions) >= 1
        assert transactions[0]["order_type"] == "INITIAL_DEPOSIT"
        assert transactions[0]["total_amount"] == 100000.0
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_db_positions_crud():
    """Verify CRUD operations for asset positions in SQLite database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        test_db = Database(db_path=db_path)
        # Create
        pos = test_db.upsert_position(
            ticker="AAPL",
            name="Apple Inc.",
            shares=10.0,
            avg_cost=180.0,
            total_cost=1800.0,
            cumulative_dividends=0.0,
        )
        assert pos["ticker"] == "AAPL"
        assert pos["shares"] == 10.0
        assert pos["avg_cost"] == 180.0

        # Read
        fetched = test_db.get_position("AAPL")
        assert fetched is not None
        assert fetched["ticker"] == "AAPL"
        assert fetched["shares"] == 10.0

        # Update
        updated = test_db.upsert_position(
            ticker="AAPL",
            name="Apple Inc.",
            shares=20.0,
            avg_cost=185.0,
            total_cost=3700.0,
            cumulative_dividends=25.0,
        )
        assert updated["shares"] == 20.0
        assert updated["total_cost"] == 3700.0
        assert updated["cumulative_dividends"] == 25.0

        # List
        all_positions = test_db.get_positions()
        assert len(all_positions) == 1
        assert all_positions[0]["ticker"] == "AAPL"

        # Delete
        deleted = test_db.delete_position("AAPL")
        assert deleted is True
        assert test_db.get_position("AAPL") is None
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_db_deposit_withdraw_and_reset():
    """Verify cash deposit, withdrawal, and portfolio reset operations on SQLite database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        test_db = Database(db_path=db_path)
        # Deposit
        dep_res = test_db.deposit_cash(amount=5000.0, notes="Bonus deposit")
        assert dep_res["cash_balance"] == 105000.0
        assert dep_res["total_deposits"] == 105000.0

        # Withdraw
        with_res = test_db.withdraw_cash(amount=2000.0, notes="Cash out")
        assert with_res["cash_balance"] == 103000.0
        assert with_res["total_withdrawals"] == 2000.0

        # Excessive withdraw
        with pytest.raises(ValueError):
            test_db.withdraw_cash(amount=200000.0)

        # Negative deposit / withdraw
        with pytest.raises(ValueError):
            test_db.deposit_cash(amount=-50.0)
        with pytest.raises(ValueError):
            test_db.withdraw_cash(amount=0.0)

        # Reset
        reset_res = test_db.reset_portfolio(initial_cash=100000.0)
        assert reset_res["cash_balance"] == 100000.0
        assert reset_res["total_withdrawals"] == 0.0
        assert reset_res["total_dividends"] == 0.0
        assert len(test_db.get_positions()) == 0
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_db_dividend_logging():
    """Verify dividend distributions update cash, cumulative dividends, and transaction log."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        test_db = Database(db_path=db_path)
        test_db.upsert_position(
            ticker="MSFT",
            name="Microsoft Corp.",
            shares=100.0,
            avg_cost=400.0,
            total_cost=40000.0,
            cumulative_dividends=0.0,
        )

        # Record dividend per share
        div_res = test_db.record_dividend(ticker="MSFT", amount_per_share=1.50)
        assert div_res["total_dividend"] == 150.0
        assert div_res["cash_balance"] == 100150.0
        assert div_res["cumulative_dividends"] == 150.0

        # Position cumulative dividend updated
        pos = test_db.get_position("MSFT")
        assert pos["cumulative_dividends"] == 150.0

        # Non-existent position raises error
        with pytest.raises(ValueError):
            test_db.record_dividend(ticker="NONEXISTENT", amount_per_share=2.0)
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


# ---------------------------------------------------------------------------
# 2. Investment Agent Core Functionality Tests
# ---------------------------------------------------------------------------

def test_investment_agent_initial_state():
    """Verify Investment Agent initial state connects to persistent DB."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        test_db = Database(db_path=db_path)
        agent = InvestmentAgent(db_instance=test_db)
        assert agent.get_cash_balance() == 100000.0
        assert agent.get_shares_owned("AAPL") == 0.0
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_investment_agent_estimate_trade():
    """Verify estimate_trade validates cash for buys and shares for sells."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        test_db = Database(db_path=db_path)
        agent = InvestmentAgent(db_instance=test_db)

        # Valid Buy
        est_buy = agent.estimate_trade(action="BUY", ticker="NVDA", quantity=10.0)
        assert est_buy["can_execute"] is True
        assert est_buy["action"] == "BUY"
        assert est_buy["quantity"] == 10.0
        assert est_buy["price_per_share"] > 0
        assert est_buy["total_value"] == est_buy["price_per_share"] * 10.0

        # Excessive Buy (exceeding $100k cash)
        est_excess_buy = agent.estimate_trade(action="BUY", ticker="MSFT", quantity=500.0)
        assert est_excess_buy["can_execute"] is False
        assert "Insufficient cash" in est_excess_buy["reason"]

        # Sell when owning 0 shares
        est_sell_zero = agent.estimate_trade(action="SELL", ticker="AAPL", quantity=5.0)
        assert est_sell_zero["can_execute"] is False
        assert "Insufficient shares" in est_sell_zero["reason"]

        # Invalid zero or negative quantity
        est_zero = agent.estimate_trade(action="BUY", ticker="AAPL", quantity=0.0)
        assert est_zero["can_execute"] is False
        assert "greater than 0" in est_zero["reason"]
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_investment_agent_buy_and_sell_execution():
    """Verify buy and sell trade execution with SQLite database persistence."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        test_db = Database(db_path=db_path)
        agent = InvestmentAgent(db_instance=test_db)

        # 1. Buy 10 shares of NVDA at fixed price $120.00
        buy_res = agent.execute_trade(action="BUY", ticker="NVDA", quantity=10.0, price=120.00)
        assert buy_res["status"] == "success"
        assert buy_res["cash_remaining"] == 100000.0 - 1200.0
        assert agent.get_cash_balance() == 98800.0
        assert agent.get_shares_owned("NVDA") == 10.0

        # Check DB position
        pos = test_db.get_position("NVDA")
        assert pos is not None
        assert pos["shares"] == 10.0
        assert pos["avg_cost"] == 120.0
        assert pos["total_cost"] == 1200.0

        # 2. Buy another 10 shares at $140.00 -> Weighted average cost basis = $130.00
        buy2_res = agent.execute_trade(action="BUY", ticker="NVDA", quantity=10.0, price=140.00)
        assert buy2_res["status"] == "success"
        assert agent.get_cash_balance() == 98800.0 - 1400.0  # 97400.0
        assert agent.get_shares_owned("NVDA") == 20.0

        pos2 = test_db.get_position("NVDA")
        assert pos2["shares"] == 20.0
        assert pos2["avg_cost"] == 130.0
        assert pos2["total_cost"] == 2600.0

        # 3. Sell 5 shares of NVDA at $150.00 -> Realized gain = ($150 - $130) * 5 = $100.00
        sell_res = agent.execute_trade(action="SELL", ticker="NVDA", quantity=5.0, price=150.00)
        assert sell_res["status"] == "success"
        assert sell_res["realized_pl"] == 100.0
        assert agent.get_cash_balance() == 97400.0 + 750.0  # 98150.0
        assert agent.get_shares_owned("NVDA") == 15.0

        summary = test_db.get_portfolio_summary()
        assert summary["realized_pl"] == 100.0

        # 4. Sell remaining 15 shares of NVDA at $160.00 -> Realized gain = ($160 - $130) * 15 = $450.00
        sell_all_res = agent.execute_trade(action="SELL", ticker="NVDA", quantity=15.0, price=160.00)
        assert sell_all_res["status"] == "success"
        assert sell_all_res["realized_pl"] == 450.0
        assert agent.get_shares_owned("NVDA") == 0.0
        assert test_db.get_position("NVDA") is None

        summary2 = test_db.get_portfolio_summary()
        assert summary2["realized_pl"] == 550.0  # 100 + 450
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.mark.asyncio
async def test_investment_agent_portfolio_status_and_valuation():
    """Verify real-time NAV computation, allocation %, and markdown report generation."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        test_db = Database(db_path=db_path)
        agent = InvestmentAgent(db_instance=test_db)

        # Execute sample positions
        agent.execute_trade(action="BUY", ticker="AAPL", quantity=20.0, price=180.00)  # $3600
        agent.execute_trade(action="BUY", ticker="NVDA", quantity=30.0, price=120.00)  # $3600

        status = await agent.get_portfolio_status()
        assert status["status"] == "success"
        assert status["cash_balance"] == 100000.0 - 7200.0
        assert len(status["positions"]) == 2
        assert status["net_asset_value"] > 0
        assert "## Portfolio & Investment Summary" in status["summary_markdown"]
        assert "AAPL" in status["summary_markdown"]
        assert "NVDA" in status["summary_markdown"]
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_investment_agent_transaction_history():
    """Verify transaction history retrieval and markdown table output."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        test_db = Database(db_path=db_path)
        agent = InvestmentAgent(db_instance=test_db)
        agent.deposit_cash(amount=10000.0, notes="Funding deposit")
        agent.execute_trade(action="BUY", ticker="MSFT", quantity=10.0, price=400.0)

        tx_data = agent.get_transaction_history()
        assert tx_data["status"] == "success"
        assert len(tx_data["transactions"]) >= 3  # INITIAL_DEPOSIT, DEPOSIT, BUY
        assert "Transaction & Audit History" in tx_data["summary_markdown"]
        assert "MSFT" in tx_data["summary_markdown"]
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


# ---------------------------------------------------------------------------
# 3. Manager Agent Phase 3 Chat Flows & Two-Step Confirmation Guardrail
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_manager_two_step_trade_confirmation_flow():
    """Verify full 2-step confirmation flow: Intent -> Confirmation Prompt -> Yes -> Executed."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Reset portfolio first to ensure clean state
        await client.post("/api/portfolio/reset", json={"initial_cash": 100000.0})

        # Step 1: Prompt Buy order
        res1 = await client.post("/api/chat", json={"message": "Buy 10 shares of NVDA"})
        assert res1.status_code == 200
        data1 = res1.json()
        session_id = data1["session_id"]
        assert "Trade Order Confirmation Required" in data1["response"]
        assert "Confirm purchase? [Yes / No]" in data1["response"]

        # Step 2: Confirm order with 'yes'
        res2 = await client.post("/api/chat", json={"message": "Yes please proceed", "session_id": session_id})
        assert res2.status_code == 200
        data2 = res2.json()
        assert "Trade Confirmation & Execution" in data2["response"]
        assert "Successfully purchased 10 shares of NVDA" in data2["response"]

        # Verify portfolio status now reflects 10 NVDA shares
        port_res = await client.get("/api/portfolio")
        assert port_res.status_code == 200
        port_data = port_res.json()
        tickers = [p["ticker"] for p in port_data["positions"]]
        assert "NVDA" in tickers


@pytest.mark.asyncio
async def test_manager_trade_cancellation_flow():
    """Verify user declining confirmation cancels trade without modifying portfolio."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Reset
        await client.post("/api/portfolio/reset", json={"initial_cash": 100000.0})

        # Step 1: Prompt Buy order
        res1 = await client.post("/api/chat", json={"message": "Buy 25 shares of AAPL"})
        data1 = res1.json()
        session_id = data1["session_id"]
        assert "Trade Order Confirmation Required" in data1["response"]

        # Step 2: Decline order with 'no'
        res2 = await client.post("/api/chat", json={"message": "No, cancel order", "session_id": session_id})
        data2 = res2.json()
        assert "cancelled" in data2["response"]

        # Verify no AAPL position created
        port_res = await client.get("/api/portfolio")
        port_data = port_res.json()
        tickers = [p["ticker"] for p in port_data["positions"]]
        assert "AAPL" not in tickers


@pytest.mark.asyncio
async def test_manager_cash_commands_via_chat():
    """Verify natural language deposit, withdrawal, reset, and transaction history commands in chat."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Reset command
        res_reset = await client.post("/api/chat", json={"message": "Reset portfolio"})
        assert res_reset.status_code == 200
        assert "Portfolio Reset Complete" in res_reset.json()["response"]

        # Deposit command
        res_dep = await client.post("/api/chat", json={"message": "Deposit $15,000"})
        assert res_dep.status_code == 200
        assert "Cash Deposit Successful" in res_dep.json()["response"]
        assert "$115,000.00" in res_dep.json()["response"]

        # Withdraw command
        res_with = await client.post("/api/chat", json={"message": "Withdraw $5,000"})
        assert res_with.status_code == 200
        assert "Cash Withdrawal Successful" in res_with.json()["response"]
        assert "$110,000.00" in res_with.json()["response"]

        # Transaction history command
        res_tx = await client.post("/api/chat", json={"message": "Show transaction history"})
        assert res_tx.status_code == 200
        assert "Transaction & Audit History" in res_tx.json()["response"]


@pytest.mark.asyncio
async def test_manager_pronoun_multi_turn_trade():
    """Verify pronoun resolution across turns: 'Analyze NVDA' -> 'Buy 10 shares of it'."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: Analyze NVDA
        res1 = await client.post("/api/chat", json={"message": "Analyze NVDA"})
        data1 = res1.json()
        session_id = data1["session_id"]
        assert "Long-Term Investment Dossier" in data1["response"]

        # Turn 2: Trade with pronoun 'it'
        res2 = await client.post("/api/chat", json={"message": "Buy 10 shares of it", "session_id": session_id})
        data2 = res2.json()
        assert "Trade Order Confirmation Required" in data2["response"]
        assert "NVDA" in data2["response"]


# ---------------------------------------------------------------------------
# 4. REST API Endpoints (/api/portfolio)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_portfolio_rest_api_endpoints():
    """Verify all /api/portfolio REST endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Reset
        res_reset = await client.post("/api/portfolio/reset", json={"initial_cash": 100000.0})
        assert res_reset.status_code == 200
        assert res_reset.json()["cash_balance"] == 100000.0

        # 2. Deposit
        res_dep = await client.post("/api/portfolio/deposit", json={"amount": 5000.0, "notes": "API Deposit"})
        assert res_dep.status_code == 200
        assert res_dep.json()["cash_balance"] == 105000.0

        # 3. Withdraw
        res_with = await client.post("/api/portfolio/withdraw", json={"amount": 2500.0, "notes": "API Withdraw"})
        assert res_with.status_code == 200
        assert res_with.json()["cash_balance"] == 102500.0

        # 4. Direct trade BUY
        res_buy = await client.post(
            "/api/portfolio/trade",
            json={"action": "BUY", "ticker": "MSFT", "quantity": 10.0, "price": 400.0},
        )
        assert res_buy.status_code == 200
        assert res_buy.json()["status"] == "success"

        # 5. Dividend
        res_div = await client.post(
            "/api/portfolio/dividend",
            json={"ticker": "MSFT", "amount_per_share": 2.0},
        )
        assert res_div.status_code == 200
        assert res_div.json()["total_dividend"] == 20.0

        # 6. Get Portfolio Status
        res_status = await client.get("/api/portfolio")
        assert res_status.status_code == 200
        data = res_status.json()
        assert data["status"] == "success"
        assert len(data["positions"]) == 1
        assert data["positions"][0]["ticker"] == "MSFT"

        # 7. Get Transactions
        res_tx = await client.get("/api/portfolio/transactions")
        assert res_tx.status_code == 200
        assert len(res_tx.json()["transactions"]) >= 4
