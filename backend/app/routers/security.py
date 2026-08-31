"""Router for security audits, input sanitization, and transaction guardrails."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.agents.security import security_agent

router = APIRouter(prefix="/api/security", tags=["security"])


class InputValidationRequest(BaseModel):
    """Payload for input sanitization check."""

    text: str = Field(..., description="User prompt or text to analyze for security risks")


class InputValidationResponse(BaseModel):
    """Result of input sanitization check."""

    is_safe: bool
    risk_level: str
    detected_patterns: List[str]
    sanitized_text: str


class TradeValidationRequest(BaseModel):
    """Payload for transaction security and risk evaluation."""

    action: str = Field(..., description="'BUY' or 'SELL'")
    ticker: str = Field(..., description="Equity ticker symbol")
    quantity: float = Field(..., description="Number of shares")
    price: float = Field(..., description="Market execution price")
    available_cash: float = Field(..., description="Current available cash reserves")
    existing_shares: Optional[float] = Field(default=0.0, description="Current shares owned in position")


class TradeValidationResponse(BaseModel):
    """Result of transaction risk evaluation."""

    is_valid: bool
    risk_level: str
    warnings: List[str]
    reasons: List[str]


class RedactRequest(BaseModel):
    """Payload for sensitive data redaction."""

    text: str = Field(..., description="Text content to scan and redact")


class RedactResponse(BaseModel):
    """Result of secret redaction."""

    sanitized_text: str
    redacted_count: int
    has_leaks: bool


class AuditItem(BaseModel):
    """Single security posture check result."""

    control: str
    status: str
    details: str


class AuditReportResponse(BaseModel):
    """System-wide security posture audit report."""

    timestamp: str
    overall_status: str
    security_score: float
    checks_passed: int
    checks_total: int
    audit_results: List[AuditItem]


@router.get("/audit", response_model=AuditReportResponse)
async def get_security_audit() -> AuditReportResponse:
    """Run real-time automated security posture audit on system configuration and guardrails."""
    report = security_agent.audit_system_posture()
    return AuditReportResponse(**report)


@router.post("/validate-input", response_model=InputValidationResponse)
async def validate_user_input(request: InputValidationRequest) -> InputValidationResponse:
    """Analyze input prompt for adversarial injection patterns, XSS, or unauthorized overrides."""
    res = security_agent.sanitize_input(request.text)
    return InputValidationResponse(**res)


@router.post("/validate-trade", response_model=TradeValidationResponse)
async def validate_trade(request: TradeValidationRequest) -> TradeValidationResponse:
    """Perform pre-trade security verification for abnormal order size, fat-finger, or cash limits."""
    res = security_agent.validate_trade_order(
        action=request.action,
        ticker=request.ticker,
        quantity=request.quantity,
        price=request.price,
        available_cash=request.available_cash,
        existing_shares=request.existing_shares or 0.0,
    )
    return TradeValidationResponse(**res)


@router.post("/redact", response_model=RedactResponse)
async def redact_secrets(request: RedactRequest) -> RedactResponse:
    """Scan and redact API keys, tokens, and sensitive secrets from text."""
    res = security_agent.redact_sensitive_data(request.text)
    return RedactResponse(**res)
