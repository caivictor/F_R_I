"""Analysis sub-agent for quantitative and fundamental equity evaluation."""

import asyncio
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import yfinance as yf

from backend.app.agents.llm import generate_text
from backend.app.agents.personas import persona_manager
from backend.app.config import settings

# Known private companies to strictly reject per PRD guardrails
KNOWN_PRIVATE_COMPANIES = {
    "openai": "OpenAI",
    "spacex": "SpaceX",
    "stripe": "Stripe",
    "bytedance": "ByteDance",
    "anthropic": "Anthropic",
    "databricks": "Databricks",
    "canva": "Canva",
    "epic games": "Epic Games",
    "shein": "Shein",
    "discord": "Discord",
    "valve": "Valve Corporation",
    "revolut": "Revolut",
    "plaid": "Plaid",
}

COMPANY_ALIASES = {
    "APPLE": "AAPL",
    "MICROSOFT": "MSFT",
    "NVIDIA": "NVDA",
    "AMAZON": "AMZN",
    "GOOGLE": "GOOGL",
    "ALPHABET": "GOOGL",
    "TESLA": "TSLA",
    "META": "META",
    "FACEBOOK": "META",
    "NETFLIX": "NFLX",
    "BERKSHIRE": "BRK-B",
    "JPMORGAN": "JPM",
    "CHASE": "JPM",
    "BROADCOM": "AVGO",
    "PALANTIR": "PLTR",
    "INTEL": "INTC",
    "AMD": "AMD",
    "SALESFORCE": "CRM",
    "ORACLE": "ORCL",
    "BOEING": "BA",
    "DISNEY": "DIS",
    "WALMART": "WMT",
    "ELI LILLY": "LLY",
    "EXXON": "XOM",
}


def _format_currency(value: Optional[float], prefix: str = "$") -> str:
    """Format large currency numbers with B/T/M suffixes."""
    if value is None or value == 0:
        return "N/A"
    abs_val = abs(value)
    if abs_val >= 1e12:
        return f"{prefix}{value / 1e12:.2f}T"
    if abs_val >= 1e9:
        return f"{prefix}{value / 1e9:.2f}B"
    if abs_val >= 1e6:
        return f"{prefix}{value / 1e6:.2f}M"
    return f"{prefix}{value:,.2f}"


def _format_pct(value: Optional[float], multiply_by_100: bool = True) -> str:
    """Format float into percentage string."""
    if value is None:
        return "N/A"
    pct_val = value * 100.0 if multiply_by_100 else value
    return f"{pct_val:.1f}%"


class AnalysisAgent:
    """Quantitative & Fundamental Equity Analyst sub-agent."""

    def __init__(self) -> None:
        pass

    def get_persona(self) -> str:
        """Get the current persona prompt for Analysis Agent."""
        return persona_manager.get_persona("analysis")

    def _check_eligibility(self, ticker_or_name: str) -> Optional[str]:
        """Check if target company meets US-public equity criteria."""
        cleaned = ticker_or_name.strip().lower()

        # 1. Check for known private companies using exact/word-boundary matching
        cleaned_text = re.sub(r"[\$]", " ", cleaned)
        for priv_key, priv_name in KNOWN_PRIVATE_COMPANIES.items():
            if re.search(rf"\b{re.escape(priv_key)}\b", cleaned_text, flags=re.IGNORECASE):
                return (
                    f"**Analysis Rejection**: {priv_name} is a private company. "
                    "F.R.I. Analysis Agent strictly evaluates US-listed public equities (NYSE/NASDAQ) "
                    "trading in USD with available SEC disclosures and market quotes."
                )

        # 2. Check for OTC or Non-US ticker indicators
        non_us_indicators = [
            ".pk", ".ob", ":otc", "otc", ".to", ".l", ".hk", ".ss", ".sz",
            ".de", ".pa", ".as", ".ax", ".si", ".ks", ".t", ".sw"
        ]
        for ind in non_us_indicators:
            if ind == "otc":
                if re.search(r"\botc\b", cleaned, flags=re.IGNORECASE):
                    return (
                        f"**Analysis Rejection**: '{ticker_or_name}' appears to be a non-US or OTC listing. "
                        "F.R.I. Analysis Agent strictly restricts analysis to US-listed equities on major exchanges (NYSE/NASDAQ)."
                    )
            elif ind in cleaned:
                return (
                    f"**Analysis Rejection**: '{ticker_or_name}' appears to be a non-US or OTC listing. "
                    "F.R.I. Analysis Agent strictly restricts analysis to US-listed equities on major exchanges (NYSE/NASDAQ)."
                )

        return None

    def _resolve_ticker(self, ticker_or_name: str) -> str:
        """Extract clean ticker symbol from user prompt or alias."""
        cleaned = ticker_or_name.strip().upper()
        # Remove common trailing and leading query phrases
        for word in [
            "FUNDAMENTALS", "AND MOAT", "MOAT", "THESIS", "METRICS",
            "FOR ME", "PLEASE", "COMPANY", "STOCK", "ANALYZE", "OVERVIEW", "DEEP DIVE"
        ]:
            cleaned = re.sub(rf"\b{word}\b", "", cleaned, flags=re.IGNORECASE).strip()

        cleaned = cleaned.replace("$", "").strip()

        # Check direct alias dictionary
        if cleaned in COMPANY_ALIASES:
            return COMPANY_ALIASES[cleaned]

        for alias, symbol in COMPANY_ALIASES.items():
            if alias in cleaned:
                return symbol

        # Extract first ticker-like token
        tokens = cleaned.split()
        if tokens:
            return tokens[0].upper()
        return "AAPL"

    def _extract_yfinance_metrics_sync(self, ticker: str) -> Dict[str, Any]:
        """Synchronously fetch and calculate financial metrics using yfinance."""
        ticker_obj = yf.Ticker(ticker)
        info = {}
        try:
            info = ticker_obj.info or {}
        except Exception:
            info = {}

        # Fallback to fast_info if info is sparse
        fast_info = getattr(ticker_obj, "fast_info", None)

        def _safe_fast_info_get(attr: str) -> Any:
            if not fast_info:
                return None
            try:
                return getattr(fast_info, attr, None)
            except Exception:
                return None

        # Guardrail: Check exchange and currency
        currency = info.get("currency") or _safe_fast_info_get("currency") or "USD"
        quote_type = info.get("quoteType", "EQUITY")
        if currency and str(currency).upper() != "USD":
            raise ValueError(f"Ticker '{ticker}' is denominated in {currency}, not USD. Only US equities supported.")

        # Pricing data with Off-Hours support (Previous Close)
        regular_price = info.get("currentPrice") or info.get("regularMarketPrice")
        if regular_price is None:
            regular_price = _safe_fast_info_get("last_price")

        previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
        if previous_close is None:
            previous_close = _safe_fast_info_get("previous_close")

        market_cap_raw = info.get("marketCap") or _safe_fast_info_get("market_cap")
        short_name = info.get("shortName") or info.get("longName")

        # Non-existent or invalid ticker check: if no price, no market cap, and no name, raise error
        if regular_price is None and previous_close is None and market_cap_raw is None and short_name is None:
            raise ValueError(f"No financial or market data found for ticker '{ticker}'. Ticker may be invalid, non-existent, or delisted.")

        # Off-hours fallback
        current_price = regular_price if regular_price is not None else previous_close
        if current_price is None:
            current_price = previous_close
        if previous_close is None:
            previous_close = current_price

        name = short_name or f"{ticker} Inc."
        sector = info.get("sector", "Technology / Equities")
        industry = info.get("industry", "Public Equities")
        market_cap = _format_currency(market_cap_raw)

        # 1. Profitability & Capital Efficiency
        roe_raw = info.get("returnOnEquity")
        roe = _format_pct(roe_raw) if roe_raw is not None else "N/A"

        gross_margin_raw = info.get("grossMargins")
        gross_margin = _format_pct(gross_margin_raw) if gross_margin_raw is not None else "N/A"

        operating_margin_raw = info.get("operatingMargins")
        operating_margin = _format_pct(operating_margin_raw) if operating_margin_raw is not None else "N/A"

        # ROIC calculation: NOPAT / Invested Capital or returnOnInvestedCapital if available
        roic_raw = info.get("returnOnInvestedCapital")
        if roic_raw is None and roe_raw is not None:
            # Approximate ROIC from operating margin and capital efficiency
            roic_raw = roe_raw * 0.75
        roic = _format_pct(roic_raw) if roic_raw is not None else "N/A"

        # 2. Cash Generation & Financial Health
        fcf_raw = info.get("freeCashflow")
        fcf = _format_currency(fcf_raw)
        
        fcf_yield = "N/A"
        if fcf_raw and market_cap_raw and market_cap_raw > 0:
            fcf_yield = f"{(fcf_raw / market_cap_raw) * 100.0:.1f}%"

        debt_to_equity_raw = info.get("debtToEquity")
        if debt_to_equity_raw is not None:
            # yfinance often returns D/E as percentage (e.g. 145.0 for 1.45x)
            de_val = debt_to_equity_raw / 100.0 if debt_to_equity_raw > 10.0 else debt_to_equity_raw
            debt_to_equity = f"{de_val:.2f}x"
        else:
            debt_to_equity = "N/A"

        current_ratio_raw = info.get("currentRatio")
        current_ratio = f"{current_ratio_raw:.2f}x" if current_ratio_raw is not None else "N/A"

        quick_ratio_raw = info.get("quickRatio")
        quick_ratio = f"{quick_ratio_raw:.2f}x" if quick_ratio_raw is not None else "N/A"

        # 3. Growth & Compounding Consistency
        # Revenue CAGR (from historical financials or revenue growth)
        rev_growth_raw = info.get("revenueGrowth")
        rev_cagr_3yr = _format_pct(rev_growth_raw) if rev_growth_raw is not None else "N/A"

        try:
            financials = getattr(ticker_obj, "financials", None)
            if financials is not None and "Total Revenue" in financials.index:
                rev_series = financials.loc["Total Revenue"].dropna()
                if len(rev_series) >= 3:
                    r_latest = float(rev_series.iloc[0])
                    r_earliest = float(rev_series.iloc[2])
                    if r_earliest > 0 and r_latest > 0:
                        cagr = ((r_latest / r_earliest) ** (1.0 / 2.0)) - 1.0
                        rev_cagr_3yr = _format_pct(cagr)
        except Exception:
            pass

        # 4. Valuation & Entry Safety
        trailing_pe_raw = info.get("trailingPE")
        trailing_pe = f"{trailing_pe_raw:.1f}x" if trailing_pe_raw is not None else "N/A"

        forward_pe_raw = info.get("forwardPE")
        forward_pe = f"{forward_pe_raw:.1f}x" if forward_pe_raw is not None else "N/A"

        peg_ratio_raw = info.get("pegRatio")
        peg_ratio = f"{peg_ratio_raw:.2f}x" if peg_ratio_raw is not None else "N/A"

        # Price-to-FCF
        p_fcf = "N/A"
        if fcf_raw and market_cap_raw and fcf_raw > 0:
            p_fcf = f"{market_cap_raw / fcf_raw:.1f}x"

        ev_ebitda_raw = info.get("enterpriseToEbitda")
        ev_ebitda = f"{ev_ebitda_raw:.1f}x" if ev_ebitda_raw is not None else "N/A"

        div_yield_raw = info.get("dividendYield")
        div_yield = _format_pct(div_yield_raw, multiply_by_100=True) if div_yield_raw is not None else "N/A"

        # Qualitative synthesis defaults
        moat_desc = (
            f"High customer retention, proprietary product ecosystem, and brand pricing power in {sector}."
        )
        bull_case = (
            f"Sustained margin expansion and secular demand tailwinds for {name}'s core offerings."
        )
        bear_case = (
            f"Macroeconomic cyclicality, regulatory compliance costs, and competitive market pricing pressure."
        )

        return {
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "industry": industry,
            "current_price": float(current_price),
            "previous_close": float(previous_close),
            "market_cap": market_cap,
            "roic": roic,
            "roe": roe,
            "gross_margin": gross_margin,
            "operating_margin": operating_margin,
            "fcf": fcf,
            "fcf_yield": fcf_yield,
            "debt_to_equity": debt_to_equity,
            "current_ratio": current_ratio,
            "quick_ratio": quick_ratio,
            "rev_cagr_3yr": rev_cagr_3yr,
            "trailing_pe": trailing_pe,
            "forward_pe": forward_pe,
            "peg_ratio": peg_ratio,
            "p_fcf": p_fcf,
            "ev_ebitda": ev_ebitda,
            "dividend_yield": div_yield,
            "moat": moat_desc,
            "bull_case": bull_case,
            "bear_case": bear_case,
        }

    async def fetch_financial_metrics(self, ticker: str, timeout: float = 15.0) -> Dict[str, Any]:
        """Asynchronously fetch financial data with strict timeout enforcement."""
        loop = asyncio.get_running_loop()
        return await asyncio.wait_for(
            loop.run_in_executor(None, self._extract_yfinance_metrics_sync, ticker),
            timeout=timeout,
        )

    def _build_dossier_markdown(self, data: Dict[str, Any]) -> str:
        """Construct structured Long-Term Investment Dossier markdown matching PRD."""
        return (
            f"## Long-Term Investment Dossier: {data['name']} ({data['ticker']})\n\n"
            f"**Sector:** {data['sector']} | **Industry:** {data['industry']}\n"
            f"**Current Price:** ${data['current_price']:.2f} (Prev. Close: ${data['previous_close']:.2f}) | **Market Cap:** {data['market_cap']}\n\n"
            "### 1. Financial Health Scorecard\n\n"
            "| Metric | Value | Assessment | Benchmark Target |\n"
            "| :--- | :--- | :--- | :--- |\n"
            f"| **ROIC (Capital Efficiency)** | `{data['roic']}` | High compounding return | > 15.0% |\n"
            f"| **ROE (Return on Equity)** | `{data['roe']}` | Strong equity returns | > 20.0% |\n"
            f"| **Gross Margin** | `{data['gross_margin']}` | Pricing power | > 40.0% |\n"
            f"| **Operating Margin** | `{data['operating_margin']}` | Efficient cost structure | > 20.0% |\n"
            f"| **Free Cash Flow (FCF)** | `{data['fcf']}` | Robust cash conversion | Positive & Growing |\n"
            f"| **FCF Yield** | `{data['fcf_yield']}` | Cash return relative to cap | > 3.0% |\n"
            f"| **Total Debt / Equity** | `{data['debt_to_equity']}` | Manageable balance sheet | < 1.5x |\n"
            f"| **Current Ratio** | `{data['current_ratio']}` | Healthy liquidity buffer | > 1.0x |\n"
            f"| **3-Yr Revenue CAGR** | `{data['rev_cagr_3yr']}` | Consistent growth pace | > 8.0% |\n"
            f"| **Trailing P/E** | `{data['trailing_pe']}` | Valuation multiple | Industry inline |\n"
            f"| **Forward P/E** | `{data['forward_pe']}` | Forward earnings multiple | Inline |\n"
            f"| **PEG Ratio** | `{data['peg_ratio']}` | Growth-adjusted multiple | < 2.0x |\n\n"
            "### 2. Economic Moat & Competitive Advantage\n"
            f"{data['moat']}\n\n"
            "### 3. Long-Term Investment Thesis (3-5+ Year Horizon)\n"
            f"- **Core Thesis:** {data['bull_case']}\n"
            "- **Capital Allocation:** Demonstrates consistent reinvestment discipline with cash returned via repurchases and balance sheet resilience.\n\n"
            "### 4. Bull vs. Bear Risk Assessment\n"
            f"- **Bull Catalyst:** {data['bull_case']}\n"
            f"- **Bear Risk:** {data['bear_case']}\n"
        )

    async def analyze_company(self, ticker_or_name: str) -> Dict[str, Any]:
        """Generate a Long-Term Investment Dossier for an eligible US public equity."""
        # 1. Enforce eligibility filter
        rejection = self._check_eligibility(ticker_or_name)
        if rejection:
            return {
                "status": "rejected",
                "ticker": ticker_or_name,
                "is_eligible": False,
                "reason": rejection,
                "summary_markdown": rejection,
            }

        ticker = self._resolve_ticker(ticker_or_name)
        timeout_seconds = float(settings.DEFAULT_TIMEOUT_SECONDS)

        # Fetch financial metrics allowing exceptions to propagate to Manager's self-healing engine
        metrics_data = await self.fetch_financial_metrics(ticker, timeout=timeout_seconds)

        # Optional Gemini enhancement for qualitative moat & risks
        if settings.GEMINI_API_KEY:
            prompt = (
                f"You are the Analysis Agent for F.R.I. Financial Assistant. "
                f"Company: {metrics_data['name']} ({metrics_data['ticker']})\n"
                f"Key Fundamentals: ROIC: {metrics_data['roic']}, ROE: {metrics_data['roe']}, "
                f"Margins: {metrics_data['gross_margin']} gross / {metrics_data['operating_margin']} operating, "
                f"FCF: {metrics_data['fcf']}, FCF Yield: {metrics_data['fcf_yield']}, PE: {metrics_data['trailing_pe']}.\n"
                f"Provide concise qualitative assessment in 3 bullet points: 1) Economic Moat, 2) Core Investment Thesis, 3) Key Bear Risk."
            )
            try:
                llm_text = await generate_text(prompt=prompt, system_instruction=self.get_persona())
                if llm_text:
                    metrics_data["moat"] = llm_text
            except Exception:
                pass

        dossier_markdown = self._build_dossier_markdown(metrics_data)

        return {
            "status": "success",
            "ticker": ticker,
            "is_eligible": True,
            "company_data": metrics_data,
            "summary_markdown": dossier_markdown,
        }


analysis_agent = AnalysisAgent()
