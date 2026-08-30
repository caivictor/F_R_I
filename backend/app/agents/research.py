"""Research sub-agent for gathering business news and market themes."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from backend.app.agents.personas import persona_manager


class ResearchAgent:
    """Financial Data & News Gatherer sub-agent."""

    def __init__(self) -> None:
        pass

    def get_persona(self) -> str:
        """Get the current persona prompt for Research Agent."""
        return persona_manager.get_persona("research")

    async def gather_market_news(self, query: Optional[str] = None) -> Dict[str, Any]:
        """Gather top business headlines and extract prominent US public companies.
        
        In Phase 1, returns a structured report with top 3-5 public companies and market themes.
        In Phase 2, this interfaces with Google News RSS and HTML scraping.
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Structured top companies for Phase 1 PoC
        top_companies: List[Dict[str, Any]] = [
            {
                "ticker": "NVDA",
                "name": "NVIDIA Corporation",
                "headline": "AI Infrastructure Demand Fuels Record Data Center Growth and Next-Gen Chip Shipments",
                "publisher": "Reuters",
                "timestamp": now,
                "url": "https://news.google.com/search?q=NVIDIA",
                "summary": "NVIDIA continues to see strong demand from cloud hyperscalers for GPU computing clusters and enterprise AI platforms.",
            },
            {
                "ticker": "MSFT",
                "name": "Microsoft Corporation",
                "headline": "Cloud Revenue and Enterprise AI Copilot Adoption Accelerate in Latest Quarter",
                "publisher": "Bloomberg",
                "timestamp": now,
                "url": "https://news.google.com/search?q=Microsoft",
                "summary": "Microsoft Azure cloud services and enterprise AI commercial seats drive sustained margin expansion and software growth.",
            },
            {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "headline": "Services Growth and On-Device Apple Intelligence Drive Upgraded Device Cycles",
                "publisher": "Wall Street Journal",
                "timestamp": now,
                "url": "https://news.google.com/search?q=Apple",
                "summary": "High-margin Services segment continues double-digit expansion with robust free cash flow generation and capital return program.",
            },
            {
                "ticker": "AMZN",
                "name": "Amazon.com, Inc.",
                "headline": "AWS Cloud Margin Rebounds While Retail Logistics Efficiency Expands Operating Income",
                "publisher": "Financial Times",
                "timestamp": now,
                "url": "https://news.google.com/search?q=Amazon",
                "summary": "Regional fulfillment network cost optimizations paired with AWS workload migrations bolster quarterly free cash flow.",
            },
        ]

        market_themes: List[str] = [
            "Enterprise Artificial Intelligence & Hyperscaler Capital Expenditure Cycles",
            "Cloud Computing Infrastructure Migration & AI Platform Monetization",
            "Resilient Free Cash Flow Generation among Mega-Cap Technology Leaders",
        ]

        summary_markdown = (
            "### Market Intelligence Briefing\n\n"
            f"**Generated:** {now}\n\n"
            "#### Key Market Themes\n"
            + "\n".join([f"- **{theme}**" for theme in market_themes])
            + "\n\n#### Prominent Public Companies in Focus\n\n"
            + "\n\n".join([
                f"**{c['name']} ({c['ticker']})**\n"
                f"- **Headline:** {c['headline']}\n"
                f"- **Publisher:** {c['publisher']} | [Source Link]({c['url']})\n"
                f"- **Summary:** {c['summary']}"
                for c in top_companies
            ])
        )

        return {
            "status": "success",
            "timestamp": now,
            "query": query,
            "market_themes": market_themes,
            "top_companies": top_companies,
            "summary_markdown": summary_markdown,
        }


research_agent = ResearchAgent()
