"""Agent system personas definitions and management."""

from typing import Dict, Optional


DEFAULT_PERSONAS: Dict[str, str] = {
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


class PersonaManager:
    """Manages active and default system personas for all agents."""

    def __init__(self) -> None:
        self._personas: Dict[str, str] = dict(DEFAULT_PERSONAS)

    def get_persona(self, agent: str) -> str:
        """Get the active persona for a specific agent."""
        return self._personas.get(agent.lower(), DEFAULT_PERSONAS.get(agent.lower(), ""))

    def get_all_personas(self) -> Dict[str, str]:
        """Get all active personas."""
        return dict(self._personas)

    def get_defaults(self) -> Dict[str, str]:
        """Get all default system personas."""
        return dict(DEFAULT_PERSONAS)

    def set_persona(self, agent: str, persona: str) -> bool:
        """Set a custom persona for an agent."""
        agent_key = agent.lower()
        if agent_key not in DEFAULT_PERSONAS:
            return False
        self._personas[agent_key] = persona
        return True

    def reset_persona(self, agent: Optional[str] = None) -> None:
        """Reset an agent persona or all personas to default."""
        if agent is None or agent.strip() == "":
            self._personas = dict(DEFAULT_PERSONAS)
        else:
            agent_key = agent.lower()
            if agent_key in DEFAULT_PERSONAS:
                self._personas[agent_key] = DEFAULT_PERSONAS[agent_key]


persona_manager = PersonaManager()
