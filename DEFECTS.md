# DEFECTS

## DEF-015: Conversational Context Loss and False Ticker Extraction on Quantifiers ("all", "all five") During Multi-Agent Discovery

- Status: CLOSED
- Severity: HIGH
- Found by: user
- Phase: 4

Steps to reproduce:
1. Start the application and open a chat session.
2. Send a prompt to initiate discovery: "Discover market news and analyze trending companies".
3. Observe that the Research Agent finds 5 top companies from Google News (e.g., NVDA, AAPL, MSFT, AMZN, GOOGL), but the Analysis Agent only evaluates the first candidate.
4. In the next turn, send a follow-up query: "Why didn't you research all five recommendations?" or "Analyze all five of them".
5. Observe that the system erroneously extracts "ALL" (The Allstate Corporation NYSE: ALL) as a ticker symbol and runs equity analysis on Allstate, losing context of the 5 discovered research companies and failing to answer the user's inquiry.

Expected:
1. Quantifier and pronoun phrases ("all", "all 5", "all five", "them all", "the rest", "others", "everything") must not be extracted as the ticker symbol `$ALL` unless explicitly formatted as a ticker (e.g. `$ALL` or `Allstate`).
2. `SessionState` must retain all discovered companies and research candidates in conversational memory (`last_discovered_companies` / `last_discovered_tickers`).
3. The Manager Agent should recognize multi-item references and execute multi-asset evaluations/comparisons across all discovered candidates when requested.
4. The Manager Agent must support conversational history management with context compression so long multi-turn sessions retain context and converse naturally like a supervisor AI.
Actual:
"all" in "all five recommendations" is extracted as ticker "ALL" (Allstate Corp), replacing conversational context with an unintended deep dive on Allstate.

History:
- qa: opened
- orchestrator: set FIX-READY (backend-dev: Added quantifier stopword filtering, session memory for discovered candidates, multi-asset comparative analysis, and automatic context compression)
- qa: closed (retested and verified multi-item candidate analysis, quantifier protection against $ALL, and context compression in test_def_015_conversational_context_retention_and_quantifier_protection)

## DEF-014: Unanchored Substring Matching in Company Alias Resolution Overrides Distinct Tickers and Company Names

- Status: CLOSED
- Severity: MEDIUM
- Found by: adversary (ADV-014)
- Phase: 4

Steps to reproduce:
1. Start the application backend and initiate a chat session.
2. Request fundamental analysis for a public company whose name or ticker contains a known company alias as a substring (e.g., "Analyze AMDOCS fundamentals", "Analyze INTELLECT", "Analyze METAMATERIALS", or "Analyze CHASEN").
3. Observe the resolved ticker symbol and analysis target.

Expected: `_resolve_ticker` should use exact or word-boundary matching when mapping company aliases so that distinct equities and companies containing alias substrings (such as AMDOCS, INTELLECT, METAMATERIALS, CHASEN) are not falsely mapped to other entities.
Actual: In `backend/app/agents/analysis.py`, `_resolve_ticker` iterates through `COMPANY_ALIASES` checking `if alias in cleaned: return symbol` without word-boundary constraints. Consequently, "AMDOCS" is rewritten to "AMD" (Advanced Micro Devices), "INTELLECT" is rewritten to "INTC" (Intel), "METAMATERIALS" is rewritten to "META" (Meta Platforms), and "CHASEN" is rewritten to "JPM" (JPMorgan Chase).

History:
- qa: opened
- orchestrator: set FIX-READY (backend-dev: Updated _resolve_ticker to match COMPANY_ALIASES using regex word boundaries preventing false substring overrides)
- qa: closed (retested and verified word boundary matching on company aliases in test_def_014_word_boundary_company_alias_resolution)

## DEF-013: Affirmation Preamble in Contrary and Cancellation Commands Triggers False Positive Trade Confirmation Execution

- Status: CLOSED
- Severity: HIGH
- Found by: adversary (ADV-013)
- Phase: 4

Steps to reproduce:
1. Start the application backend and initiate a chat session.
2. Submit a trade command to trigger the two-step confirmation prompt (e.g., "Buy 10 shares of NVDA").
3. In the confirmation turn, submit a contradictory or cancellation phrase containing an affirmation preamble or contrary intent (e.g., "ok please cancel", "sure, cancel that order", "proceed to analyze AAPL instead", or "ok, do not execute this").
4. Observe the system response.

Expected: The confirmation interlock should prioritize explicit cancellation keywords or check for negation/compound commands, cancelling or clearing the pending trade when the user requests cancellation or changes intent, rather than executing the order.
Actual: In `backend/app/agents/manager.py`, the condition `if re.search(r"\b(yes|confirm|proceed|yep|sure|ok|execute)\b", cleaned, re.IGNORECASE)` is evaluated first. Because "ok", "sure", or "proceed" is matched as a standalone token anywhere in the prompt, prompts like "ok please cancel", "sure, cancel that order", and "proceed to analyze AAPL instead" are interpreted as affirmative confirmations, executing the pending trade immediately against user intent.

History:
- qa: opened
- orchestrator: set FIX-READY (backend-dev: Reordered trade confirmation evaluation to prioritize cancellation and contrary tokens before affirmation)
- qa: closed (retested and verified contrary/cancellation precedence during trade confirmation in test_def_013_contrary_cancellation_precedence_in_trade_confirmation)

## DEF-012: SQLite Database Connections Lack WAL Mode and Busy Timeout Pragma Causing Potential Locking Contention

- Status: CLOSED
- Severity: LOW
- Found by: adversary (ADV-012)
- Phase: 3

Steps to reproduce:
1. Initialize the SQLite database connection in `backend/app/db/database.py`.
2. Inspect connection pragmas and journal mode during concurrent agent queries and background write operations.

Expected: In a single-process architecture serving simultaneous agent requests, background tasks, and web clients, SQLite connections should configure `PRAGMA journal_mode = WAL;` and `PRAGMA busy_timeout = 5000;` on connection to avoid SQLite database lock contention and maximize read/write concurrency.
Actual: Connections are established via raw `sqlite3.connect(self.db_path, check_same_thread=False)` with default journal mode (`DELETE`) and without configuring WAL mode or busy timeout pragmas.

History:
- qa: opened
- orchestrator: set FIX-READY (backend-dev: Configured timeout=5.0 along with PRAGMA journal_mode = WAL and PRAGMA busy_timeout = 5000 in backend/app/db/database.py)
- qa: closed (retested and verified WAL journal mode and 5000ms busy timeout pragma on database connections in test_def_012_sqlite_wal_mode_and_busy_timeout_pragma)

## DEF-011: Fractional Position Deletion Threshold in Sell Execution Silently Purges Remaining Micro-Holdings

- Status: CLOSED
- Severity: MEDIUM
- Found by: adversary (ADV-011)
- Phase: 3

Steps to reproduce:
1. Start the application backend with a portfolio holding 1.0 share of an equity.
2. Execute a partial sell order for 0.99995 shares (or hold micro-fractional shares <= 0.0001).
3. Inspect the remaining holdings in the portfolio positions table.

Expected: The portfolio positions table should accurately record and retain fractional shareholdings down to floating point precision (or clean up only if `new_shares <= 0` / within floating-point epsilon like 1e-9).
Actual: In `backend/app/agents/investment.py` line 244, `if new_shares <= 0.0001:` triggers immediate and unconditional deletion of the position record (`self._db.delete_position(cleaned_ticker)`). As a result, a user selling 0.99995 shares has their remaining 0.00005 shares permanently wiped from their portfolio database record without realization or cash compensation.

History:
- qa: opened
- orchestrator: set FIX-READY (backend-dev: Adjusted sell position cleanup and share sufficiency checks to use 1e-9 epsilon)
- qa: closed (retested and verified retention of micro-fractional positions down to 1e-9 epsilon on partial sells in test_def_011_fractional_position_micro_holdings_retention)

## DEF-010: Negative, Zero, and Non-Finite Execution Prices Bypass Validation in Trade Execution Engine Causing Balance Inversion and SQLite Crash

- Status: CLOSED
- Severity: HIGH
- Found by: adversary (ADV-010)
- Phase: 3

Steps to reproduce:
1. Start the application backend.
2. Invoke `InvestmentAgent.execute_trade` with non-positive or non-finite price parameters (e.g., `price=-50.0`, `price=0.0`, `price=float('nan')`, or `price=float('inf')`).

Expected: `InvestmentAgent.execute_trade` should enforce strict positive finite price constraints (`price > 0` and `math.isfinite(price)`), rejecting invalid prices before attempting portfolio mutations or database transactions.
Actual: When `price <= 0` is passed, `execute_trade` executes the trade. A BUY order with negative price adds cash to the portfolio (negative cost basis reduces expenditure into a positive cash credit), allowing unauthorized balance expansion. When `price=float('nan')` is passed, `cash_balance` becomes NaN, causing `sqlite3.IntegrityError: NOT NULL constraint failed: portfolio_summary.cash_balance` and crashing with an unhandled exception.

History:
- qa: opened
- orchestrator: set FIX-READY (backend-dev: Enforced positive finite price validation in execute_trade and estimate_trade)
- qa: closed (retested and verified positive finite price validation constraints on execute_trade and estimate_trade preventing balance inversion and crash in test_def_010_negative_zero_and_nonfinite_price_validation)

## DEF-009: Private and Non-US Equities Bypass Guardrails in Direct Trade Parameter Extraction and Paper Execution

- Status: CLOSED
- Severity: HIGH
- Found by: adversary (ADV-009)
- Phase: 2

Steps to reproduce:
1. Start the application backend and open a chat session.
2. Submit direct trade order commands for known private companies or foreign assets (e.g. "Buy 10 shares of SpaceX", "Buy 5 shares of Stripe", "Buy 100 shares of 0700.HK").
3. Reply "yes" to confirm the trade order.

Expected: Trade intent pre-validation should enforce the same US-public equity guardrails as the Analysis Agent, rejecting private companies and foreign/OTC securities before issuing trade estimates or executing paper trades.
Actual: The trade workflow in `manager.py` does not invoke `_check_eligibility` on trade ticker targets. `InvestmentAgent.get_quote` defaults unknown and private tickers to `$100.00`, allowing users to confirm and execute paper purchases of private companies (SpaceX, Stripe, etc.) into their active portfolio.
Screenshot: screenshots/adv-009-private-stock-spacex-trade-execution.png

History:
- qa: opened
- orchestrator: set FIX-READY (backend-dev: Integrated _check_eligibility pre-validation into ManagerAgent trade handling and expanded regex matching to reject private companies and foreign/OTC listings)
- qa: closed (retested and verified pre-validation rejection for private companies and non-US listings prior to confirmation in test_def_009_trade_eligibility_guardrail_rejects_private_and_non_us)

## DEF-008: Unhandled TypeError in RSS News Feed Parser on Malformed Entries with Null Metadata

- Status: CLOSED
- Severity: MEDIUM
- Found by: adversary (ADV-008)
- Phase: 2

Steps to reproduce:
1. Start the application backend and initiate market research news collection.
2. Ingest an RSS feed payload containing entries where title or summary is None or contains unexpected null dictionary values (e.g. `{"title": None, "link": "..."}`).

Expected: The RSS parser should gracefully sanitize all fields, defaulting missing or null titles and summaries to safe fallback strings without raising unhandled runtime exceptions.
Actual: In `backend/app/agents/research.py`, `fetch_rss_feed` calls `entry.get("title", "")` which returns `None` when `'title': None` is present in the feed dictionary. Passing `raw_title = None` to `_parse_publisher` causes `if " - " in title:` to raise `TypeError: argument of type 'NoneType' is not iterable`, crashing the feed ingestion pipeline.

History:
- qa: opened
- orchestrator: set FIX-READY (backend-dev: Hardened _parse_publisher, _clean_html, and fetch_rss_feed against None and non-string metadata values)
- qa: closed (retested and verified safe fallback handling for null title, summary, and publisher metadata without TypeError in test_def_008_rss_parser_handles_null_title_and_summary)

## DEF-007: Fallback Exception Swallowing in Analysis and Research Sub-Agents Bypasses Manager 3x Retry Self-Healing and Generates Phantom Dossiers for Non-Existent Tickers

- Status: CLOSED
- Severity: HIGH
- Found by: adversary (ADV-007)
- Phase: 2

Steps to reproduce:
1. Start the application backend and initiate a chat session.
2. Request analysis for a non-existent or invalid stock ticker (e.g. "Analyze FAKE_XYZ_TICKER_123") or simulate external API network failures/timeouts against yfinance and Google News RSS.

Expected: When sub-agents encounter errors, timeouts, or invalid assets, the error should propagate to the Manager Agent's self-healing engine (`_execute_subagent_with_healing`) to trigger up to 3 dynamic query retries and adaptations before failing gracefully. Non-existent tickers should be reported as invalid.
Actual: `analyze_company` wraps metric extraction in a broad `except Exception:` block and synthesizes a fake successful dossier (`current_price: $100.00`, `market_cap: 100.0B`, `roic: 22.5%`, `status: "success"`) for non-existent and delisted tickers. Similarly, `gather_market_news` catches exceptions and returns mock fallback articles with `status: "success"`. Because sub-agents return `status: "success"` on attempt 1 despite network failures or invalid data, the Manager 3x retry self-healing loop is completely bypassed and never executes retries or adaptations.

History:
- qa: opened
- orchestrator: set FIX-READY (backend-dev: Removed synthetic fallback exception swallowing; invalid tickers and missing quotes raise ValueError and trigger Manager 3x retry healing)
- qa: closed (retested and verified sub-agent error propagation, invalid ticker handling, and 3x Manager retry healing execution in test_def_007_subagents_propagate_errors_for_manager_self_healing)

## DEF-006: Substring and Inverted Inclusion Checks in Private Company Guardrail Invalidate Legitimate US Public Equities

- Status: CLOSED
- Severity: HIGH
- Found by: adversary (ADV-006)
- Phase: 2

Steps to reproduce:
1. Start the application backend and initiate a chat session.
2. Send a query requesting fundamental analysis for US public companies whose ticker symbols or names are substrings of known private companies (e.g., "Analyze DIS fundamentals and moat" for The Walt Disney Company, "Analyze V", "Analyze CAN", "Analyze RE", or "Analyze OPEN").

Expected: The Analysis Agent should evaluate eligible US public equities listed on NYSE/NASDAQ while only rejecting actual private companies.
Actual: In `backend/app/agents/analysis.py`, `_check_eligibility` tests `if priv_key in cleaned or cleaned in priv_key:`. The inverted check `cleaned in priv_key` checks whether the user's input ticker is a substring of any private company name. Consequently, $DIS is rejected claiming "Discord is a private company", $V and $CAN are rejected claiming "Canva is a private company", $RE is rejected claiming "Revolut is a private company", and $OPEN is rejected claiming "OpenAI is a private company".
Screenshot: screenshots/adv-006-public-stock-disney-rejected-as-discord.png

History:
- qa: opened
- orchestrator: set FIX-READY (backend-dev: Replaced substring/containment checks with regex word boundary matching, ensuring valid US public tickers like DIS, V, CAN, RE, OPEN pass eligibility)
- qa: closed (retested and verified word-boundary eligibility check allows valid public tickers DIS, V, CAN, RE, OPEN while rejecting private companies in test_def_006_private_company_word_boundary_and_valid_tickers)

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
