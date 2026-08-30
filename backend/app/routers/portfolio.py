"""Router for Investment Agent portfolio tracking, cash management, and transaction history."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.agents.investment import investment_agent

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


class CashDepositRequest(BaseModel):
    """Payload for cash deposit."""
    amount: float = Field(..., gt=0, description="Amount of cash to deposit in USD")
    notes: Optional[str] = Field(default="", description="Optional deposit note")


class CashWithdrawRequest(BaseModel):
    """Payload for cash withdrawal."""
    amount: float = Field(..., gt=0, description="Amount of cash to withdraw in USD")
    notes: Optional[str] = Field(default="", description="Optional withdrawal note")


class PortfolioResetRequest(BaseModel):
    """Payload for resetting paper trading account."""
    initial_cash: Optional[float] = Field(default=100000.0, gt=0, description="Initial cash balance")


class DividendLogRequest(BaseModel):
    """Payload for logging dividend income."""
    ticker: str = Field(..., description="Equity ticker symbol")
    amount_per_share: Optional[float] = Field(default=None, gt=0, description="Dividend per share")
    total_amount: Optional[float] = Field(default=None, gt=0, description="Total dividend distribution amount")
    notes: Optional[str] = Field(default="", description="Optional dividend note")


class DirectTradeRequest(BaseModel):
    """Payload for direct paper trade execution."""
    action: str = Field(..., description="Trade action (BUY or SELL)")
    ticker: str = Field(..., description="Ticker symbol")
    quantity: float = Field(..., gt=0, description="Number of shares")
    price: Optional[float] = Field(default=None, gt=0, description="Execution price per share (optional)")


@router.get("")
async def get_portfolio() -> Dict[str, Any]:
    """Retrieve full portfolio status including holdings, NAV, and profit/loss metrics."""
    return await investment_agent.get_portfolio_status()


@router.get("/transactions")
async def get_transactions(limit: int = 50) -> Dict[str, Any]:
    """Retrieve historical transaction audit logs."""
    return investment_agent.get_transaction_history(limit=limit)


@router.post("/deposit")
async def deposit_cash(request: CashDepositRequest) -> Dict[str, Any]:
    """Deposit cash funds into the portfolio."""
    result = investment_agent.deposit_cash(amount=request.amount, notes=request.notes or "")
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/withdraw")
async def withdraw_cash(request: CashWithdrawRequest) -> Dict[str, Any]:
    """Withdraw cash funds from the portfolio."""
    result = investment_agent.withdraw_cash(amount=request.amount, notes=request.notes or "")
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/reset")
async def reset_portfolio(request: Optional[PortfolioResetRequest] = None) -> Dict[str, Any]:
    """Reset portfolio back to baseline initial cash ($100,000 default)."""
    initial_amt = request.initial_cash if request and request.initial_cash else 100000.0
    return investment_agent.reset_portfolio(initial_cash=initial_amt)


@router.post("/dividend")
async def record_dividend(request: DividendLogRequest) -> Dict[str, Any]:
    """Record dividend distribution for a holding."""
    if not request.amount_per_share and not request.total_amount:
        raise HTTPException(
            status_code=400,
            detail="Must provide either 'amount_per_share' or 'total_amount' greater than 0.",
        )
    result = investment_agent.record_dividend(
        ticker=request.ticker,
        amount_per_share=request.amount_per_share,
        total_amount=request.total_amount,
        notes=request.notes or "",
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/trade")
async def execute_trade(request: DirectTradeRequest) -> Dict[str, Any]:
    """Execute a paper trade order."""
    action = request.action.upper().strip()
    if action not in ("BUY", "SELL"):
        raise HTTPException(status_code=400, detail="Action must be BUY or SELL.")
    result = investment_agent.execute_trade(
        action=action,
        ticker=request.ticker,
        quantity=request.quantity,
        price=request.price,
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result
