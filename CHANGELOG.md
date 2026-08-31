# Changelog: F.R.I. AI Multi-Agent System

All notable changes to this project are documented below.

---

## [1.1.1] - 2026-08-30

### Turn-Level Debug Logging, Context Inspector & Session Deletion Fixes
- **DEF-016 Debug & History Fix**: Added turn-level automatic debug logging in `llm_debug_logs` across all discovery, analysis, trade, and conversational turns.
- **Tabbed Debug Modal Inspector**: Added tabbed navigation in `DebugModal` (LLM Context & Prompts, Conversation Transcript, Active Memory State) with a session selector dropdown.
- **Safe Debug Endpoint**: Handled fresh/uninitialized session IDs gracefully in `GET /api/chat/sessions/{session_id}/debug` without returning 404.
- **Reliable Session Deletion**: Fixed session deletion in `SessionsModal` and `Database.delete_session` to cleanly remove associated messages, conversation memory, debug logs, and session records.
- **Conversational Reasoning Loop**: Enhanced Manager Agent free-form conversation reasoning to construct full context prompts (including active tickers, candidates, and portfolio state) and respond naturally.

---

## [1.1.0] - 2026-08-30

### Persistent Chat Continuity, Multi-Session History & Security Posture UI
- **Cross-Session SQLite Continuity**: Added persistent database backing for `chat_sessions`, `chat_messages`, and `conversation_memory` so conversations, entities, and summaries are preserved across reboots.
- **Multi-Session History Switcher UI**: Added `SessionsModal` and History button in terminal header allowing users to browse, switch between, and manage persistent conversations.
- **Security Posture & Guardrails Modal**: Added `SecurityModal` and `GET /api/security/audit` endpoint displaying live security controls (WAL mode, timeouts, trade interlocks, secret redaction, and prompt sanitization).
- **Sub-Agent Progress & Companion Architecture**: Aligned system architecture with the updated PRD: an AI companion that autonomously spins up specialized worker sub-agents on demand with live UI progress trace.

---

## [1.0.1] - 2026-08-30

### Context Memory, Multi-Candidate Evaluation & Security Agent
- **DEF-015 Context Retention**: Resolved context loss during multi-turn research workflows by persisting all discovered company candidates in `SessionState` (`last_discovered_companies` / `last_discovered_tickers`).
- **Quantifier Stopword Protection**: Guarded terms (`all`, `all five`, `them all`, `the rest`, `others`, `both`, `each`) against being falsely extracted as ticker symbol `$ALL` (Allstate Corp).
- **Multi-Asset Comparative Financial Scorecards**: Added capability for Manager Agent to perform and display multi-company comparative evaluations across all candidates when requested.
- **Conversational Context Compression**: Implemented automatic context compression in `SessionState` preserving active focus entities, candidates, and portfolio states over long sessions.
- **Security Agent Role**: Added dedicated `security` subagent definition, initialized `SECURITY.md` vulnerability ledger, and configured strict security auditing workflows.

---

## [1.0.0] - 2026-08-29

### Phase 1: Proof of Concept & Core Agent Wiring
- Initialized FastAPI backend and React + TypeScript + Tailwind CSS financial terminal frontend.
- Implemented Manager Agent architecture with intent routing, session memory, entity resolution, and two-step trade confirmation interlocks.
- Implemented Server-Sent Events (SSE) streaming (`POST /api/chat/stream`) and REST chat endpoint (`POST /api/chat`).
- Implemented agent persona management (`GET /api/personas`, `POST /api/personas`, `POST /api/personas/reset`) with reset-to-default capability.
- Established Playwright E2E suite and Vitest frontend component tests.
- Addressed initial adversary findings DEF-001 through DEF-005.

### Phase 2: Agent Tooling & Real Data Integration
- Built Research Agent with live Google News Business RSS parsing (`httpx`, `feedparser`, `beautifulsoup4`) with 15s timeout and Top 3 to 5 prominent company ranking.
- Equipped Analysis Agent with `yfinance` quantitative evaluation tools with 15s timeout, off-hours Previous Close support, and strict US public equity filtering (rejecting private companies and OTC listings).
- Implemented fundamental scorecard metrics: ROIC, ROE, Free Cash Flow, FCF Yield, Debt-to-Equity, Interest Coverage, Quick/Current ratios, Revenue CAGR, EPS growth, Trailing/Forward P/E, PEG, and EV/EBITDA.
- Implemented Manager Agent Self-Healing Engine with automated 3x retry on sub-agent failure and dynamic parameter adaptation.
- Resolved and verified edge defects DEF-006 through DEF-009.

### Phase 3: Portfolio Tracking & Local Database Persistence
- Implemented local SQLite database with `portfolio_summary` ($100,000 baseline cash), `positions`, `transactions`, and `agent_personas` tables.
- Equipped Investment Agent with full paper trading capabilities: BUY/SELL order execution, weighted average cost basis calculations, realized gain/loss tracking, and cash adjustments (deposit, withdraw, reset).
- Implemented dividend distribution logging and cumulative yield on cost tracking.
- Added live portfolio valuation calculating Net Asset Value (NAV), unrealized P/L, and portfolio allocation percentages.
- Hardened database concurrency with `PRAGMA journal_mode = WAL` and `PRAGMA busy_timeout = 5000`.
- Resolved and verified defects DEF-010 through DEF-012.

### Phase 4: UX Polish, Session Export, Single-Process Static Serving, & Documentation
- Built production static web distribution in `frontend/dist/` directly served by FastAPI at root `/`.
- Polished Markdown financial tables rendering in chat interface.
- Implemented Obsidian-compatible Markdown export utility with YAML frontmatter tags and execution traces.
- Created single-command execution scripts `start.sh` (Linux/macOS) and `start.bat` (Windows).
- Authored comprehensive documentation: `INSTALL.md`, `USER_MANUAL.md`, `README.md`, and `CHANGELOG.md`.
- Completed full regression test run across all 56 backend tests, 18 frontend unit tests, and 22 Playwright E2E browser tests.
