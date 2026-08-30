"""SQLite database layer for F.R.I. portfolio, positions, transactions, and personas."""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from backend.app.config import settings

DEFAULT_PERSONAS_DB: Dict[str, str] = {
    "manager": (
        "You are the Manager Agent for F.R.I. (Financial Research & Investment). "
        "You serve as the master orchestrator, user interface proxy, and supervisor. "
        "Your responsibilities include:\n"
        "1. Intelligently routing user requests to specialized sub-agents: Research Agent (market & news discovery), "
        "Analysis Agent (company & fundamental analysis), and Investment Agent (portfolio status & trade execution).\n"
        "2. Enforcing a strict 2-step confirmation guardrail for any buy or sell trade order.\n"
        "3. Resolving conversational references and pronouns across multi-turn sessions.\n"
        "4. Synthesizing sub-agent findings into concise, structured executive summaries.\n"
        "5. Communicating transparently with step-by-step progress updates."
    ),
    "research": (
        "You are the Research Agent for F.R.I. (Financial Research & Investment). "
        "Your role is the Financial Data & News Gatherer. You gather market news from Google News Business RSS, "
        "extract critical metadata (title, publisher, timestamp, summary snippet, url), and filter the top 3 to 5 "
        "most prominent US public companies and market themes."
    ),
    "analysis": (
        "You are the Analysis Agent for F.R.I. (Financial Research & Investment). "
        "Your role is Quantitative & Fundamental Equity Analyst. "
        "Guardrails: strictly analyze US-listed public equities (NYSE/NASDAQ) trading in USD. "
        "Reject requests for private companies (such as OpenAI, SpaceX, Stripe) and non-US OTC listings. "
        "Evaluate long-term compounding potential using ROIC, ROE, Free Cash Flow, Debt-to-Equity, P/E, PEG, "
        "and produce a structured Long-Term Investment Dossier in Markdown."
    ),
    "investment": (
        "You are the Investment Agent for F.R.I. (Financial Research & Investment). "
        "Your role is Portfolio Manager & Execution Engine. You track paper trading positions, cash reserves "
        "(starting balance $100,000.00 USD), Net Asset Value (NAV), profit/loss, and maintain transaction logs. "
        "You validate cash sufficiency for buy orders and position quantities for sell orders."
    ),
}


class Database:
    """SQLite Database manager handling persistence for F.R.I."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path: str = db_path if db_path is not None else settings.DATABASE_PATH
        self._ensure_db_dir()
        self.init_db()

    def _ensure_db_dir(self) -> None:
        """Ensure the parent directory of the database file exists."""
        if self.db_path != ":memory:":
            path = Path(self.db_path)
            if not path.is_absolute():
                path = Path.cwd() / path
            path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager yielding a SQLite connection configured with Row factory, WAL mode, and busy timeout."""
        conn = sqlite3.connect(self.db_path, timeout=5.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self) -> None:
        """Create tables if they do not exist and seed initial state."""
        self._ensure_db_dir()
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Portfolio summary table (single-row baseline)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_summary (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    cash_balance REAL NOT NULL DEFAULT 100000.0,
                    initial_cash REAL NOT NULL DEFAULT 100000.0,
                    realized_pl REAL NOT NULL DEFAULT 0.0,
                    total_deposits REAL NOT NULL DEFAULT 100000.0,
                    total_withdrawals REAL NOT NULL DEFAULT 0.0,
                    total_dividends REAL NOT NULL DEFAULT 0.0,
                    updated_at TEXT NOT NULL
                )
            """)

            # 2. Positions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    ticker TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    shares REAL NOT NULL DEFAULT 0.0,
                    avg_cost REAL NOT NULL DEFAULT 0.0,
                    total_cost REAL NOT NULL DEFAULT 0.0,
                    cumulative_dividends REAL NOT NULL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # 3. Transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    order_type TEXT NOT NULL,
                    ticker TEXT,
                    shares REAL DEFAULT 0.0,
                    price REAL DEFAULT 0.0,
                    total_amount REAL NOT NULL,
                    realized_pl REAL DEFAULT 0.0,
                    notes TEXT
                )
            """)

            # 4. Agent Personas table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_personas (
                    agent TEXT PRIMARY KEY,
                    persona TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Seed portfolio summary if empty ($100,000 baseline)
            cursor.execute("SELECT COUNT(*) FROM portfolio_summary")
            if cursor.fetchone()[0] == 0:
                now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                cursor.execute("""
                    INSERT INTO portfolio_summary (
                        id, cash_balance, initial_cash, realized_pl, total_deposits, total_withdrawals, total_dividends, updated_at
                    ) VALUES (1, 100000.0, 100000.0, 0.0, 100000.0, 0.0, 0.0, ?)
                """, (now_str,))

                cursor.execute("""
                    INSERT INTO transactions (
                        timestamp, order_type, ticker, shares, price, total_amount, realized_pl, notes
                    ) VALUES (?, 'INITIAL_DEPOSIT', '-', 0.0, 0.0, 100000.0, 0.0, 'Paper trading account bootstrap baseline')
                """, (now_str,))

            # Seed agent personas if empty
            cursor.execute("SELECT COUNT(*) FROM agent_personas")
            if cursor.fetchone()[0] == 0:
                now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                for agent_name, prompt in DEFAULT_PERSONAS_DB.items():
                    cursor.execute("""
                        INSERT OR REPLACE INTO agent_personas (agent, persona, updated_at)
                        VALUES (?, ?, ?)
                    """, (agent_name, prompt, now_str))

    # --- Portfolio Summary Operations ---

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Fetch the current portfolio summary row."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM portfolio_summary WHERE id = 1")
            row = cursor.fetchone()
            if row:
                return dict(row)
            # Re-init if missing
            self.init_db()
            cursor.execute("SELECT * FROM portfolio_summary WHERE id = 1")
            return dict(cursor.fetchone())

    def update_portfolio_summary(
        self,
        cash_balance: Optional[float] = None,
        realized_pl: Optional[float] = None,
        total_deposits: Optional[float] = None,
        total_withdrawals: Optional[float] = None,
        total_dividends: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Update fields in the portfolio summary table."""
        current = self.get_portfolio_summary()
        new_cash = cash_balance if cash_balance is not None else current["cash_balance"]
        new_realized = realized_pl if realized_pl is not None else current["realized_pl"]
        new_deposits = total_deposits if total_deposits is not None else current["total_deposits"]
        new_withdrawals = total_withdrawals if total_withdrawals is not None else current["total_withdrawals"]
        new_dividends = total_dividends if total_dividends is not None else current["total_dividends"]
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE portfolio_summary
                SET cash_balance = ?,
                    realized_pl = ?,
                    total_deposits = ?,
                    total_withdrawals = ?,
                    total_dividends = ?,
                    updated_at = ?
                WHERE id = 1
            """, (new_cash, new_realized, new_deposits, new_withdrawals, new_dividends, now_str))

        return self.get_portfolio_summary()

    def reset_portfolio(self, initial_cash: float = 100000.0) -> Dict[str, Any]:
        """Reset the portfolio back to the initial cash baseline and clear positions."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM positions")
            cursor.execute("""
                UPDATE portfolio_summary
                SET cash_balance = ?,
                    initial_cash = ?,
                    realized_pl = 0.0,
                    total_deposits = ?,
                    total_withdrawals = 0.0,
                    total_dividends = 0.0,
                    updated_at = ?
                WHERE id = 1
            """, (initial_cash, initial_cash, initial_cash, now_str))

            cursor.execute("""
                INSERT INTO transactions (
                    timestamp, order_type, ticker, shares, price, total_amount, realized_pl, notes
                ) VALUES (?, 'RESET', '-', 0.0, 0.0, ?, 0.0, 'Portfolio reset to initial baseline')
            """, (now_str, initial_cash))

        return self.get_portfolio_summary()

    def deposit_cash(self, amount: float, notes: str = "") -> Dict[str, Any]:
        """Deposit cash into the paper trading portfolio."""
        if amount <= 0:
            raise ValueError(f"Deposit amount must be greater than 0 (received {amount}).")
        summary = self.get_portfolio_summary()
        new_cash = summary["cash_balance"] + amount
        new_deposits = summary["total_deposits"] + amount
        self.update_portfolio_summary(cash_balance=new_cash, total_deposits=new_deposits)
        tx = self.record_transaction(
            order_type="DEPOSIT",
            total_amount=amount,
            ticker="-",
            notes=notes or f"Cash deposit of ${amount:,.2f}",
        )
        return {
            "status": "success",
            "amount": amount,
            "cash_balance": new_cash,
            "total_deposits": new_deposits,
            "transaction": tx,
        }

    def withdraw_cash(self, amount: float, notes: str = "") -> Dict[str, Any]:
        """Withdraw cash from the paper trading portfolio."""
        if amount <= 0:
            raise ValueError(f"Withdrawal amount must be greater than 0 (received {amount}).")
        summary = self.get_portfolio_summary()
        if summary["cash_balance"] < amount:
            raise ValueError(
                f"Insufficient cash for withdrawal: requested ${amount:,.2f}, available ${summary['cash_balance']:,.2f}."
            )
        new_cash = summary["cash_balance"] - amount
        new_withdrawals = summary["total_withdrawals"] + amount
        self.update_portfolio_summary(cash_balance=new_cash, total_withdrawals=new_withdrawals)
        tx = self.record_transaction(
            order_type="WITHDRAW",
            total_amount=amount,
            ticker="-",
            notes=notes or f"Cash withdrawal of ${amount:,.2f}",
        )
        return {
            "status": "success",
            "amount": amount,
            "cash_balance": new_cash,
            "total_withdrawals": new_withdrawals,
            "transaction": tx,
        }

    def record_dividend(
        self,
        ticker: str,
        amount_per_share: Optional[float] = None,
        total_amount: Optional[float] = None,
        notes: str = "",
    ) -> Dict[str, Any]:
        """Log dividend distribution income for an equity holding."""
        cleaned = ticker.strip().upper()
        pos = self.get_position(cleaned)
        if pos is None:
            raise ValueError(f"Cannot record dividend: position '{cleaned}' not found in portfolio.")

        if total_amount is None:
            if amount_per_share is None or amount_per_share <= 0:
                raise ValueError("Must provide either amount_per_share > 0 or total_amount > 0.")
            div_total = float(pos["shares"]) * float(amount_per_share)
            div_per_share = float(amount_per_share)
        else:
            if total_amount <= 0:
                raise ValueError(f"Dividend total amount must be greater than 0 (received {total_amount}).")
            div_total = float(total_amount)
            div_per_share = div_total / pos["shares"] if pos["shares"] > 0 else 0.0

        summary = self.get_portfolio_summary()
        new_cash = summary["cash_balance"] + div_total
        new_total_div = summary["total_dividends"] + div_total
        self.update_portfolio_summary(cash_balance=new_cash, total_dividends=new_total_div)

        new_cum_div = pos["cumulative_dividends"] + div_total
        self.upsert_position(
            ticker=cleaned,
            name=pos["name"],
            shares=pos["shares"],
            avg_cost=pos["avg_cost"],
            total_cost=pos["total_cost"],
            cumulative_dividends=new_cum_div,
        )

        tx = self.record_transaction(
            order_type="DIVIDEND",
            total_amount=div_total,
            ticker=cleaned,
            shares=pos["shares"],
            price=div_per_share,
            notes=notes or f"Dividend received for {cleaned}: ${div_total:,.2f} (${div_per_share:.2f}/share)",
        )
        return {
            "status": "success",
            "ticker": cleaned,
            "amount_per_share": div_per_share,
            "total_dividend": div_total,
            "cumulative_dividends": new_cum_div,
            "cash_balance": new_cash,
            "transaction": tx,
        }

    # --- Position Operations ---

    def get_positions(self) -> List[Dict[str, Any]]:
        """Retrieve all active positions from the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM positions ORDER BY ticker ASC")
            return [dict(row) for row in cursor.fetchall()]

    def get_position(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific position by ticker symbol."""
        cleaned = ticker.strip().upper()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM positions WHERE ticker = ?", (cleaned,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def upsert_position(
        self,
        ticker: str,
        name: str,
        shares: float,
        avg_cost: float,
        total_cost: float,
        cumulative_dividends: float = 0.0,
    ) -> Dict[str, Any]:
        """Insert or update an equity position record."""
        cleaned = ticker.strip().upper()
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM positions WHERE ticker = ?", (cleaned,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("""
                    UPDATE positions
                    SET name = ?,
                        shares = ?,
                        avg_cost = ?,
                        total_cost = ?,
                        cumulative_dividends = ?,
                        updated_at = ?
                    WHERE ticker = ?
                """, (name, shares, avg_cost, total_cost, cumulative_dividends, now_str, cleaned))
            else:
                cursor.execute("""
                    INSERT INTO positions (
                        ticker, name, shares, avg_cost, total_cost, cumulative_dividends, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (cleaned, name, shares, avg_cost, total_cost, cumulative_dividends, now_str, now_str))

        return self.get_position(cleaned) or {}

    def delete_position(self, ticker: str) -> bool:
        """Delete a position record by ticker symbol."""
        cleaned = ticker.strip().upper()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM positions WHERE ticker = ?", (cleaned,))
            return cursor.rowcount > 0

    # --- Transaction Log Operations ---

    def record_transaction(
        self,
        order_type: str,
        total_amount: float,
        ticker: Optional[str] = None,
        shares: float = 0.0,
        price: float = 0.0,
        realized_pl: float = 0.0,
        notes: str = "",
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log a trade, deposit, withdrawal, dividend, or reset transaction."""
        now_str = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        cleaned_ticker = ticker.strip().upper() if ticker else "-"
        cleaned_type = order_type.strip().upper()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions (
                    timestamp, order_type, ticker, shares, price, total_amount, realized_pl, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (now_str, cleaned_type, cleaned_ticker, shares, price, total_amount, realized_pl, notes))
            tx_id = cursor.lastrowid

            cursor.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,))
            return dict(cursor.fetchone())

    def get_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve recent transaction history ordered by timestamp descending."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # --- Agent Persona Persistence Operations ---

    def get_persona(self, agent: str) -> Optional[str]:
        """Fetch custom persona prompt for an agent from the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT persona FROM agent_personas WHERE agent = ?", (agent.lower(),))
            row = cursor.fetchone()
            return row["persona"] if row else None

    def get_all_personas(self) -> Dict[str, str]:
        """Fetch all stored agent personas."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT agent, persona FROM agent_personas")
            rows = cursor.fetchall()
            return {row["agent"]: row["persona"] for row in rows}

    def save_persona(self, agent: str, persona: str) -> bool:
        """Persist a persona prompt for an agent."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO agent_personas (agent, persona, updated_at)
                VALUES (?, ?, ?)
            """, (agent.lower(), persona, now_str))
            return True

    def reset_personas(self, agent: Optional[str] = None) -> None:
        """Reset agent persona(s) back to default in the database."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if agent:
                agent_key = agent.lower()
                if agent_key in DEFAULT_PERSONAS_DB:
                    cursor.execute("""
                        INSERT OR REPLACE INTO agent_personas (agent, persona, updated_at)
                        VALUES (?, ?, ?)
                    """, (agent_key, DEFAULT_PERSONAS_DB[agent_key], now_str))
            else:
                for a_name, prompt in DEFAULT_PERSONAS_DB.items():
                    cursor.execute("""
                        INSERT OR REPLACE INTO agent_personas (agent, persona, updated_at)
                        VALUES (?, ?, ?)
                    """, (a_name, prompt, now_str))


db = Database()
