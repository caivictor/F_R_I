# ADVERSARIAL REVIEW

## ADV-001: Substring Matching on Trade Confirmation Causes False Positive Trade Execution and Stale Pending State Leakage

- Session: phase-1 gate
- Suggested severity: HIGH

What I did: In a multi-turn chat session, initiated a trade command ("Buy 10 shares of NVDA"). Upon receiving the two-step trade confirmation prompt, typed a follow-up inquiry containing the substring "ok" within another word ("Is tokenomics important?"). Also tested asking unrelated conversational questions (e.g. "What is the weather?") followed multiple turns later by "ok thank you".
Expected: The system should strictly match explicit, standalone confirmation keywords or prompt tokens ("yes", "confirm", "proceed", "no", "cancel") and should invalidate or clear the pending trade state when the user asks an unrelated query.
Actual: The check `any(w in cleaned for w in ["yes", "confirm", "proceed", "yep", "sure", "ok", "execute"])` matches "ok" as a substring inside arbitrary words such as "tokenomics", "broker", "spoke", or "looking", immediately executing the trade order without genuine user consent. Additionally, `session.pending_trade` is never invalidated or expired when unrelated queries are received, so conversational responses turns later trigger stale orders.
Screenshot: screenshots/adv-001-unintended-trade-execution.png

Disposition: ACCEPTED -> DEF-001

## ADV-002: Zero-Share Unowned Stock Sell Order Allowed to Enter Confirmation and Erroneously Reports $0.00 Remaining Cash

- Session: phase-1 gate
- Suggested severity: HIGH

What I did: Submitted a sell order for 0 shares of an unowned stock: "Sell 0 shares of TSLA", followed by a "yes" confirmation response.
Expected: Trade pre-validation should enforce positive quantities (> 0) and reject 0-share orders before prompting for confirmation. If trade execution fails or is rejected, the remaining cash balance reported to the user should reflect the actual current cash balance rather than $0.00.
Actual: Trade pre-validation checked `current_shares >= quantity` (0.0 >= 0 is True) and prompted the user for confirmation. Upon confirmation, `execute_trade` rejected the order, but `manager.py` extracted `exec_result.get('cash_remaining', 0.0)` which defaulted to 0.0, displaying `**Remaining Cash Balance:** $0.00` to the user despite having over $87,000 cash in the portfolio.
Screenshot: screenshots/adv-002-zero-shares-zero-cash-reporting.png

Disposition: ACCEPTED -> DEF-002

## ADV-003: Unhandled ZeroDivisionError in Portfolio NAV Calculations When Total Portfolio Value Is Zero

- Session: phase-1 gate
- Suggested severity: MEDIUM

What I did: Triggered `investment_agent.get_portfolio_status()` under a portfolio state where Net Asset Value is 0 (zero cash and zero positions).
Expected: The agent should safely handle zero NAV conditions without crashing, displaying 0.00% cash allocation.
Actual: In `backend/app/agents/investment.py` line 249, `(self._cash_balance / net_asset_value) * 100` executes without checking whether `net_asset_value == 0`. When NAV is 0, this raises an unhandled `ZeroDivisionError: float division by zero`, causing a 500 Internal Server Error.

Disposition: ACCEPTED -> DEF-003

## ADV-004: Unbounded Persona Payload Injection and Lack of Input Validation in Persona Management Endpoints

- Session: phase-1 gate
- Suggested severity: MEDIUM

What I did: Sent empty string `""` and multi-megabyte payloads (5MB+) to `POST /api/personas`. Also sent `POST /api/personas/reset` with invalid agent keys (e.g. `{"agent": "invalid_agent"}`).
Expected: `POST /api/personas` should enforce minimum and maximum length bounds on custom persona directives. `POST /api/personas/reset` should validate that the agent exists in system definitions and return HTTP 400 for unknown agents.
Actual: `POST /api/personas` accepts empty strings and arbitrarily large payloads without validation. `POST /api/personas/reset` returns HTTP 200 with `Persona(s) reset to default for: invalid_agent` for non-existent agents without raising an error or validating against known agents.
Screenshot: screenshots/adv-003-empty-persona-allowed.png

Disposition: ACCEPTED -> DEF-004

## ADV-005: Unhandled Regex PatternError in Pronoun Entity Resolution When Ticker Contains Regex Special Characters

- Session: phase-1 gate
- Suggested severity: LOW

What I did: Sent queries where extracted ticker/company tokens contain backslash patterns (e.g. `\99` or `\g<...>`), followed by a pronoun reference query ("What is its balance?" or "Buy 10 shares of it").
Expected: Entity resolution in `_resolve_entities_and_pronouns` should safely handle regex special characters by escaping replacement strings or using literal string replacements.
Actual: `re.sub(pattern, ticker, resolved, flags=re.IGNORECASE)` treats backslashes in `ticker` as group reference escapes. When an invalid group escape (like `\99`) is passed, python's `re.sub` raises `re.PatternError: invalid group reference`, causing an unhandled server error.

Disposition: ACCEPTED -> DEF-005
