"""Manager Agent orchestrator for F.R.I. multi-agent system."""

import asyncio
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple

from backend.app.agents.analysis import analysis_agent
from backend.app.agents.investment import investment_agent
from backend.app.agents.personas import persona_manager
from backend.app.agents.research import research_agent
from backend.app.config import settings

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

        # Match patterns like: "Buy 10 shares of NVDA", "purchase 15 AAPL", "sell 5 shares of it", "Buy 100 shares of 0700.HK"
        pattern = r"\b(buy|purchase|sell)\s+(\d+(?:\.\d+)?)\s*(?:shares\s*(?:of)?)?\s*([a-zA-Z0-9\$\.\:\-]+)"
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
                cleaned = re.sub(
                    r"\b(today|now|please|stock|company|portfolio|shares|share|fundamentals|and moat|moat|thesis|for me)\b",
                    "",
                    extracted,
                    flags=re.IGNORECASE,
                ).strip()
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

    async def _execute_subagent_with_healing(
        self,
        agent_name: str,
        task_func: Callable[..., Coroutine[Any, Any, Dict[str, Any]]],
        initial_param: Any,
        progress_callback: Optional[ProgressCallback],
        steps_accumulator: List[Dict[str, Any]],
        max_attempts: int = 3,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Self-Healing Engine: execute sub-agent task with dynamic query adaptation up to 3 retries."""
        last_exception: Optional[Exception] = None
        current_param = initial_param

        for attempt in range(1, max_attempts + 1):
            try:
                # Enforce tool timeout per PRD (15-20s)
                timeout_limit = float(settings.DEFAULT_TIMEOUT_SECONDS)
                result = await asyncio.wait_for(
                    task_func(current_param),
                    timeout=timeout_limit,
                )
                # If the agent returned an explicit error status (not guardrail rejection)
                if isinstance(result, dict) and result.get("status") == "error":
                    raise RuntimeError(result.get("message", "Sub-agent execution error."))

                return True, result

            except Exception as exc:
                last_exception = exc
                err_msg = str(exc) or exc.__class__.__name__

                if attempt < max_attempts:
                    # Dynamically adjust query / parameter for next attempt
                    if agent_name == "research":
                        if attempt == 1:
                            # Attempt 2: Rephrase to simplified clean keywords
                            raw = str(initial_param or "")
                            cleaned_terms = " ".join(re.findall(r"\b[a-zA-Z]{3,}\b", raw))
                            current_param = cleaned_terms if cleaned_terms else "business market"
                            adaptation_desc = f"rephrased query '{current_param}'"
                        else:
                            # Attempt 3: Fallback to global top business RSS
                            current_param = None
                            adaptation_desc = "general business topic feed"

                    elif agent_name == "analysis":
                        if attempt == 1:
                            # Attempt 2: Normalize and extract ticker symbol
                            current_param = analysis_agent._resolve_ticker(str(initial_param))
                            adaptation_desc = f"normalized ticker symbol '{current_param}'"
                        else:
                            # Attempt 3: Base clean symbol
                            current_param = str(current_param).split()[0].replace("$", "").upper()
                            adaptation_desc = f"base ticker fallback '{current_param}'"
                    else:
                        adaptation_desc = "standard fallback parameters"

                    await self._emit_step(
                        progress_callback,
                        steps_accumulator,
                        "manager",
                        f"[Manager] Sub-agent '{agent_name}' failed attempt {attempt} ({err_msg}). Retrying ({attempt + 1}/{max_attempts}) with {adaptation_desc}...",
                    )
                else:
                    await self._emit_step(
                        progress_callback,
                        steps_accumulator,
                        "manager",
                        f"[Manager] Sub-agent '{agent_name}' failed after {max_attempts} attempts. Error: {err_msg}",
                    )

        # Graceful root-cause reporting after 3 failed retries
        return False, {
            "status": "failed",
            "agent": agent_name,
            "attempts": max_attempts,
            "error": str(last_exception),
            "reason": f"Execution failed after {max_attempts} attempts. Last error: {str(last_exception)}",
        }

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
                qty_str = f"{int(trade['quantity'])}" if float(trade['quantity']).is_integer() else f"{trade['quantity']:.2f}"
                response_text = f"Trade order for **{trade['action']} {qty_str} shares of {trade['ticker']}** has been **cancelled**."
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

        # 2. Check for Portfolio Reset Intent
        if re.search(r"\b(reset\s+(?:my\s+)?(?:portfolio|account|balance|holdings|baseline)|reset\s+to\s+\$?(?:100k|100,000|100000))\b", cleaned, re.IGNORECASE):
            await self._emit_step(
                progress_callback, steps, "manager", "[Manager] Routing portfolio reset request to Investment Agent..."
            )
            await self._emit_step(
                progress_callback, steps, "investment", "[Investment Agent] Resetting paper trading portfolio to $100,000 baseline..."
            )
            reset_result = investment_agent.reset_portfolio()
            response_text = (
                "### Portfolio Reset Complete\n\n"
                f"{reset_result['message']}\n\n"
                f"- **Cash Balance:** `${reset_result['cash_balance']:,.2f}`\n"
                "- **Holdings:** Cleared (0 positions)\n"
                "- **Realized P/L:** `$0.00`"
            )
            session.add_message("assistant", response_text)
            return {
                "session_id": session.session_id,
                "response": response_text,
                "steps": steps,
                "agent_data": reset_result,
            }

        # 3. Check for Cash Deposit Intent
        deposit_match = re.search(r"\b(?:deposit|fund\s+account|add\s+cash)\s+\$?(\d+(?:,\d{3})*(?:\.\d+)?)\b", user_message, re.IGNORECASE)
        if not deposit_match and cleaned.startswith("deposit"):
            deposit_match = re.search(r"\bdeposit\s+\$?(\d+(?:,\d{3})*(?:\.\d+)?)", user_message, re.IGNORECASE)
        if deposit_match:
            raw_amt = deposit_match.group(1).replace(",", "")
            amt = float(raw_amt)
            await self._emit_step(
                progress_callback, steps, "manager", f"[Manager] Processing cash deposit of ${amt:,.2f}..."
            )
            await self._emit_step(
                progress_callback, steps, "investment", f"[Investment Agent] Depositing ${amt:,.2f} into cash reserves..."
            )
            dep_result = investment_agent.deposit_cash(amt)
            if dep_result["status"] == "success":
                response_text = (
                    "### Cash Deposit Successful\n\n"
                    f"Successfully deposited **${amt:,.2f}** into your portfolio.\n\n"
                    f"- **Updated Cash Balance:** `${dep_result['cash_balance']:,.2f}`\n"
                    f"- **Total Capital Deposited:** `${dep_result['total_deposits']:,.2f}`"
                )
            else:
                response_text = f"### Deposit Failed\n\n{dep_result['message']}"
            session.add_message("assistant", response_text)
            return {
                "session_id": session.session_id,
                "response": response_text,
                "steps": steps,
                "agent_data": dep_result,
            }

        # 4. Check for Cash Withdrawal Intent
        withdraw_match = re.search(r"\b(?:withdraw|take\s+out)\s+(?:cash\s+)?\$?(\d+(?:,\d{3})*(?:\.\d+)?)\b", user_message, re.IGNORECASE)
        if withdraw_match:
            raw_amt = withdraw_match.group(1).replace(",", "")
            amt = float(raw_amt)
            await self._emit_step(
                progress_callback, steps, "manager", f"[Manager] Processing cash withdrawal of ${amt:,.2f}..."
            )
            await self._emit_step(
                progress_callback, steps, "investment", f"[Investment Agent] Validating cash balance and processing withdrawal of ${amt:,.2f}..."
            )
            with_result = investment_agent.withdraw_cash(amt)
            if with_result["status"] == "success":
                response_text = (
                    "### Cash Withdrawal Successful\n\n"
                    f"Successfully withdrew **${amt:,.2f}** from your portfolio.\n\n"
                    f"- **Remaining Cash Balance:** `${with_result['cash_balance']:,.2f}`\n"
                    f"- **Total Capital Withdrawn:** `${with_result['total_withdrawals']:,.2f}`"
                )
            else:
                response_text = (
                    "### Withdrawal Failed\n\n"
                    f"**Reason:** {with_result['message']}\n\n"
                    f"**Current Cash Available:** `${with_result.get('cash_balance', investment_agent.get_cash_balance()):,.2f}`"
                )
            session.add_message("assistant", response_text)
            return {
                "session_id": session.session_id,
                "response": response_text,
                "steps": steps,
                "agent_data": with_result,
            }

        # 5. Check for Dividend Distribution Intent
        dividend_match = re.search(r"\b(?:record|log|add)\s+dividend\s+(?:of\s+)?\$?(\d+(?:\.\d+)?)\s*(?:per\s+share\s+)?(?:for\s+)?([A-Za-z0-9\$\.\:\-]+)", user_message, re.IGNORECASE)
        if dividend_match:
            amt_val = float(dividend_match.group(1))
            ticker_val = dividend_match.group(2).replace("$", "").upper().strip()
            is_per_share = "per share" in user_message.lower()
            await self._emit_step(
                progress_callback, steps, "manager", f"[Manager] Logging dividend for {ticker_val}..."
            )
            await self._emit_step(
                progress_callback, steps, "investment", f"[Investment Agent] Updating cumulative dividends and cash for {ticker_val}..."
            )
            if is_per_share:
                div_result = investment_agent.record_dividend(ticker=ticker_val, amount_per_share=amt_val)
            else:
                div_result = investment_agent.record_dividend(ticker=ticker_val, total_amount=amt_val)

            if div_result["status"] == "success":
                response_text = (
                    "### Dividend Distribution Recorded\n\n"
                    f"{div_result['message']}\n\n"
                    f"- **Cumulative Dividends for {ticker_val}:** `${div_result['cumulative_dividends']:,.2f}`\n"
                    f"- **Updated Cash Balance:** `${div_result['cash_balance']:,.2f}`"
                )
            else:
                response_text = f"### Dividend Recording Failed\n\n**Reason:** {div_result['message']}"
            session.add_message("assistant", response_text)
            return {
                "session_id": session.session_id,
                "response": response_text,
                "steps": steps,
                "agent_data": div_result,
            }

        # 6. Check for Transaction History / Audit Log Intent
        if re.search(r"\b(transaction history|transactions|trade history|order history|audit log|recent trades|history of orders)\b", cleaned, re.IGNORECASE):
            await self._emit_step(
                progress_callback, steps, "manager", "[Manager] Fetching transaction history and audit log from Investment Agent..."
            )
            await self._emit_step(
                progress_callback, steps, "investment", "[Investment Agent] Retrieving historical order logs from SQLite database..."
            )
            tx_res = investment_agent.get_transaction_history()
            session.add_message("assistant", tx_res["summary_markdown"])
            return {
                "session_id": session.session_id,
                "response": tx_res["summary_markdown"],
                "steps": steps,
                "agent_data": tx_res,
            }

        # 7. Check for Trade Intent (Buy / Sell) -> Trigger 2-Step Confirmation Guardrail
        trade_params = self._extract_trade_parameters(user_message, session)
        if trade_params:
            action = trade_params["action"]
            ticker = trade_params["ticker"]
            quantity = trade_params["quantity"]
            session.last_ticker = ticker

            # Guardrail: Check eligibility for trade targets (reject private and non-US / OTC equities)
            rejection = analysis_agent._check_eligibility(ticker)
            if rejection:
                await self._emit_step(
                    progress_callback, steps, "manager",
                    f"[Manager] Trade eligibility check rejected target '{ticker}': {rejection}"
                )
                shares_owned = investment_agent.get_shares_owned(ticker)
                response_text = (
                    f"### Trade Validation Failed\n\n"
                    f"Cannot execute order for **{action} {quantity} shares of {ticker}**.\n\n"
                    f"**Reason:** {rejection}\n\n"
                    f"**Current Cash Balance:** `${investment_agent.get_cash_balance():,.2f}`\n"
                    f"**Shares Owned:** `{shares_owned:.1f}`"
                )
                session.add_message("assistant", response_text)
                return {
                    "session_id": session.session_id,
                    "response": response_text,
                    "steps": steps,
                    "agent_data": {"status": "rejected", "reason": rejection},
                }

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
            # Step A: Research with Self-Healing
            await self._emit_step(
                progress_callback, steps, "research", "[Research Agent] Fetching top market headlines and prominent companies..."
            )
            success_r, research_res = await self._execute_subagent_with_healing(
                agent_name="research",
                task_func=research_agent.gather_market_news,
                initial_param=user_message,
                progress_callback=progress_callback,
                steps_accumulator=steps,
            )
            if not success_r:
                error_resp = (
                    "### Sub-Agent Execution Failure\n\n"
                    f"**Manager Report:** Research Agent failed after 3 automated retry attempts.\n\n"
                    f"**Root Cause:** `{research_res.get('reason')}`\n\n"
                    "Please verify your query or try again shortly."
                )
                session.add_message("assistant", error_resp)
                return {"session_id": session.session_id, "response": error_resp, "steps": steps, "agent_data": research_res}

            top_companies = research_res.get("top_companies", [])
            top_ticker = top_companies[0]["ticker"] if top_companies else "NVDA"
            session.last_ticker = top_ticker

            # Step B: Analysis with Self-Healing
            await self._emit_step(
                progress_callback, steps, "analysis", f"[Analysis Agent] Performing deep fundamental evaluation on lead candidate {top_ticker}..."
            )
            success_a, analysis_res = await self._execute_subagent_with_healing(
                agent_name="analysis",
                task_func=analysis_agent.analyze_company,
                initial_param=top_ticker,
                progress_callback=progress_callback,
                steps_accumulator=steps,
            )
            if not success_a:
                error_resp = (
                    "### Sub-Agent Execution Failure\n\n"
                    f"**Manager Report:** Analysis Agent failed after 3 automated retry attempts on candidate `{top_ticker}`.\n\n"
                    f"**Root Cause:** `{analysis_res.get('reason')}`\n\n"
                    "Please specify an alternate ticker symbol."
                )
                session.add_message("assistant", error_resp)
                return {"session_id": session.session_id, "response": error_resp, "steps": steps, "agent_data": analysis_res}

            # Step C: Investment Context
            await self._emit_step(
                progress_callback, steps, "investment", "[Investment Agent] Checking portfolio cash capacity and allocation..."
            )
            portfolio_res = await investment_agent.get_portfolio_status()

            pipeline_summary = (
                f"# Executive Investment Discovery Briefing\n\n"
                f"## 1. Market Research Findings\n"
                f"{research_res.get('summary_markdown', '')}\n\n"
                f"---\n\n"
                f"## 2. Quantitative & Fundamental Analysis: {top_ticker}\n"
                f"{analysis_res.get('summary_markdown', '')}\n\n"
                f"---\n\n"
                f"## 3. Portfolio Allocation & Capital Capacity\n"
                f"Current Cash Balance: `${portfolio_res['cash_balance']:,.2f}` | NAV: `${portfolio_res['net_asset_value']:,.2f}`\n\n"
                f"**Manager Recommendation:** {top_ticker} represents a compelling compounding thesis aligned with current market themes. "
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

            # Check guardrail eligibility directly first
            rejection = analysis_agent._check_eligibility(target)
            if rejection:
                session.add_message("assistant", rejection)
                return {
                    "session_id": session.session_id,
                    "response": rejection,
                    "steps": steps,
                    "agent_data": {"status": "rejected", "reason": rejection},
                }

            # Self-healing execution for analysis agent
            success_a, analysis_res = await self._execute_subagent_with_healing(
                agent_name="analysis",
                task_func=analysis_agent.analyze_company,
                initial_param=target,
                progress_callback=progress_callback,
                steps_accumulator=steps,
            )

            if not success_a:
                error_resp = (
                    "### Analysis Agent Execution Failure\n\n"
                    f"**Manager Report:** Unable to complete fundamental analysis for **'{target}'** after 3 automated attempts.\n\n"
                    f"**Root Cause:** `{analysis_res.get('reason')}`\n\n"
                    "**Action Required:** Please verify the ticker symbol or exchange listing and try again."
                )
                session.add_message("assistant", error_resp)
                return {
                    "session_id": session.session_id,
                    "response": error_resp,
                    "steps": steps,
                    "agent_data": analysis_res,
                }

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

            # Self-healing execution for research agent
            success_r, research_res = await self._execute_subagent_with_healing(
                agent_name="research",
                task_func=research_agent.gather_market_news,
                initial_param=user_message,
                progress_callback=progress_callback,
                steps_accumulator=steps,
            )

            if not success_r:
                error_resp = (
                    "### Research Agent Execution Failure\n\n"
                    "**Manager Report:** Unable to retrieve business news headlines after 3 automated recovery attempts.\n\n"
                    f"**Root Cause:** `{research_res.get('reason')}`\n\n"
                    "**Action Required:** Please check your internet connectivity or try rephrasing your research prompt."
                )
                session.add_message("assistant", error_resp)
                return {
                    "session_id": session.session_id,
                    "response": error_resp,
                    "steps": steps,
                    "agent_data": research_res,
                }

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
