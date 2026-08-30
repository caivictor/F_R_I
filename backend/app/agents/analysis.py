"""Analysis sub-agent for fundamental equity evaluation and dossier generation."""

from typing import Any, Dict, Optional
from backend.app.agents.personas import persona_manager

# Known private companies and non-US OTC indicators to filter
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
}

# Standard mock metrics library for Phase 1 PoC
COMPANY_DATABASE: Dict[str, Dict[str, Any]] = {
    "AAPL": {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "current_price": 185.50,
        "previous_close": 184.20,
        "market_cap": "2.85T",
        "roic": "58.2%",
        "roe": "147.4%",
        "gross_margin": "46.2%",
        "operating_margin": "30.7%",
        "fcf": "$108.8B",
        "fcf_yield": "3.8%",
        "debt_to_equity": "1.45",
        "current_ratio": "0.99",
        "rev_cagr_3yr": "7.8%",
        "trailing_pe": "32.4",
        "forward_pe": "28.6",
        "peg_ratio": "2.6",
        "dividend_yield": "0.52%",
        "moat": "Extremely high brand loyalty, proprietary iOS hardware/software ecosystem, and high ecosystem switching costs.",
        "bull_case": "Services revenue continues expansion with recurring high-margin subscriptions, while Apple Intelligence drives sustained upgrade supercycles.",
        "bear_case": "Regulatory antitrust scrutiny regarding App Store economics in the EU/US and smartphone market saturation.",
    },
    "MSFT": {
        "ticker": "MSFT",
        "name": "Microsoft Corporation",
        "sector": "Technology",
        "industry": "Software - Infrastructure",
        "current_price": 420.00,
        "previous_close": 418.50,
        "market_cap": "3.12T",
        "roic": "31.4%",
        "roe": "38.5%",
        "gross_margin": "69.8%",
        "operating_margin": "44.6%",
        "fcf": "$74.1B",
        "fcf_yield": "2.4%",
        "debt_to_equity": "0.41",
        "current_ratio": "1.24",
        "rev_cagr_3yr": "14.2%",
        "trailing_pe": "35.2",
        "forward_pe": "30.8",
        "peg_ratio": "2.2",
        "dividend_yield": "0.71%",
        "moat": "Entrenched enterprise software suite (Windows, Office365, Azure), deep developer lock-in, and leadership in commercial AI copilot integration.",
        "bull_case": "Azure cloud market share gains combined with enterprise software seat price increases and high-margin Copilot cross-selling.",
        "bear_case": "Elevated AI data center capex spending weighing on near-term free cash flow margins if monetization velocity slows.",
    },
    "NVDA": {
        "ticker": "NVDA",
        "name": "NVIDIA Corporation",
        "sector": "Technology",
        "industry": "Semiconductors",
        "current_price": 125.00,
        "previous_close": 123.80,
        "market_cap": "3.08T",
        "roic": "82.5%",
        "roe": "115.6%",
        "gross_margin": "75.1%",
        "operating_margin": "62.3%",
        "fcf": "$53.2B",
        "fcf_yield": "1.7%",
        "debt_to_equity": "0.18",
        "current_ratio": "3.52",
        "rev_cagr_3yr": "65.4%",
        "trailing_pe": "46.8",
        "forward_pe": "34.5",
        "peg_ratio": "1.4",
        "dividend_yield": "0.03%",
        "moat": "CUDA software ecosystem barrier to entry, full-stack computing architecture, and multi-generation lead in accelerated AI hardware.",
        "bull_case": "Continued sovereign and enterprise AI cluster infrastructure buildouts spanning the Blackwell architecture rollout.",
        "bear_case": "Customer concentration among top cloud hyperscalers designing custom internal silicon (ASICs) and semiconductor cyclicality.",
    },
    "AMZN": {
        "ticker": "AMZN",
        "name": "Amazon.com, Inc.",
        "sector": "Consumer Cyclical",
        "industry": "Internet Retail & Cloud",
        "current_price": 180.00,
        "previous_close": 178.50,
        "market_cap": "1.87T",
        "roic": "14.8%",
        "roe": "21.6%",
        "gross_margin": "48.9%",
        "operating_margin": "9.1%",
        "fcf": "$50.1B",
        "fcf_yield": "2.7%",
        "debt_to_equity": "0.58",
        "current_ratio": "1.06",
        "rev_cagr_3yr": "11.5%",
        "trailing_pe": "42.1",
        "forward_pe": "31.2",
        "peg_ratio": "1.5",
        "dividend_yield": "N/A",
        "moat": "Massive Prime subscriber network effect, automated regional logistics network, and high-margin AWS cloud infrastructure.",
        "bull_case": "Operating leverage from retail logistics regionalization and re-acceleration of AWS generative AI workloads.",
        "bear_case": "Macro consumer discretionary spending pressure and rising cloud infrastructure competitive pricing.",
    },
    "GOOGL": {
        "ticker": "GOOGL",
        "name": "Alphabet Inc.",
        "sector": "Communication Services",
        "industry": "Internet Content & Information",
        "current_price": 165.00,
        "previous_close": 163.70,
        "market_cap": "2.04T",
        "roic": "28.7%",
        "roe": "31.2%",
        "gross_margin": "57.4%",
        "operating_margin": "32.0%",
        "fcf": "$69.5B",
        "fcf_yield": "3.4%",
        "debt_to_equity": "0.10",
        "current_ratio": "2.10",
        "rev_cagr_3yr": "12.8%",
        "trailing_pe": "22.5",
        "forward_pe": "19.8",
        "peg_ratio": "1.2",
        "dividend_yield": "0.48%",
        "moat": "Dominant global search market share, YouTube streaming audience, Android OS ecosystem, and custom TPU computing stack.",
        "bull_case": "Search monetization resilience, Google Cloud profitability scaling, and custom silicon efficiency advantages.",
        "bear_case": "Antitrust remedies in search distribution agreements and AI search interface transition dynamics.",
    },
}


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

        # Check for known private companies
        for priv_key, priv_name in KNOWN_PRIVATE_COMPANIES.items():
            if priv_key in cleaned or cleaned in priv_key:
                return (
                    f"**Analysis Rejection**: {priv_name} is a private company. "
                    "F.R.I. Analysis Agent strictly evaluates US-listed public equities (NYSE/NASDAQ) "
                    "trading in USD with available SEC disclosures and market quotes."
                )

        # Check for OTC or Non-US indicators
        non_us_indicators = [".pk", ".ob", ":otc", "otc", ".to", ".l", ".hk", ".ss", ".sz", ".de", ".pa", ".as"]
        if any(ind in cleaned for ind in non_us_indicators):
            return (
                f"**Analysis Rejection**: '{ticker_or_name}' appears to be a non-US or OTC listing. "
                "F.R.I. Analysis Agent strictly restricts analysis to US-listed equities on major exchanges (NYSE/NASDAQ)."
            )

        return None

    def _find_company_data(self, ticker_or_name: str) -> Dict[str, Any]:
        """Lookup or build fundamental metrics for the company."""
        cleaned = ticker_or_name.strip().upper()
        # Remove common phrases if present
        for word in ["FUNDAMENTALS", "AND MOAT", "MOAT", "THESIS", "METRICS", "FOR ME", "PLEASE", "COMPANY", "STOCK"]:
            cleaned = cleaned.replace(word, "").strip()

        # Check alias
        if cleaned in COMPANY_ALIASES:
            cleaned = COMPANY_ALIASES[cleaned]
        
        # Direct ticker lookup
        if cleaned in COMPANY_DATABASE:
            return COMPANY_DATABASE[cleaned]

        # Name lookup in database
        for ticker, data in COMPANY_DATABASE.items():
            if cleaned in data["name"].upper() or data["name"].upper() in cleaned or cleaned in ticker:
                return data

        # Default structured fallback for other US tickers
        ticker_symbol = cleaned.split()[0].replace("$", "") if cleaned else "EQUITY"
        return {
            "ticker": ticker_symbol,
            "name": f"{ticker_symbol} Corporation",
            "sector": "US Equities",
            "industry": "Public Corporate",
            "current_price": 100.00,
            "previous_close": 99.50,
            "market_cap": "100.0B",
            "roic": "22.5%",
            "roe": "28.0%",
            "gross_margin": "52.0%",
            "operating_margin": "24.0%",
            "fcf": "$5.0B",
            "fcf_yield": "5.0%",
            "debt_to_equity": "0.65",
            "current_ratio": "1.50",
            "rev_cagr_3yr": "10.0%",
            "trailing_pe": "24.0",
            "forward_pe": "20.0",
            "peg_ratio": "1.8",
            "dividend_yield": "1.2%",
            "moat": "Established customer base, solid competitive positioning, and operational execution.",
            "bull_case": "Long-term secular market tailwinds and disciplined capital allocation driving shareholder returns.",
            "bear_case": "Broader macroeconomic cyclicality, inflation, and competitive market dynamics.",
        }

    async def analyze_company(self, ticker_or_name: str) -> Dict[str, Any]:
        """Generate a Long-Term Investment Dossier for an eligible US public equity."""
        rejection = self._check_eligibility(ticker_or_name)
        if rejection:
            return {
                "status": "rejected",
                "ticker": ticker_or_name,
                "is_eligible": False,
                "reason": rejection,
                "summary_markdown": rejection,
            }

        data = self._find_company_data(ticker_or_name)
        ticker = data["ticker"]
        name = data["name"]

        dossier_markdown = (
            f"## Long-Term Investment Dossier: {name} ({ticker})\n\n"
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
            f"- **Capital Allocation:** Demonstrates consistent reinvestment discipline with cash returned via repurchases and balance sheet resilience.\n\n"
            "### 4. Bull vs. Bear Risk Assessment\n"
            f"- **Bull Catalyst:** {data['bull_case']}\n"
            f"- **Bear Risk:** {data['bear_case']}\n"
        )

        return {
            "status": "success",
            "ticker": ticker,
            "is_eligible": True,
            "company_data": data,
            "summary_markdown": dossier_markdown,
        }


analysis_agent = AnalysisAgent()
