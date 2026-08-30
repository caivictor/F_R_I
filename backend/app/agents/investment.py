"""Investment sub-agent for portfolio tracking and paper trade execution with SQLite persistence."""

import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import yfinance as yf

from backend.app.agents.personas import persona_manager
from backend.app.db.database import Database, db


class InvestmentAgent:
    """Portfolio Manager & Execution Engine sub-agent backed by SQLite persistence."""

    def __init__(self, db_instance: Optional[Database] = None) -> None:
        self._db: Database = db_instance if db_instance is not None else db
        self._cash_balance: Optional[float] = None
        self._positions: Optional[Dict[str, Dict[str, Any]]] = None
        self._initial_cash: Optional[float] = None

    def get_persona(self) -> str:
        """Get the current persona prompt for Investment Agent."""
        return persona_manager.get_persona("investment")

    def get_cash_balance(self) -> float:
        """Get the current cash reserve balance from the SQLite database or in-memory override."""
        if self._cash_balance is not None:
            return float(self._cash_balance)
        summary = self._db.get_portfolio_summary()
        return float(summary.get("cash_balance", 100000.0))

    def get_shares_owned(self, ticker: str) -> float:
        """Get current shares owned for a ticker from the SQLite database or in-memory override."""
        cleaned = ticker.strip().upper()
        if self._positions is not None:
            return float(self._positions.get(cleaned, {}).get("shares", 0.0))
        pos = self._db.get_position(cleaned)
        return float(pos["shares"]) if pos else 0.0

    def get_quote(self, ticker: str) -> float:
        """Get the latest market price or fallback for a ticker."""
        cleaned = ticker.strip().upper()

        # Try yfinance real-time quote / previous close
        try:
            ticker_obj = yf.Ticker(cleaned)
            info = getattr(ticker_obj, "info", None) or {}
            regular_price = info.get("currentPrice") or info.get("regularMarketPrice")
            previous_close = info.get("previousClose")

            fast_info = getattr(ticker_obj, "fast_info", None)
            if regular_price is None and fast_info:
                regular_price = getattr(fast_info, "last_price", None)
            if previous_close is None and fast_info:
                previous_close = getattr(fast_info, "previous_close", None)

            price = regular_price if regular_price is not None else previous_close
            if price is not None and float(price) > 0:
                return float(price)
        except Exception:
            pass

        # Fallback dictionary for common stocks / offline testing
        fallback_quotes = {
            "AAPL": 185.50,
            "NVDA": 125.00,
            "MSFT": 420.00,
            "AMZN": 180.00,
            "GOOGL": 165.00,
            "TSLA": 210.00,
            "META": 490.00,
            "PLTR": 32.00,
            "DIS": 115.00,
            "AMD": 160.00,
            "AVGO": 170.00,
            "CRM": 290.00,
            "ORCL": 140.00,
            "WMT": 75.00,
            "JPM": 215.00,
        }
        return float(fallback_quotes.get(cleaned, 100.00))

    def estimate_trade(
        self,
        action: str,
        ticker: str,
        quantity: float,
        price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Calculate trade cost, check affordability/shares, and prepare confirmation parameters."""
        cleaned_ticker = ticker.strip().upper()
        action_type = action.strip().upper()
        exec_price = price if price is not None else self.get_quote(cleaned_ticker)

        cash_available = self.get_cash_balance()
        current_shares = self.get_shares_owned(cleaned_ticker)

        if type(quantity) is bool or not (isinstance(quantity, (int, float)) and math.isfinite(quantity) and quantity > 0):
            can_execute = False
            reason = f"Invalid trade quantity: {quantity}. Quantity must be greater than 0 and finite."
            price_out = exec_price if (type(exec_price) is not bool and isinstance(exec_price, (int, float)) and math.isfinite(exec_price) and exec_price > 0) else 0.0
            total_cost = 0.0
        elif type(exec_price) is bool or not (isinstance(exec_price, (int, float)) and math.isfinite(exec_price) and exec_price > 0):
            can_execute = False
            reason = f"Invalid trade price: {exec_price}. Price must be greater than 0 and finite."
            price_out = exec_price if (type(exec_price) is not bool and isinstance(exec_price, (int, float)) and math.isfinite(exec_price)) else 0.0
            total_cost = 0.0
        else:
            price_out = exec_price
            total_cost = exec_price * quantity
            if action_type == "BUY":
                can_execute = cash_available >= total_cost
                reason = "" if can_execute else f"Insufficient cash: required ${total_cost:,.2f}, available ${cash_available:,.2f}"
            elif action_type == "SELL":
                can_execute = (current_shares - quantity) >= -1e-9
                reason = "" if can_execute else f"Insufficient shares: requested {quantity}, owned {current_shares}"
            else:
                can_execute = False
                reason = f"Unknown trade action '{action}'"

        return {
            "action": action_type,
            "ticker": cleaned_ticker,
            "quantity": quantity,
            "price_per_share": price_out,
            "total_value": total_cost,
            "cash_available": cash_available,
            "shares_owned": current_shares,
            "can_execute": can_execute,
            "reason": reason,
        }

    def execute_trade(
        self,
        action: str,
        ticker: str,
        quantity: float,
        price: Optional[float] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a paper trade order and persist position and transaction to SQLite."""
        cleaned_ticker = ticker.strip().upper()
        action_type = action.strip().upper()
        cash_balance = self.get_cash_balance()

        if type(quantity) is bool or not (isinstance(quantity, (int, float)) and math.isfinite(quantity) and quantity > 0):
            return {
                "status": "error",
                "message": f"Order rejected: Quantity must be greater than 0 and finite (received {quantity}).",
                "cash_remaining": cash_balance,
            }

        exec_price = price if price is not None else self.get_quote(cleaned_ticker)

        if type(exec_price) is bool or not (isinstance(exec_price, (int, float)) and math.isfinite(exec_price) and exec_price > 0):
            return {
                "status": "error",
                "message": f"Order rejected: Price must be greater than 0 and finite (received {exec_price}).",
                "cash_remaining": cash_balance,
            }

        total_amount = exec_price * quantity

        if action_type == "BUY":
            if cash_balance < total_amount:
                return {
                    "status": "error",
                    "message": f"Order rejected: Insufficient cash balance (${cash_balance:,.2f} available vs ${total_amount:,.2f} required).",
                    "cash_remaining": cash_balance,
                }

            new_cash = cash_balance - total_amount
            if self._cash_balance is not None:
                self._cash_balance = new_cash
            self._db.update_portfolio_summary(cash_balance=new_cash)

            pos = None
            if self._positions is not None:
                pos = self._positions.get(cleaned_ticker)
            else:
                pos = self._db.get_position(cleaned_ticker)

            if pos:
                old_shares = float(pos["shares"])
                old_cost = float(pos["total_cost"])
                new_shares = old_shares + quantity
                new_total_cost = old_cost + total_amount
                new_avg_cost = new_total_cost / new_shares if new_shares > 0 else exec_price
                pos_name = name or pos["name"]
                cum_div = float(pos.get("cumulative_dividends", 0.0))
            else:
                new_shares = quantity
                new_total_cost = total_amount
                new_avg_cost = exec_price
                pos_name = name or f"{cleaned_ticker} Equity"
                cum_div = 0.0

            if self._positions is not None:
                self._positions[cleaned_ticker] = {
                    "ticker": cleaned_ticker,
                    "name": pos_name,
                    "shares": new_shares,
                    "avg_cost": new_avg_cost,
                    "total_cost": new_total_cost,
                    "cumulative_dividends": cum_div,
                }

            self._db.upsert_position(
                ticker=cleaned_ticker,
                name=pos_name,
                shares=new_shares,
                avg_cost=new_avg_cost,
                total_cost=new_total_cost,
                cumulative_dividends=cum_div,
            )

            tx = self._db.record_transaction(
                order_type="BUY",
                total_amount=total_amount,
                ticker=cleaned_ticker,
                shares=quantity,
                price=exec_price,
                notes="Executed paper buy order",
            )

            qty_str = f"{int(quantity)}" if float(quantity).is_integer() else f"{quantity:.2f}"
            return {
                "status": "success",
                "action": "BUY",
                "ticker": cleaned_ticker,
                "shares": quantity,
                "price": exec_price,
                "total_amount": total_amount,
                "message": f"Successfully purchased {qty_str} shares of {cleaned_ticker} at ${exec_price:.2f}/share for ${total_amount:,.2f}.",
                "cash_remaining": new_cash,
                "transaction": tx,
            }

        elif action_type == "SELL":
            pos = None
            if self._positions is not None:
                pos = self._positions.get(cleaned_ticker)
            else:
                pos = self._db.get_position(cleaned_ticker)
            current_shares = float(pos["shares"]) if pos else 0.0

            if not pos or (quantity - current_shares > 1e-9):
                return {
                    "status": "error",
                    "message": f"Order rejected: Insufficient shares to sell {quantity} of {cleaned_ticker} (owned {current_shares}).",
                    "cash_remaining": cash_balance,
                }

            avg_cost = float(pos["avg_cost"])
            cost_basis_sold = avg_cost * quantity
            realized_pl = total_amount - cost_basis_sold

            summary = self._db.get_portfolio_summary()
            new_cash = float(cash_balance) + total_amount
            new_realized_pl = float(summary["realized_pl"]) + realized_pl
            if self._cash_balance is not None:
                self._cash_balance = new_cash
            self._db.update_portfolio_summary(cash_balance=new_cash, realized_pl=new_realized_pl)

            new_shares = current_shares - quantity
            if new_shares <= 1e-9:
                if self._positions is not None and cleaned_ticker in self._positions:
                    del self._positions[cleaned_ticker]
                self._db.delete_position(cleaned_ticker)
            else:
                new_total_cost = float(pos["total_cost"]) - cost_basis_sold
                if self._positions is not None:
                    self._positions[cleaned_ticker] = {
                        "ticker": cleaned_ticker,
                        "name": pos["name"],
                        "shares": new_shares,
                        "avg_cost": avg_cost,
                        "total_cost": new_total_cost,
                        "cumulative_dividends": float(pos.get("cumulative_dividends", 0.0)),
                    }
                self._db.upsert_position(
                    ticker=cleaned_ticker,
                    name=pos["name"],
                    shares=new_shares,
                    avg_cost=avg_cost,
                    total_cost=new_total_cost,
                    cumulative_dividends=float(pos.get("cumulative_dividends", 0.0)),
                )

            tx = self._db.record_transaction(
                order_type="SELL",
                total_amount=total_amount,
                ticker=cleaned_ticker,
                shares=quantity,
                price=exec_price,
                realized_pl=realized_pl,
                notes="Executed paper sell order",
            )

            qty_str = f"{int(quantity)}" if float(quantity).is_integer() else f"{quantity:.2f}"
            return {
                "status": "success",
                "action": "SELL",
                "ticker": cleaned_ticker,
                "shares": quantity,
                "price": exec_price,
                "total_amount": total_amount,
                "realized_pl": realized_pl,
                "message": f"Successfully sold {qty_str} shares of {cleaned_ticker} at ${exec_price:.2f}/share for ${total_amount:,.2f} (Realized P/L: ${realized_pl:+,.2f}).",
                "cash_remaining": new_cash,
                "transaction": tx,
            }

        return {
            "status": "error",
            "message": f"Invalid trade action '{action}'.",
            "cash_remaining": cash_balance,
        }

    def deposit_cash(self, amount: float, notes: str = "") -> Dict[str, Any]:
        """Deposit cash into the paper trading portfolio."""
        if amount <= 0:
            return {
                "status": "error",
                "message": f"Deposit amount must be greater than 0 (received {amount}).",
                "cash_balance": self.get_cash_balance(),
            }
        result = self._db.deposit_cash(amount=amount, notes=notes)
        return {
            "status": "success",
            "message": f"Successfully deposited ${amount:,.2f} cash.",
            "cash_balance": result["cash_balance"],
            "total_deposits": result["total_deposits"],
            "transaction": result["transaction"],
        }

    def withdraw_cash(self, amount: float, notes: str = "") -> Dict[str, Any]:
        """Withdraw cash from the paper trading portfolio."""
        if amount <= 0:
            return {
                "status": "error",
                "message": f"Withdrawal amount must be greater than 0 (received {amount}).",
                "cash_balance": self.get_cash_balance(),
            }
        try:
            result = self._db.withdraw_cash(amount=amount, notes=notes)
            return {
                "status": "success",
                "message": f"Successfully withdrew ${amount:,.2f} cash.",
                "cash_balance": result["cash_balance"],
                "total_withdrawals": result["total_withdrawals"],
                "transaction": result["transaction"],
            }
        except ValueError as err:
            return {
                "status": "error",
                "message": str(err),
                "cash_balance": self.get_cash_balance(),
            }

    def reset_portfolio(self, initial_cash: float = 100000.0) -> Dict[str, Any]:
        """Reset the portfolio back to the initial baseline cash balance."""
        summary = self._db.reset_portfolio(initial_cash=initial_cash)
        return {
            "status": "success",
            "message": f"Portfolio reset successfully to initial ${initial_cash:,.2f} baseline.",
            "cash_balance": summary["cash_balance"],
            "summary": summary,
        }

    def record_dividend(
        self,
        ticker: str,
        amount_per_share: Optional[float] = None,
        total_amount: Optional[float] = None,
        notes: str = "",
    ) -> Dict[str, Any]:
        """Log dividend distributions for an active holding."""
        cleaned = ticker.strip().upper()
        try:
            result = self._db.record_dividend(
                ticker=cleaned,
                amount_per_share=amount_per_share,
                total_amount=total_amount,
                notes=notes,
            )
            return {
                "status": "success",
                "message": f"Successfully recorded dividend of ${result['total_dividend']:,.2f} for {cleaned}.",
                "ticker": cleaned,
                "total_dividend": result["total_dividend"],
                "cash_balance": result["cash_balance"],
                "cumulative_dividends": result["cumulative_dividends"],
                "transaction": result["transaction"],
            }
        except ValueError as err:
            return {
                "status": "error",
                "message": str(err),
                "cash_balance": self.get_cash_balance(),
            }

    async def get_portfolio_status(self) -> Dict[str, Any]:
        """Generate comprehensive portfolio report and holdings table from SQLite database."""
        summary = self._db.get_portfolio_summary()
        cash_balance = float(self._cash_balance) if self._cash_balance is not None else float(summary.get("cash_balance", 0.0))
        initial_cash = float(self._initial_cash) if self._initial_cash is not None else float(summary.get("initial_cash", 100000.0))
        realized_pl = float(summary.get("realized_pl", 0.0))
        total_deposits = float(summary.get("total_deposits", 100000.0))
        total_withdrawals = float(summary.get("total_withdrawals", 0.0))
        total_dividends = float(summary.get("total_dividends", 0.0))

        if self._positions is not None:
            raw_positions = list(self._positions.values())
        else:
            raw_positions = self._db.get_positions()

        positions_list: List[Dict[str, Any]] = []
        total_positions_value = 0.0
        total_cost_basis = 0.0

        for p in raw_positions:
            ticker = p["ticker"]
            shares = float(p["shares"])
            avg_cost = float(p.get("avg_cost", 0.0))
            total_cost = float(p.get("total_cost", shares * avg_cost))
            cum_div = float(p.get("cumulative_dividends", 0.0))

            price = p.get("current_price", self.get_quote(ticker))
            current_val = shares * price
            unrealized_pl = current_val - total_cost
            unrealized_pl_pct = f"{(unrealized_pl / total_cost) * 100:.2f}%" if total_cost > 0 else "0.00%"
            yield_on_cost = f"{(cum_div / total_cost) * 100:.2f}%" if total_cost > 0 else "0.00%"

            pos_dict = {
                "ticker": ticker,
                "name": p.get("name", f"{ticker} Equity"),
                "shares": shares,
                "avg_cost": avg_cost,
                "total_cost": total_cost,
                "current_price": price,
                "current_value": current_val,
                "unrealized_pl": unrealized_pl,
                "unrealized_pl_pct": unrealized_pl_pct,
                "cumulative_dividends": cum_div,
                "yield_on_cost": yield_on_cost,
                "allocation_pct": "0.00%",
            }
            positions_list.append(pos_dict)
            total_positions_value += current_val
            total_cost_basis += total_cost

        net_asset_value = cash_balance + total_positions_value
        total_unrealized_pl = total_positions_value - total_cost_basis
        total_pl = total_unrealized_pl + realized_pl + total_dividends
        total_return_pct = (
            (total_pl / total_deposits) * 100.0 if total_deposits > 0 else 0.0
        )

        # Allocation percentages
        for pos_item in positions_list:
            if net_asset_value > 0:
                pos_item["allocation_pct"] = f"{(pos_item['current_value'] / net_asset_value) * 100:.2f}%"
            else:
                pos_item["allocation_pct"] = "0.00%"

        cash_allocation_pct = (cash_balance / net_asset_value) * 100 if net_asset_value > 0 else 0.0

        report_markdown = (
            "## Portfolio & Investment Summary\n\n"
            f"**Net Asset Value (NAV):** `${net_asset_value:,.2f}`\n"
            f"**Cash Balance:** `${cash_balance:,.2f}` ({cash_allocation_pct:.2f}% of portfolio)\n"
            f"**Holdings Market Value:** `${total_positions_value:,.2f}`\n"
            f"**Total Unrealized P/L:** `${total_unrealized_pl:+,.2f}`\n"
            f"**Realized P/L:** `${realized_pl:+,.2f}` | **Total Dividends:** `${total_dividends:,.2f}`\n"
            f"**Total Portfolio Return:** `${total_pl:+,.2f}` (`{total_return_pct:+.2f}%`)\n\n"
            "### Current Holdings\n\n"
            "| Ticker | Shares | Avg Cost | Current Price | Market Value | Unrealized P/L | Yield on Cost | Allocation |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
        )

        if positions_list:
            for p in positions_list:
                report_markdown += (
                    f"| **{p['ticker']}** | `{p['shares']:.1f}` | `${p['avg_cost']:.2f}` | `${p['current_price']:.2f}` | "
                    f"`${p['current_value']:,.2f}` | `{p['unrealized_pl']:+,.2f}` ({p['unrealized_pl_pct']}) | "
                    f"`{p['yield_on_cost']}` | `{p['allocation_pct']}` |\n"
                )
        else:
            report_markdown += "| - | 0.0 | $0.00 | $0.00 | $0.00 | $0.00 (0.00%) | 0.00% | 0.00% |\n"

        return {
            "status": "success",
            "net_asset_value": net_asset_value,
            "cash_balance": cash_balance,
            "initial_cash": initial_cash,
            "holdings_value": total_positions_value,
            "total_unrealized_pl": total_unrealized_pl,
            "realized_pl": realized_pl,
            "total_dividends": total_dividends,
            "total_return": total_pl,
            "total_return_pct": total_return_pct,
            "total_deposits": total_deposits,
            "total_withdrawals": total_withdrawals,
            "positions": positions_list,
            "summary_markdown": report_markdown,
        }

    def get_transaction_history(self, limit: int = 50) -> Dict[str, Any]:
        """Fetch and format transaction history log from the SQLite database."""
        tx_rows = self._db.get_transactions(limit=limit)
        tx_markdown = (
            "### Transaction & Audit History\n\n"
            "| Timestamp | Order Type | Ticker | Shares | Price | Total Value | Realized P/L | Notes |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
        )
        if tx_rows:
            for tx in tx_rows:
                shares_str = f"{tx['shares']:.1f}" if tx.get("shares") else "-"
                price_str = f"${tx['price']:.2f}" if tx.get("price") else "-"
                realized_str = f"${tx['realized_pl']:+,.2f}" if tx.get("realized_pl") else "-"
                tx_markdown += (
                    f"| {tx['timestamp']} | **{tx['order_type']}** | `{tx['ticker']}` | {shares_str} | "
                    f"{price_str} | `${tx['total_amount']:,.2f}` | {realized_str} | {tx['notes'] or '-'} |\n"
                )
        else:
            tx_markdown += "| - | - | - | - | - | $0.00 | - | No transactions recorded. |\n"

        return {
            "status": "success",
            "transactions": tx_rows,
            "summary_markdown": tx_markdown,
        }


investment_agent = InvestmentAgent()
