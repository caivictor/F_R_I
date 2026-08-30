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

## ADV-006: Substring and Inverted Inclusion Checks in Private Company Guardrail Invalidate Legitimate US Public Equities

- Session: phase-2 gate
- Suggested severity: HIGH

What I did: Requested fundamental analysis for standard US-listed public companies whose ticker symbols or names are substrings of known private companies (e.g., "Analyze DIS fundamentals and moat" for The Walt Disney Company, "Analyze V" for Visa Inc., "Analyze CAN" for Canaan Inc., "Analyze RE" for Everest Group, or "Analyze OPEN" for Opendoor Technologies).
Expected: The Analysis Agent should evaluate eligible US public equities listed on NYSE/NASDAQ while only rejecting actual private companies.
Actual: In `backend/app/agents/analysis.py`, `_check_eligibility` tests `if priv_key in cleaned or cleaned in priv_key:`. The inverted check `cleaned in priv_key` checks whether the user's input ticker is a substring of any private company name. Consequently, $DIS is rejected claiming "Discord is a private company", $V and $CAN are rejected claiming "Canva is a private company", $RE is rejected claiming "Revolut is a private company", and $OPEN is rejected claiming "OpenAI is a private company".
Screenshot: screenshots/adv-006-public-stock-disney-rejected-as-discord.png

Disposition: ACCEPTED -> DEF-006

## ADV-007: Fallback Exception Swallowing in Analysis and Research Sub-Agents Bypasses Manager 3x Retry Self-Healing and Generates Phantom Dossiers for Non-Existent Tickers

- Session: phase-2 gate
- Suggested severity: HIGH

What I did: Tested the system with non-existent or invalid stock tickers (e.g. "Analyze FAKE_XYZ_TICKER_123") and simulated network timeouts / external API connection failures against yfinance and Google News RSS feeds.
Expected: When sub-agents fail or encounter network timeouts/invalid assets, errors should propagate to the Manager Agent's self-healing engine (`_execute_subagent_with_healing`) to execute up to 3 dynamic query retries and rephrasings, ultimately presenting a graceful failure report if recovery fails. Non-existent tickers should be reported as invalid.
Actual: `analyze_company` wraps metric extraction in a broad `except Exception:` block and synthesizes a fake successful dossier (`current_price: $100.00`, `market_cap: 100.0B`, `roic: 22.5%`, `status: "success"`) for non-existent and delisted tickers. Similarly, `gather_market_news` catches exceptions and returns mock fallback articles with `status: "success"`. Because sub-agents return `status: "success"` on attempt 1 despite network failures or invalid data, the Manager 3x retry self-healing loop is completely bypassed and never executes retries or adaptations.

Disposition: ACCEPTED -> DEF-007

## ADV-008: Unhandled TypeError in RSS News Feed Parser on Malformed Entries with Null Metadata

- Session: phase-2 gate
- Suggested severity: MEDIUM

What I did: Ingested RSS feed payloads containing entries where title or summary is None or structured with unexpected null dictionary values (e.g. `{"title": None, "link": "..."}`).
Expected: The RSS parser should gracefully sanitize all fields, defaulting missing or null titles and summaries to safe fallback strings without raising unhandled runtime exceptions.
Actual: In `backend/app/agents/research.py`, `fetch_rss_feed` calls `entry.get("title", "")` which returns `None` when `'title': None` is present in the feed dictionary. Passing `raw_title = None` to `_parse_publisher` causes `if " - " in title:` to raise `TypeError: argument of type 'NoneType' is not iterable`, crashing the feed ingestion pipeline.

Disposition: ACCEPTED -> DEF-008

## ADV-009: Private and Non-US Equities Bypass Guardrails in Direct Trade Parameter Extraction and Paper Execution

- Session: phase-2 gate
- Suggested severity: HIGH

What I did: Submitted direct trade order commands for known private companies and foreign assets (e.g. "Buy 10 shares of SpaceX", "Buy 5 shares of Stripe", "Buy 100 shares of 0700.HK"), followed by confirming the trade ("yes").
Expected: Trade intent pre-validation should enforce the same US-public equity guardrails as the Analysis Agent, rejecting private companies and foreign/OTC securities before issuing trade estimates or executing paper trades.
Actual: The trade workflow in `manager.py` does not invoke `_check_eligibility` on trade ticker targets. `InvestmentAgent.get_quote` defaults unknown and private tickers to `$100.00`, allowing users to confirm and execute paper purchases of private companies (SpaceX, Stripe, etc.) into their active portfolio.
Screenshot: screenshots/adv-009-private-stock-spacex-trade-execution.png

Disposition: ACCEPTED -> DEF-009

## ADV-010: Negative, Zero, and Non-Finite Execution Prices Bypass Validation in Trade Execution Engine Causing Balance Inversion and SQLite Crash

- Session: phase-3 gate
- Suggested severity: HIGH

What I did: Injected non-positive and non-finite price parameters into `InvestmentAgent.execute_trade` (e.g., `price=-50.0`, `price=0.0`, `price=float('nan')`, `price=float('inf')`).
Expected: `InvestmentAgent.execute_trade` should enforce strict positive finite price constraints (`price > 0` and `math.isfinite(price)`), rejecting invalid prices before attempting portfolio mutations or database transactions.
Actual: When `price <= 0` is passed, `execute_trade` executes the trade. A BUY order with negative price adds cash to the portfolio (negative cost basis reduces expenditure into a positive cash credit), allowing unauthorized balance expansion. When `price=float('nan')` is passed, `cash_balance` becomes NaN, causing `sqlite3.IntegrityError: NOT NULL constraint failed: portfolio_summary.cash_balance` and crashing with an unhandled exception.

Disposition: ACCEPTED -> DEF-010

## ADV-011: Fractional Position Deletion Threshold in Sell Execution Silently Purges Remaining Micro-Holdings

- Session: phase-3 gate
- Suggested severity: MEDIUM

What I did: Owned 1.0 share of equity and executed a partial sell order for 0.99995 shares (or purchased/owned fractional shares <= 0.0001).
Expected: The portfolio positions table should accurately record and retain fractional shareholdings down to floating point precision (or clean up only if `new_shares <= 0` / within floating-point epsilon like 1e-9).
Actual: In `backend/app/agents/investment.py` line 244, `if new_shares <= 0.0001:` triggers immediate and unconditional deletion of the position record (`self._db.delete_position(cleaned_ticker)`). As a result, a user selling 0.99995 shares has their remaining 0.00005 shares permanently wiped from their portfolio database record without realization or cash compensation.

Disposition: ACCEPTED -> DEF-011

## ADV-012: SQLite Database Connections Lack WAL Mode and Busy Timeout Pragma Causing Potential Locking Contention

- Session: phase-3 gate
- Suggested severity: LOW

What I did: Evaluated database connection initialization in `backend/app/db/database.py` for multi-threaded/multi-agent concurrent operations.
Expected: In a single-process architecture serving simultaneous agent requests, background tasks, and web clients, SQLite connections should configure `PRAGMA journal_mode = WAL;` and `PRAGMA busy_timeout = 5000;` on connection to avoid SQLite database lock contention and maximize read/write concurrency.
Actual: Connections are established via raw `sqlite3.connect(self.db_path, check_same_thread=False)` with default journal mode (`DELETE`) and without configuring WAL mode or busy timeout pragmas.

Disposition: ACCEPTED -> DEF-012


