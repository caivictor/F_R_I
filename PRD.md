---
tags: [prd, ai-build, finance]
status: Ready
---
# PRD: F.R.I. (Financial Research & Investment) AI Multi-Agent System

## 1. Product Vision & Overview
F.R.I. is an intelligent AI Agent chat companion designed for comprehensive financial research, equity analysis, and paper portfolio management. Users interact through a standard, clean AI chat interface with a **Manager Agent** (Main Agent companion) that autonomously spins up specialized worker sub-agents on-demand:
1. **Research Agent**: Scrapes and synthesizes live market and business news.
2. **Analysis Agent**: Conducts fundamental and quantitative equity evaluations.
3. **Investment Agent**: Manages paper trading portfolios, cash flows, and position tracking.

The system features robust long-context memory and persistent continuity across sessions backed by local SQLite storage, along with rolling multi-turn conversation context compression that preserves active entities, portfolio metrics, and prior research findings across turns and restarts.

## 2. Core Architecture & Agent Definitions

- **Manager Agent (Master Orchestrator & Chat Companion):**
  - **Role:** Primary Chat Companion, Autonomous Sub-Agent Delegator, Context & Memory Manager.
  - **Core Responsibilities:**
    1. **Autonomous Sub-Agent Delegation & Task Progress Streaming:**
       - Dynamically spins up specialized sub-agents on-demand based on user intent and workflow needs.
       - Streams live task progress badges and real-time step status to the user in the chat UI (e.g., `[Manager] Spinning up Research Agent...` -> `[Research Agent] Parsing top market themes...` -> `[Manager] Delegating AAPL to Analysis Agent...`).
       - Orchestrates single-agent queries, parallel sub-agent tasks, and sequential chains (e.g., *Market News -> Deep Equity Analysis -> Investment Recommendation*).
    2. **Long-Context Memory & Cross-Session Continuity:**
       - Persistently stores customer preferences, historical research threads, multi-company candidate sets, and past trade requests in SQLite.
       - Restores complete conversational memory and context across sessions and server restarts, enabling the user to seamlessly resume past threads.
    3. **Context Compression & Rolling Memory Management:**
       - Implements a rolling multi-turn conversation memory model with automated context compression.
       - Compresses long conversational histories while strictly preserving active entities, portfolio state, research dossiers, and pending confirmations.
    4. **Trade Confirmation Guardrail (Safety Interlock):**
       - Intercepts all BUY and SELL trade requests.
       - Prompts the Investment Agent for real-time market pricing and available cash balance.
       - Issues an explicit two-step confirmation prompt displaying live price estimates, quantity, total value, and available cash before execution.
       - Enforces strict cancellation/negation precedence over casual affirmation.
    5. **Self-Healing & Dynamic Unsticking Engine:**
       - Monitors sub-agent execution state and enforces strict tool timeouts (15–20 seconds).
       - Automatically retries failed sub-agent tasks up to 3 times with dynamic prompt adjustments and query rephrasing.
       - Gracefully reports root cause and options if a task fails after 3 retries.
    6. **Multi-Agent Synthesis & Executive Briefings:**
       - Synthesizes findings from Research, Analysis, and Investment sub-agents into clean, actionable executive summaries with Markdown tables and key takeaways.

- **Research Agent (Financial Data & News Gatherer):**
  - **Role:** Live News Discovery & Market Trend Aggregator.
  - **Data Source:** Google News Business RSS feeds (`https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en`) and HTML scraping via `feedparser`, `httpx`, and `beautifulsoup4` (Free / Zero API Key).
  - **Batch Cap & Throttling:** Filters and ranks the top 3 to 5 most prominent public companies per run to optimize latency and token budgets.
  - **Responsibilities:**
    1. Fetches and parses latest top business headlines on demand.
    2. Extracts article metadata: title, publisher, publication timestamp, summary snippet, and URL.
    3. Generates structured markdown summaries of major market themes and trending public companies.
    4. Hands off candidate company sets to the Analysis Agent and Manager Agent.

- **Analysis Agent (Quantitative & Fundamental Equity Analyst):**
  - **Role:** Fundamental Valuation & Quantitative Investment Dossiers.
  - **Asset Scope & Guardrails:** Restricts analysis strictly to US-listed public equities (NYSE/NASDAQ) trading in USD. Private companies (e.g., OpenAI, SpaceX, Stripe) and OTC/non-US listings are explicitly rejected.
  - **Data Ingestion Tooling:** Queries `yfinance` for fundamental statements, historical price data, and valuation multiples (15s request timeout; uses Previous Close for off-hours valuations).
  - **Core Long-Term Holding Evaluation Metrics:**
    1. **Profitability & Capital Efficiency:** ROIC, ROE, Operating Margin, Gross Margin consistency/expansion.
    2. **Solvency & Cash Generation:** Free Cash Flow (FCF), FCF Yield, Debt-to-Equity (D/E), Interest Coverage, Current & Quick Ratios.
    3. **Growth Trajectory:** Multi-year Revenue CAGR, Normalized Diluted EPS growth, 3–5 year FCF growth.
    4. **Valuation & Multiples:** Trailing P/E, Forward P/E, PEG Ratio, Price/FCF, EV/EBITDA, Dividend Yield & Payout Ratio.
    5. **Qualitative Moat & Risk:** Pricing power, switching costs, competitive moat, tailwinds, and regulatory/technological risks.
  - **Deliverable:** Generates structured "Long-Term Investment Dossiers" with Financial Health Scorecards and Bull/Bear risk analyses.

- **Investment Agent (Portfolio Manager & Execution Engine):**
  - **Role:** Paper Trading Execution, Portfolio Accounting, & Performance Tracking.
  - **Baseline Capital:** Initializes paper trading account with $100,000.00 USD baseline cash.
  - **Simulated Database Tracking (SQLite):**
    - Tracks positions: Ticker, Shares Owned, Average Cost Basis, Market Price (`yfinance`), Market Value, Unrealized P&L ($ / %), Cumulative Dividends, and Portfolio Allocation %.
    - Tracks transactions: Timestamp, Order Type (BUY / SELL / DIVIDEND / DEPOSIT / WITHDRAW / RESET), Ticker, Quantity, Price, Total Value, and Notes.
  - **Core Responsibilities:**
    1. Validates and executes BUY/SELL orders against available cash and share balances.
    2. Supports cash management operations (deposit, withdraw, reset to $100k).
    3. Real-time portfolio valuation (NAV, total return, realized/unrealized P&L, cash allocation).
    4. Dividend and yield-on-cost tracking.
    5. Formats markdown portfolio summaries and performance reports.

## 3. Interface, Memory & User Experience

- **Clean AI Chat Interface:**
  - Standard, minimalist financial terminal chat interface with real-time Markdown rendering for tables, financial scorecards, and dossiers.
  - Real-time animated sub-agent progress badges indicating live task status and delegation handoffs.
  - Starter prompt chips for rapid workflow initiation (e.g., "Scan Market News", "Analyze AAPL", "View Portfolio", "Buy 10 NVDA").

- **Long Context & Persistent Continuity:**
  - Persistent SQLite storage for conversational sessions, retaining user preferences, past research threads, multi-company candidate sets, and previous trade requests.
  - Instant context restoration upon user return or server restart, preserving conversational continuity without context loss.

- **Context Compression & Memory Management:**
  - Automatic sliding-window context compression: As multi-turn conversations expand, older dialogue turns are compressed into compact semantic summaries while preserving key entities (active tickers, portfolio state, financial metrics, and user instructions).
  - High-fidelity entity retention ensures references like "it", "that company", or "the second stock we discussed" resolve accurately even in lengthy sessions.

- **Obsidian & Markdown Export:**
  - One-click copy and export of complete research dossiers, market digests, and portfolio reports formatted in Obsidian-compatible Markdown with YAML frontmatter tags.

- **Persona Management Panel:**
  - Dedicated settings modal allowing inspection and customization of system prompts for the Manager, Research, Analysis, and Investment agents.
  - Fail-safe "Reset to Default" button per agent to revert any modified persona to safe defaults.

## 4. Technical Stack & Environment Constraints

- **Single-Process Lightweight Architecture:**
  - Python 3.10+ virtual environment (`venv`) with zero external database daemons or mandatory Docker overhead.
  - FastAPI backend directly serves pre-compiled React 18 + Tailwind CSS production assets from `/` and REST/SSE endpoints under `/api`.
- **Backend Framework & Tooling:**
  - FastAPI, Pydantic, `httpx`, `feedparser`, `beautifulsoup4`, `yfinance`, Google Gemini Flash API.
- **Frontend Stack:**
  - React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Markdown renderer (`react-markdown`).
- **Database & Storage (SQLite):**
  - WAL mode enabled (`PRAGMA journal_mode = WAL;`, `PRAGMA busy_timeout = 5000;`).
  - Schema tables:
    1. `chat_sessions` & `chat_messages`: Multi-session chat history and token logs.
    2. `conversation_memory`: Persistent context, active entity candidate sets, user preferences, and compressed summaries.
    3. `llm_debug_logs`: Turn-level context, prompts, system instructions, and execution latencies.
    4. `positions`: Asset holdings, cost basis, shares, dividends.
    5. `transactions`: Trade and cash flow audit history.
    6. `portfolio_summary`: Real-time cash balance ($100k initial) and realized gains.
    7. `agent_personas`: System prompt configurations and defaults.
- **Network & Tool Timeouts:**
  - 15–20 seconds hard timeout per external request (`yfinance`, Google News RSS).

## 5. Phased Execution Roadmap

### Phase 1: Core Orchestrator, Chat Interface & Sub-Agent Wiring
- Implement FastAPI server, React chat interface, and Manager Agent.
- Establish autonomous dynamic sub-agent dispatch and streaming progress badges.
- Setup SQLite conversation memory, session persistence, and persona manager.

### Phase 2: Live Market Research & Quantitative Equity Analysis
- Implement Research Agent with Google News RSS parser and top 3–5 company ranking.
- Implement Analysis Agent with `yfinance` fundamental metrics (ROIC, FCF, D/E, valuation multiples).
- Implement dynamic 3x retry self-healing engine and private company guardrails.

### Phase 3: Paper Portfolio, Cash Management & Trade Confirmation
- Implement Investment Agent with SQLite persistence ($100k cash default), BUY/SELL validation, and 2-step trade confirmation.
- Implement context compression engine for rolling multi-turn continuity.

### Phase 4: UX Polish, Long-Context Continuity & Obsidian Export
- Refine long-context memory retrieval across sessions and server restarts.
- Polish Markdown rendering, live sub-agent status badges, and one-click Obsidian export.
- Complete comprehensive end-to-end verification and adversarial review.

## 6. Documentation & Maintenance Mandates
1. **`INSTALL.md`**: Multi-platform installation guide (Linux, macOS, Windows) and single-command launcher instructions.
2. **`USER_MANUAL.md`**: Operational guide covering chat workflows, sub-agent capabilities, paper trading, and persona customization.
3. **`SECURITY.md`**: Security vulnerability ledger, posture audit findings, and development guardrail validations.
4. **`DEFECTS.md` & `ADVERSARIAL_REVIEW.md`**: QA and adversarial tracking ledgers.
5. **`README.md` & `CHANGELOG.md`**: High-level system architecture, repository structure, and version history.
