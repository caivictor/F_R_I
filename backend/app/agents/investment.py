"""Investment sub-agent for portfolio tracking and paper trade execution."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from backend.app.agents.personas import persona_manager


class InvestmentAgent:
    """Portfolio Manager & Execution Engine sub-agent."""

    def __init__(self) -> None:
        # Default bootstrap state for paper trading
        self._initial_cash: float = 100000.00
        self._cash_balance: float = 100000.00
        self._positions: Dict[str, Dict[str, Any]] = {
            "AAPL": {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "shares": 50.0,
                "avg_cost": 175.00,
                "total_cost": 8750.00,
                "current_price": 185.50,
                "current_value": 9275.00,
                "unrealized_pl": 525.00,
                "unrealized_pl_pct": "6.00%",
                "allocation_pct": "8.87%",
            },
            "NVDA": {
                "ticker": "NVDA",
                "name": "NVIDIA Corporation",
                "shares": 30.0,
                "avg_cost": 110.00,
                "total_cost": 3300.00,
                "current_price": 125.00,
                "current_value": 3750.00,
                "unrealized_pl": 450.00,
                "unrealized_pl_pct": "13.64%",
                "allocation_pct": "3.59%",
            },
        }
        # Deduct initial cost from cash
        self._cash_balance = self._initial_cash - sum(p["total_cost"] for p in self._positions.values())
        self._transactions: List[Dict[str, Any]] = [
            {
                "timestamp": "2026-08-01 09:30:00 UTC",
                "type": "INITIAL_DEPOSIT",
                "ticker": "-",
                "shares": 0,
                "price": 0.0,
                "total_amount": 100000.00,
                "notes": "Paper trading account bootstrap",
            },
            {
                "timestamp": "2026-08-05 14:00:00 UTC",
                "type": "BUY",
                "ticker": "AAPL",
                "shares": 50.0,
                "price": 175.00,
                "total_amount": 8750.00,
                "notes": "Core position allocation",
            },
            {
                "timestamp": "2026-08-10 10:15:00 UTC",
                "type": "BUY",
                "ticker": "NVDA",
                "shares": 30.0,
                "price": 110.00,
                "total_amount": 3300.00,
                "notes": "AI infrastructure allocation",
            },
        ]

    def get_persona(self) -> str:
        """Get the current persona prompt for Investment Agent."""
        return persona_manager.get_persona("investment")

    def get_cash_balance(self) -> float:
        """Get the current cash reserve balance."""
        return self._cash_balance

    def get_shares_owned(self, ticker: str) -> float:
        """Get current shares owned for a ticker."""
        cleaned = ticker.strip().upper()
        return float(self._positions.get(cleaned, {}).get("shares", 0.0))

    def get_quote(self, ticker: str) -> float:
        """Get the latest market price or fallback for a ticker."""
        cleaned = ticker.strip().upper()
        quotes = {
            "AAPL": 185.50,
            "NVDA": 125.00,
            "MSFT": 420.00,
            "AMZN": 180.00,
            "GOOGL": 165.00,
            "TSLA": 210.00,
            "META": 490.00,
        }
        return quotes.get(cleaned, 100.00)

    def estimate_trade(self, action: str, ticker: str, quantity: float) -> Dict[str, Any]:
        """Calculate trade cost, check affordability/shares, and prepare confirmation parameters."""
        cleaned_ticker = ticker.strip().upper()
        action_type = action.strip().upper()
        price = self.get_quote(cleaned_ticker)
        total_cost = price * quantity

        current_shares = self._positions.get(cleaned_ticker, {}).get("shares", 0.0)

        if quantity <= 0:
            can_execute = False
            reason = f"Invalid trade quantity: {quantity}. Quantity must be greater than 0."
        elif action_type == "BUY":
            can_execute = self._cash_balance >= total_cost
            reason = "" if can_execute else f"Insufficient cash: required ${total_cost:,.2f}, available ${self._cash_balance:,.2f}"
        elif action_type == "SELL":
            can_execute = current_shares >= quantity
            reason = "" if can_execute else f"Insufficient shares: requested {quantity}, owned {current_shares}"
        else:
            can_execute = False
            reason = f"Unknown trade action '{action}'"

        return {
            "action": action_type,
            "ticker": cleaned_ticker,
            "quantity": quantity,
            "price_per_share": price,
            "total_value": total_cost,
            "cash_available": self._cash_balance,
            "shares_owned": current_shares,
            "can_execute": can_execute,
            "reason": reason,
        }

    def execute_trade(self, action: str, ticker: str, quantity: float, price: Optional[float] = None) -> Dict[str, Any]:
        """Execute a paper trade order after user confirmation."""
        cleaned_ticker = ticker.strip().upper()
        action_type = action.strip().upper()
        exec_price = price if price is not None else self.get_quote(cleaned_ticker)
        total_amount = exec_price * quantity
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        if quantity <= 0:
            return {
                "status": "error",
                "message": f"Order rejected: Quantity must be greater than 0 (received {quantity}).",
                "cash_remaining": self._cash_balance,
            }

        if action_type == "BUY":
            if self._cash_balance < total_amount:
                return {
                    "status": "error",
                    "message": f"Order rejected: Insufficient cash balance (${self._cash_balance:,.2f} available vs ${total_amount:,.2f} required).",
                    "cash_remaining": self._cash_balance,
                }
            
            self._cash_balance -= total_amount
            if cleaned_ticker in self._positions:
                pos = self._positions[cleaned_ticker]
                new_shares = pos["shares"] + quantity
                new_total_cost = pos["total_cost"] + total_amount
                new_avg_cost = new_total_cost / new_shares
                pos["shares"] = new_shares
                pos["total_cost"] = new_total_cost
                pos["avg_cost"] = new_avg_cost
                pos["current_price"] = exec_price
                pos["current_value"] = new_shares * exec_price
                pos["unrealized_pl"] = pos["current_value"] - new_total_cost
                pos["unrealized_pl_pct"] = f"{(pos['unrealized_pl'] / new_total_cost) * 100:.2f}%"
            else:
                self._positions[cleaned_ticker] = {
                    "ticker": cleaned_ticker,
                    "name": f"{cleaned_ticker} Equity",
                    "shares": quantity,
                    "avg_cost": exec_price,
                    "total_cost": total_amount,
                    "current_price": exec_price,
                    "current_value": total_amount,
                    "unrealized_pl": 0.0,
                    "unrealized_pl_pct": "0.00%",
                    "allocation_pct": "0.00%",
                }

            self._transactions.append({
                "timestamp": now,
                "type": "BUY",
                "ticker": cleaned_ticker,
                "shares": quantity,
                "price": exec_price,
                "total_amount": total_amount,
                "notes": "Executed paper buy order",
            })

            return {
                "status": "success",
                "message": f"Successfully purchased {quantity} shares of {cleaned_ticker} at ${exec_price:.2f}/share for ${total_amount:,.2f}.",
                "cash_remaining": self._cash_balance,
            }

        elif action_type == "SELL":
            current_pos = self._positions.get(cleaned_ticker)
            if not current_pos or current_pos["shares"] < quantity:
                return {
                    "status": "error",
                    "message": f"Order rejected: Insufficient shares to sell {quantity} of {cleaned_ticker}.",
                    "cash_remaining": self._cash_balance,
                }

            self._cash_balance += total_amount
            new_shares = current_pos["shares"] - quantity
            cost_basis_sold = current_pos["avg_cost"] * quantity
            current_pos["total_cost"] -= cost_basis_sold
            current_pos["shares"] = new_shares
            current_pos["current_value"] = new_shares * exec_price
            if new_shares > 0:
                current_pos["unrealized_pl"] = current_pos["current_value"] - current_pos["total_cost"]
                current_pos["unrealized_pl_pct"] = f"{(current_pos['unrealized_pl'] / current_pos['total_cost']) * 100:.2f}%"
            else:
                del self._positions[cleaned_ticker]

            self._transactions.append({
                "timestamp": now,
                "type": "SELL",
                "ticker": cleaned_ticker,
                "shares": quantity,
                "price": exec_price,
                "total_amount": total_amount,
                "notes": "Executed paper sell order",
            })

            return {
                "status": "success",
                "message": f"Successfully sold {quantity} shares of {cleaned_ticker} at ${exec_price:.2f}/share for ${total_amount:,.2f}.",
                "cash_remaining": self._cash_balance,
            }

        return {"status": "error", "message": f"Invalid trade action '{action}'.", "cash_remaining": self._cash_balance}

    async def get_portfolio_status(self) -> Dict[str, Any]:
        """Generate comprehensive portfolio report and holdings table."""
        total_positions_value = 0.0
        total_cost_basis = 0.0

        for ticker, pos in self._positions.items():
            price = self.get_quote(ticker)
            pos["current_price"] = price
            pos["current_value"] = pos["shares"] * price
            pos["unrealized_pl"] = pos["current_value"] - pos["total_cost"]
            if pos["total_cost"] > 0:
                pos["unrealized_pl_pct"] = f"{(pos['unrealized_pl'] / pos['total_cost']) * 100:.2f}%"
            total_positions_value += pos["current_value"]
            total_cost_basis += pos["total_cost"]

        net_asset_value = self._cash_balance + total_positions_value
        total_unrealized_pl = total_positions_value - total_cost_basis
        total_return_pct = (
            ((net_asset_value - self._initial_cash) / self._initial_cash) * 100
            if self._initial_cash > 0
            else 0.0
        )

        # Update allocation percentages
        for pos in self._positions.values():
            if net_asset_value > 0:
                pos["allocation_pct"] = f"{(pos['current_value'] / net_asset_value) * 100:.2f}%"
            else:
                pos["allocation_pct"] = "0.00%"

        cash_allocation_pct = (self._cash_balance / net_asset_value) * 100 if net_asset_value > 0 else 0.0

        report_markdown = (
            "## Portfolio & Investment Summary\n\n"
            f"**Net Asset Value (NAV):** `${net_asset_value:,.2f}`\n"
            f"**Cash Balance:** `${self._cash_balance:,.2f}` ({cash_allocation_pct:.2f}% of portfolio)\n"
            f"**Holdings Market Value:** `${total_positions_value:,.2f}`\n"
            f"**Total Unrealized P/L:** `${total_unrealized_pl:+,.2f}` (Overall Return: `{total_return_pct:+.2f}%`)\n\n"
            "### Current Holdings\n\n"
            "| Ticker | Shares | Avg Cost | Current Price | Market Value | Unrealized P/L | Allocation |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
        )

        if self._positions:
            for p in self._positions.values():
                report_markdown += (
                    f"| **{p['ticker']}** | `{p['shares']:.1f}` | `${p['avg_cost']:.2f}` | `${p['current_price']:.2f}` | "
                    f"`${p['current_value']:,.2f}` | `{p['unrealized_pl']:+,.2f}` ({p['unrealized_pl_pct']}) | `{p['allocation_pct']}` |\n"
                )
        else:
            report_markdown += "| - | 0.0 | $0.00 | $0.00 | $0.00 | $0.00 (0.00%) | 0.00% |\n"

        return {
            "status": "success",
            "net_asset_value": net_asset_value,
            "cash_balance": self._cash_balance,
            "holdings_value": total_positions_value,
            "total_unrealized_pl": total_unrealized_pl,
            "total_return_pct": total_return_pct,
            "positions": list(self._positions.values()),
            "summary_markdown": report_markdown,
        }


investment_agent = InvestmentAgent()
