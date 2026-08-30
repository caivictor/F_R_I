"""Manager Agent orchestrator for F.R.I. multi-agent system."""

import re
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional
from datetime import datetime, timezone

from backend.app.config import settings
from backend.app.agents.personas import persona_manager
from backend.app.agents.research import research_agent
from backend.app.agents.analysis import analysis_agent
from backend.app.agents.investment import investment_agent

ProgressCallback = Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]


class SessionState:
    """Conversational memory state for a single session."""

    def __init__(self, session_id: str) -> None:
        self.session_id: str = session_id
        self.messages: List[Dict[str, str]] = []
        self.last_ticker: Optional[str] = None
        self.pending_trade: Optional[Dict[str, Any]] = None
        self.created_at: str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def add_message(self, role: str, content: str) -> None:
        """Append a message to history."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        })


class ManagerAgent:
    """Master Orchestrator, User Interface Proxy, & System Supervisor."""

    def __init__(self) -> None:
        self._sessions: Dict[str, SessionState] = {}

    def get_persona(self) -> str:
        """Get the current persona prompt for Manager Agent."""
        return persona_manager.get_persona("manager")

    def get_or_create_session(self, session_id: Optional[str] = None) -> SessionState:
        """Retrieve existing session state or initialize a new one."""
        if not session_id or session_id.strip() == "":
            session_id = str(uuid.uuid4())
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(session_id=session_id)
        return self._sessions[session_id]

    def _resolve_entities_and_pronouns(self, message: str, session: SessionState) -> str:
        """Resolve pronouns like 'it', 'its', 'this company' using session memory."""
        if not session.last_ticker:
            return message

        resolved = message
        ticker = session.last_ticker

        # Regex replacements for pronoun references using literal replacement callable
        patterns = [
            r"\b(it|its|this company|the company|this stock|the stock)\b",
        ]
        for pattern in patterns:
            resolved = re.sub(pattern, lambda _: ticker, resolved, flags=re.IGNORECASE)

        return resolved

    def _extract_trade_parameters(self, message: str, session: SessionState) -> Optional[Dict[str, Any]]:
        """Extract action, ticker, and quantity from a trade query."""
        resolved = self._resolve_entities_and_pronouns(message, session)
        
        # Match patterns like: "Buy 10 shares of NVDA", "purchase 15 AAPL", "sell 5 shares of it"
        pattern = r"\b(buy|purchase|sell)\s+(\d+(?:\.\d+)?)\s*(?:shares\s*(?:of)?)?\s*([a-zA-Z\$\.]+)"
        match = re.search(pattern, resolved, flags=re.IGNORECASE)
        if match:
            raw_action = match.group(1).upper()
            action = "BUY" if raw_action in ("BUY", "PURCHASE") else "SELL"
            quantity = float(match.group(2))
            ticker = match.group(3).replace("$", "").upper().strip()
            return {"action": action, "ticker": ticker, "quantity": quantity}
        
        return None

    def _extract_ticker_for_analysis(self, message: str, session: SessionState) -> Optional[str]:
        """Extract company name or ticker for equity analysis."""
        resolved = self._resolve_entities_and_pronouns(message, session)

        # Common prompt patterns
        patterns = [
            r"\b(?:analyze|dossier|evaluate|research|overview|check|fundamentals of|look into)\s+(?:company|stock|ticker)?\s*([a-zA-Z0-9\$\.\s\:\-]+)",
            r"\bwhat about\s+([a-zA-Z0-9\$\.\s\:\-]+)",
            r"\bis\s+([a-zA-Z0-9\$\.\s\:\-]+)\s+a (?:good|bad|solid|buy)",
            r"\bhow is\s+([a-zA-Z0-9\$\.\s\:\-]+)\s+doing",
        ]
        for pat in patterns:
            m = re.search(pat, resolved, flags=re.IGNORECASE)
            if m:
                extracted = m.group(1).strip().replace("$", "")
                # Exclude common non-ticker trailing words
                cleaned = re.sub(r"\b(today|now|please|stock|company|portfolio|shares|share|fundamentals|and moat|moat|thesis|for me)\b", "", extracted, flags=re.IGNORECASE).strip()
                if cleaned:
                    return cleaned

        # Direct short ticker detection like "$AAPL" or "NVDA"
        ticker_match = re.search(r"\$([A-Za-z]{1,5})\b", message)
        if ticker_match:
            return ticker_match.group(1).upper()

        return None

    async def _emit_step(
        self,
        callback: Optional[ProgressCallback],
        steps_accumulator: List[Dict[str, Any]],
        agent: str,
        message: str,
    ) -> None:
        """Record step and invoke progress callback if provided."""
        step = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "agent": agent,
            "message": message,
        }
        steps_accumulator.append(step)
        if callback:
            await callback(step)

    async def process_message(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Dict[str, Any]:
        """Process incoming user prompt through multi-agent orchestration."""
        session = self.get_or_create_session(session_id)
        session.add_message("user", user_message)
        steps: List[Dict[str, Any]] = []

        await self._emit_step(
            progress_callback, steps, "manager", f"[Manager] Ingesting request: '{user_message.strip()}'"
        )

        cleaned = user_message.strip().lower()

        # 1. Check for Pending Trade Confirmation Interlock
        if session.pending_trade:
            await self._emit_step(
                progress_callback, steps, "manager", "[Manager] Evaluating pending trade confirmation guardrail..."
            )
            trade = session.pending_trade
            if re.search(r"\b(yes|confirm|proceed|yep|sure|ok|execute)\b", cleaned, re.IGNORECASE):
                await self._emit_step(
                    progress_callback, steps, "investment",
                    f"[Investment Agent] Executing verified order: {trade['action']} {trade['quantity']} {trade['ticker']}..."
                )
                exec_result = investment_agent.execute_trade(
                    action=trade["action"],
                    ticker=trade["ticker"],
                    quantity=trade["quantity"],
                    price=trade["price_per_share"],
                )
                session.pending_trade = None
                
                cash_remaining = exec_result.get("cash_remaining", investment_agent.get_cash_balance())
                response_text = (
                    f"### Trade Confirmation & Execution\n\n"
                    f"{exec_result.get('message', 'Trade executed.')}\n\n"
                    f"**Remaining Cash Balance:** `${cash_remaining:,.2f}`"
                )
                session.add_message("assistant", response_text)
                return {
                    "session_id": session.session_id,
                    "response": response_text,
                    "steps": steps,
                    "agent_data": exec_result,
                }

            elif re.search(r"\b(no|cancel|reject|nevermind|stop|abort)\b", cleaned, re.IGNORECASE):
                session.pending_trade = None
                await self._emit_step(
                    progress_callback, steps, "manager", "[Manager] User declined trade confirmation. Order cancelled."
                )
                response_text = f"Trade order for **{trade['action']} {trade['quantity']} shares of {trade['ticker']}** has been **cancelled**."
                session.add_message("assistant", response_text)
                return {
                    "session_id": session.session_id,
                    "response": response_text,
                    "steps": steps,
                    "agent_data": {"status": "cancelled"},
                }
            else:
                # Unrelated message received while a trade was pending - invalidate pending trade
                session.pending_trade = None

        # 2. Check for Trade Intent (Buy / Sell) -> Trigger 2-Step Confirmation Guardrail
        trade_params = self._extract_trade_parameters(user_message, session)
        if trade_params:
            action = trade_params["action"]
            ticker = trade_params["ticker"]
            quantity = trade_params["quantity"]
            session.last_ticker = ticker

            await self._emit_step(
                progress_callback, steps, "manager",
                f"[Manager] Trade intent detected: {action} {quantity} shares of {ticker}. Querying Investment Agent for quote and balance..."
            )
            estimate = investment_agent.estimate_trade(action, ticker, quantity)

            if not estimate["can_execute"]:
                await self._emit_step(
                    progress_callback, steps, "investment",
                    f"[Investment Agent] Trade pre-check failed: {estimate['reason']}"
                )
                response_text = (
                    f"### Trade Validation Failed\n\n"
                    f"Cannot execute order for **{action} {quantity} shares of {ticker}**.\n\n"
                    f"**Reason:** {estimate['reason']}\n\n"
                    f"**Current Cash Balance:** `${estimate['cash_available']:,.2f}`\n"
                    f"**Shares Owned:** `{estimate['shares_owned']}`"
                )
                session.add_message("assistant", response_text)
                return {
                    "session_id": session.session_id,
                    "response": response_text,
                    "steps": steps,
                    "agent_data": estimate,
                }

            # Set pending trade state
            session.pending_trade = estimate
            await self._emit_step(
                progress_callback, steps, "manager",
                "[Manager] Enforcing 2-step confirmation guardrail. Prompting user for verification."
            )
            confirmation_prompt = (
                f"### Trade Order Confirmation Required\n\n"
                f"You have requested to **{action}** **{quantity} shares** of **{ticker}**.\n\n"
                f"- **Market Price (Estimate):** `${estimate['price_per_share']:.2f}` / share\n"
                f"- **Total Estimated Value:** `${estimate['total_value']:,.2f}`\n"
                f"- **Available Cash Balance:** `${estimate['cash_available']:,.2f}`\n\n"
                f"**You have ${estimate['cash_available']:,.2f} cash. {action.capitalize()}ing {quantity} shares of {ticker} at ${estimate['price_per_share']:.2f}/share will cost ~${estimate['total_value']:,.2f}. Confirm purchase? [Yes / No]**"
            )
            session.add_message("assistant", confirmation_prompt)
            return {
                "session_id": session.session_id,
                "response": confirmation_prompt,
                "steps": steps,
                "agent_data": estimate,
            }

        # 3. Check for End-to-End Discovery Pipeline
        if any(p in cleaned for p in ["discover", "pipeline", "top tech stories and analyze", "find top tech", "explore and analyze", "recommend top stocks"]):
            await self._emit_step(
                progress_callback, steps, "manager", "[Manager] Launching End-to-End Pipeline: Research -> Analysis -> Investment..."
            )
            # Step A: Research
            await self._emit_step(
                progress_callback, steps, "research", "[Research Agent] Fetching top market headlines and prominent companies..."
            )
            research_res = await research_agent.gather_market_news()
            top_company = research_res["top_companies"][0]
            top_ticker = top_company["ticker"]
            session.last_ticker = top_ticker

            # Step B: Analysis
            await self._emit_step(
                progress_callback, steps, "analysis", f"[Analysis Agent] Performing deep fundamental evaluation on lead candidate {top_ticker}..."
            )
            analysis_res = await analysis_agent.analyze_company(top_ticker)

            # Step C: Investment Context
            await self._emit_step(
                progress_callback, steps, "investment", "[Investment Agent] Checking portfolio cash capacity and allocation..."
            )
            portfolio_res = await investment_agent.get_portfolio_status()

            pipeline_summary = (
                f"# Executive Investment Discovery Briefing\n\n"
                f"## 1. Market Research Findings\n"
                f"{research_res['summary_markdown']}\n\n"
                f"---\n\n"
                f"## 2. Quantitative & Fundamental Analysis: {top_ticker}\n"
                f"{analysis_res['summary_markdown']}\n\n"
                f"---\n\n"
                f"## 3. Portfolio Allocation & Capital Capacity\n"
                f"Current Cash Balance: `${portfolio_res['cash_balance']:,.2f}` | NAV: `${portfolio_res['net_asset_value']:,.2f}`\n\n"
                f"**Manager Recommendation:** {top_ticker} represents a compelling compounding thesis aligned with current market AI infrastructure themes. "
                f"To initiate a position, instruct: `Buy [quantity] shares of {top_ticker}`."
            )
            session.add_message("assistant", pipeline_summary)
            return {
                "session_id": session.session_id,
                "response": pipeline_summary,
                "steps": steps,
                "agent_data": {
                    "research": research_res,
                    "analysis": analysis_res,
                    "portfolio": portfolio_res,
                },
            }

        # 4. Check for Portfolio / Balance / Holdings Intent
        if any(w in cleaned for w in ["portfolio", "balance", "holdings", "positions", "cash balance", "nav", "how much cash", "account"]):
            await self._emit_step(
                progress_callback, steps, "manager", "[Manager] Routing query to Investment Agent for portfolio status..."
            )
            await self._emit_step(
                progress_callback, steps, "investment", "[Investment Agent] Fetching real-time portfolio holdings and cash balance..."
            )
            portfolio_res = await investment_agent.get_portfolio_status()
            session.add_message("assistant", portfolio_res["summary_markdown"])
            return {
                "session_id": session.session_id,
                "response": portfolio_res["summary_markdown"],
                "steps": steps,
                "agent_data": portfolio_res,
            }

        # 5. Check for Company / Ticker Analysis Intent
        ticker_query = self._extract_ticker_for_analysis(user_message, session)
        if ticker_query or any(w in cleaned for w in ["analyze", "analysis", "dossier", "roic", "valuation", "moat", "thesis", "metrics", "fundamentals"]):
            target = ticker_query if ticker_query else (session.last_ticker or "AAPL")
            session.last_ticker = target

            await self._emit_step(
                progress_callback, steps, "manager", f"[Manager] Routing equity analysis for '{target}' to Analysis Agent..."
            )
            await self._emit_step(
                progress_callback, steps, "analysis", f"[Analysis Agent] Enforcing US-public filter and calculating fundamental metrics for {target}..."
            )
            analysis_res = await analysis_agent.analyze_company(target)
            if analysis_res.get("ticker"):
                session.last_ticker = analysis_res["ticker"]
            session.add_message("assistant", analysis_res["summary_markdown"])
            return {
                "session_id": session.session_id,
                "response": analysis_res["summary_markdown"],
                "steps": steps,
                "agent_data": analysis_res,
            }

        # 6. Check for Market / News / Discovery Intent
        if any(w in cleaned for w in ["news", "market", "headlines", "trends", "stories", "macro", "sector", "research"]):
            await self._emit_step(
                progress_callback, steps, "manager", "[Manager] Routing market exploration request to Research Agent..."
            )
            await self._emit_step(
                progress_callback, steps, "research", "[Research Agent] Ingesting top business headlines and ranking public companies..."
            )
            research_res = await research_agent.gather_market_news(query=user_message)
            if research_res.get("top_companies"):
                session.last_ticker = research_res["top_companies"][0]["ticker"]
            session.add_message("assistant", research_res["summary_markdown"])
            return {
                "session_id": session.session_id,
                "response": research_res["summary_markdown"],
                "steps": steps,
                "agent_data": research_res,
            }

        # 7. General Assistant Overview / Greeting Fallback
        await self._emit_step(
            progress_callback, steps, "manager", "[Manager] Processing general inquiry..."
        )
        greeting = (
            "### Welcome to F.R.I. (Financial Research & Investment)\n\n"
            "I am your **Manager Agent**, orchestrating financial research, fundamental equity analysis, and paper-trading portfolio execution.\n\n"
            "**How I can assist you:**\n"
            "1. **Market Research:** *\"What are today's top business news and market themes?\"*\n"
            "2. **Fundamental Analysis:** *\"Analyze Apple\"* or *\"Evaluate NVDA fundamentals and moat\"*\n"
            "3. **Portfolio Management:** *\"Show my portfolio balance and positions\"*\n"
            "4. **Trade Execution:** *\"Buy 10 shares of NVDA\"* (includes strict 2-step confirmation)\n"
            "5. **End-to-End Discovery:** *\"Find top tech stories and analyze promising stocks\"*\n\n"
            "How would you like to proceed today?"
        )
        session.add_message("assistant", greeting)
        return {
            "session_id": session.session_id,
            "response": greeting,
            "steps": steps,
            "agent_data": {"type": "general_greeting"},
        }


manager_agent = ManagerAgent()
