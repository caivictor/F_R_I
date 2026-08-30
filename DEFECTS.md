# DEFECTS

## DEF-005: Unhandled Regex PatternError in Pronoun Entity Resolution When Ticker Contains Regex Special Characters

- Status: CLOSED
- Severity: LOW
- Found by: adversary (ADV-005)
- Phase: 1

Steps to reproduce:
1. Start the application and open a chat session.
2. Send a query where the extracted ticker or company name contains regex backslash sequences (e.g., `\99` or `\g<1>`).
3. In the next turn, send a pronoun reference query such as "What is its balance?" or "Buy 10 shares of it".

Expected: Entity resolution in `_resolve_entities_and_pronouns` should safely handle regex special characters by escaping replacement strings or performing literal string replacement.
Actual: `re.sub(pattern, replacement, resolved)` interprets backslashes in the replacement string as group reference escapes, throwing an unhandled `re.PatternError: invalid group reference` and crashing the server request.

History:
- qa: opened
- orchestrator: set FIX-READY (backend-dev: Replaced raw string interpolation with replacement callable in _resolve_entities_and_pronouns preventing unhandled re.PatternError)
- qa: closed (retested and verified safe resolution with regex escape characters in test_def_005_pronoun_resolution_regex_special_characters)

## DEF-004: Unbounded Persona Payload Injection and Lack of Input Validation in Persona Management Endpoints

- Status: CLOSED
- Severity: MEDIUM
- Found by: adversary (ADV-004)
- Phase: 1

Steps to reproduce:
1. Start the application backend server.
2. Send a `POST /api/personas` request with an empty string payload: `{"agent": "manager", "persona": ""}`.
3. Send a `POST /api/personas` request with an excessively large payload (e.g., 5MB+ string).
4. Send a `POST /api/personas/reset` request with an invalid/non-existent agent: `{"agent": "invalid_agent"}`.

Expected: `POST /api/personas` should validate input length bounds and reject empty or oversized strings with HTTP 400/422. `POST /api/personas/reset` should validate the agent name against configured system agents and return HTTP 400 for unknown agents.
Actual: `POST /api/personas` accepts empty strings and arbitrarily large payloads without validation. `POST /api/personas/reset` accepts invalid agent names and returns HTTP 200 with "Persona(s) reset to default for: invalid_agent".
Screenshot: screenshots/adv-003-empty-persona-allowed.png

History:
- qa: opened
- orchestrator: set FIX-READY (backend-dev: Added request validation checking agent names against registered defaults and constraining persona prompt length between 10 and 10,000 characters, returning HTTP 400 on invalid input)
- qa: closed (retested and verified HTTP 400 rejection on empty, short, oversized payloads, and invalid agents in test_def_004_persona_validation_bounds_and_agent_names)

## DEF-003: Unhandled ZeroDivisionError in Portfolio NAV Calculations When Total Portfolio Value Is Zero

- Status: CLOSED
- Severity: MEDIUM
- Found by: adversary (ADV-003)
- Phase: 1

Steps to reproduce:
1. Start the application backend.
2. Simulate or establish a portfolio state where Net Asset Value is 0 (zero cash balance and zero active stock holdings).
3. Request the portfolio summary status via `investment_agent.get_portfolio_status()`.

Expected: The agent should safely handle zero NAV conditions without crashing, displaying 0.00% cash allocation.
Actual: In `backend/app/agents/investment.py`, calculating `(self._cash_balance / net_asset_value) * 100` executes without checking whether `net_asset_value == 0`, raising an unhandled `ZeroDivisionError: float division by zero` and resulting in an HTTP 500 error.

History:
- qa: opened
- orchestrator: set FIX-READY (backend-dev: Added zero-check guards for net_asset_value == 0 and _initial_cash == 0 in get_portfolio_status to prevent ZeroDivisionError)
- qa: closed (retested and verified 0 NAV portfolio state handled gracefully with 0.00% allocation in test_def_003_zero_nav_calculation_no_zero_division)

## DEF-002: Zero-Share Unowned Stock Sell Order Allowed to Enter Confirmation and Erroneously Reports $0.00 Remaining Cash

- Status: CLOSED
- Severity: HIGH
- Found by: adversary (ADV-002)
- Phase: 1

Steps to reproduce:
1. Start the application and initiate a chat session with the default initial cash balance ($100,000.00) and no TSLA shares.
2. Send the sell order command: "Sell 0 shares of TSLA".
3. Observe that the system enters the two-step confirmation prompt.
4. Reply "yes" to confirm the trade order.

Expected: Trade pre-validation should enforce positive quantities (> 0) and reject 0-share orders before prompting for confirmation. If execution fails or is rejected, the remaining cash balance reported to the user should reflect the actual current cash balance rather than $0.00.
Actual: Pre-validation checks `current_shares >= quantity` (0.0 >= 0 is True) and prompts the user for confirmation. Upon confirmation, execution fails, but `manager.py` defaults missing `cash_remaining` to 0.0, incorrectly reporting "**Remaining Cash Balance:** $0.00" despite the portfolio retaining its full cash balance.
Screenshot: screenshots/adv-002-zero-shares-zero-cash-reporting.png

History:
- qa: opened
- orchestrator: set FIX-READY (backend-dev: Added strict quantity > 0 validation and guaranteed cash_remaining returns actual current cash balance across all trade execution responses)
- qa: closed (retested and verified quantity > 0 validation and correct cash balance reporting in test_def_002_zero_quantity_trade_rejected_and_cash_reported)

## DEF-001: Substring Matching on Trade Confirmation Causes False Positive Trade Execution and Stale Pending State Leakage

- Status: CLOSED
- Severity: HIGH
- Found by: adversary (ADV-001)
- Phase: 1

Steps to reproduce:
1. Start the application and initiate a chat session.
2. Send a trade command: "Buy 10 shares of NVDA".
3. Receive the two-step trade confirmation prompt.
4. Send a follow-up message containing a word with "ok" as a substring, such as "Is tokenomics important?" or "What is the broker fee?".
5. Alternatively, send unrelated conversational queries and multiple turns later send "ok thank you".

Expected: The system should strictly match explicit confirmation keywords on word boundaries and invalidate/expire any pending trade state when an unrelated inquiry is received.
Actual: The check `any(w in cleaned for w in ["yes", "confirm", "proceed", "yep", "sure", "ok", "execute"])` matches substrings inside unrelated words like "tokenomics", immediately executing the trade order without genuine user consent. Additionally, `session.pending_trade` is never invalidated or expired when unrelated queries are received, allowing stale pending orders to be executed turns later.
Screenshot: screenshots/adv-001-unintended-trade-execution.png

History:
- qa: opened
- orchestrator: set FIX-READY (backend-dev: Updated manager.py with strict regex word-boundary matching and cleared pending_trade when unrelated queries are received)
- qa: closed (retested and verified regex word-boundary matching and pending_trade invalidation on unrelated queries in test_def_001_word_boundary_confirmation_and_unrelated_invalidation)
