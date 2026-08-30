# Changelog: F.R.I. AI Multi-Agent System

All notable changes to this project are documented below.

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
