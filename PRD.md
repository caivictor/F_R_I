---
tags: [prd, ai-build, finance]
status: Ready
---
# PRD: F.R.I. (Financial Research & Investment) AI Multi-Agent System

## 1. Overview
A standalone web application powered by a multi-agent AI system. The application serves as an automated financial research and portfolio management assistant. The user interacts entirely via a chat interface with a Manager Agent, which delegates tasks to specialized sub-agents to gather data, analyze investments, and track portfolio performance.

## 2. Core Architecture & Agent Definitions

- **Manager Agent (Model: Gemini Pro Latest):**
  - **Role:** Master Orchestrator, User Interface Proxy, & System Supervisor.
  - **Core Responsibilities:**
    1. **Intelligent Intent Routing & Workflow Chaining:**
       - Natively parses free-form natural language to route tasks to sub-agents:
         - *Market exploration / news query* -> Delegates to **Research Agent**.
         - *Specific ticker / company deep dive* -> Delegates directly to **Analysis Agent**.
         - *Portfolio balance, performance, cash adjustments, or trade execution* -> Delegates to **Investment Agent**.
         - *End-to-End Discovery Pipeline* (e.g., "Find top tech stories and analyze promising stocks") -> Orchestrates a sequential chain: **Research -> Analysis -> Investment recommendation**.
    2. **Trade Confirmation Guardrail (Safety Interlock):**
       - Intercepts all trade orders (e.g., "Buy 10 shares of NVDA").
       - Queries the Investment Agent for current market pricing and available cash balance.
       - Generates an explicit, clear two-step confirmation prompt (e.g., *"You have $100,000 cash. Buying 10 shares of NVDA at $125/share will cost ~$1,250. Confirm purchase? [Yes / No]"*) before executing.
    3. **Conversational Memory & Pronoun/Entity Resolution:**
       - Retains conversational context across multi-turn dialogues, correctly resolving references and pronouns (e.g., "Analyze Apple" followed by "What is its cost basis in my portfolio?" or "Buy 15 shares of it").
    4. **Multi-Agent Synthesis & Executive Briefings:**
       - Ingests raw analytical reports, tables, and news digests from sub-agents and synthesizes them into concise, structured executive summaries before presenting them to the user.
    5. **Self-Healing & Unsticking Engine:**
       - Monitors sub-agent execution state and enforces strict tool timeouts (15–20 seconds).
       - Automatically retries failed sub-agent tasks up to 3 times with dynamically adjusted prompts, query rephrasing, or fallback parameters.
       - If a failure persists after 3 retries, gracefully reports the root cause in the chat UI and requests user clarification instead of crashing.
    6. **Real-Time Step-by-Step Status Broadcasting:**
       - Emits real-time progress events to the web UI to provide transparency during multi-step runs (e.g., `[Manager] Initiating news scan with Research Agent...` -> `[Manager] Handing off AAPL to Analysis Agent...`).

- **Research Agent (Model: Gemini Flash Latest):**
  - **Role:** Financial Data & News Gatherer.
  - **Data Source (MVP):** Google News Business Section.
  - **Access Mechanism:** Free / No-API-Key approach using Google News RSS feeds (`https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en`) and HTML scraping with `feedparser`, `httpx`, and `beautifulsoup4`.
  - **Batch Cap & Throttling:** Filters and ranks the **Top 3 to 5 most prominent public companies** per run to control latency, rate limits, and token usage (overrideable via user prompt).
  - **Responsibilities:**
    1. Fetches and parses the latest top business and market headlines on demand without requiring paid API keys.
    2. Extracts essential metadata: title, source publisher, publication timestamp, summary snippet, and article URL.
    3. Synthesizes and filters the raw news feed into a structured markdown report highlighting major market themes and trending public companies.
    4. Passes the consolidated research briefing downstream to the Analysis Agent.

- **Analysis Agent (Model: Gemini Flash Latest):**
  - **Role:** Quantitative & Fundamental Equity Analyst.
  - **Asset Scope & Guardrails:** Enforces a strict filter for US-listed public equities (NYSE/NASDAQ) trading in USD. Private companies (e.g., OpenAI, SpaceX, Stripe) and non-US OTC listings are explicitly flagged and excluded.
  - **Data Ingestion Tooling:** Uses `yfinance` to retrieve historical market data, fundamental financial statements (Income Statement, Balance Sheet, Cash Flow), and valuation multiples (15s request timeout).
  - **Off-Hours Pricing:** Uses Previous Market Close prices for valuations and order estimations when markets are closed or over weekends.
  - **Core Long-Term Holding Evaluation Metrics:**
    1. **Profitability & Capital Efficiency (The Moat Indicators):**
       - Return on Invested Capital (ROIC) & Return on Equity (ROE) (identifying high returns on reinvested capital).
       - Operating Margin and Gross Margin consistency/expansion over 3-5 years.
    2. **Cash Generation & Financial Health (Solvency & Resilience):**
       - Free Cash Flow (FCF) and Free Cash Flow Yield (FCF / Market Cap).
       - Total Debt-to-Equity (D/E) ratio and Interest Coverage ratio (assessing leverage and debt safety).
       - Current & Quick Ratios (short-term liquidity buffer).
    3. **Growth & Compounding Consistency:**
       - Multi-year Revenue CAGR and Normalized Diluted EPS growth.
       - Free cash flow growth trajectory over 3-5 years.
    4. **Valuation & Entry Safety:**
       - Trailing P/E, Forward P/E, and PEG Ratio (Price/Earnings to Growth).
       - Price-to-Free-Cash-Flow (P/FCF) and EV/EBITDA ratios.
       - Dividend Yield & Payout Ratio (if applicable).
    5. **Qualitative Moat & Risk Assessment:**
       - Competitive advantages (pricing power, network effects, high switching costs).
       - Industry tailwinds vs. key regulatory or technological disruption risks.
  - **Output Deliverable:** Generates a structured "Long-Term Investment Dossier" in Markdown featuring:
    - Company Name & Ticker Symbol
    - Executive Summary & Recent News Context
    - Financial Health Scorecard (Key Metrics Table)
    - Core Investment Thesis (Why this is a 3-5+ year compounder)
    - Bull vs. Bear Risk Analysis

- **Investment Agent (Model: Gemini Flash Latest):**
  - **Role:** Portfolio Manager & Execution Engine.
  - **Default Bootstrap:** Initializes the paper-trading account with a default balance of **$100,000.00 USD**.
  - **Simulated Database Tracking (SQLite):**
    - Manages a persistent SQLite database storing cash balance, asset positions, and historical transaction logs.
    - **Data Tracked per Asset:**
      - Ticker Symbol & Asset Name
      - Total Shares Owned
      - Average Cost Basis per Share & Total Invested Amount
      - Current Market Price & Current Market Value (fetched via `yfinance`)
      - Unrealized Profit/Loss ($ and %)
      - Cumulative Dividends Received & Yield on Cost
      - Portfolio Allocation Percentage (% of total portfolio)
    - **Transaction History Log:**
      - Timestamp, Order Type (BUY / SELL / DIVIDEND / DEPOSIT / WITHDRAW / RESET), Ticker, Quantity, Price per Share, Total Transaction Value, and Notes.
  - **Core Responsibilities:**
    1. **Order Validation & Execution:** Simulates buying and selling. Verifies sufficient cash balance before executing BUY orders, and checks sufficient share quantity before executing SELL orders. Updates cash reserves and position records automatically.
    2. **Cash Management:** Supports commands to deposit cash, withdraw cash, or reset the portfolio back to the initial $100,000 baseline.
    3. **Real-time Portfolio Valuation:** Queries current quotes to compute real-time Net Asset Value (NAV), total portfolio return (unrealized + realized P&L), and cash allocation.
    4. **Dividend & Income Tracking:** Allows logging dividend distributions, updating total returns and yield on cost metrics.
    5. **Portfolio Reporting:** Generates clean, markdown-formatted portfolio status reports, asset allocation summaries, and performance breakdowns on demand.

## 3. User Experience & Interface
- **Primary Interface:** A clean, modern chat-based UI communicating directly with the Manager Agent. The chat UI must support full Markdown rendering for displaying financial reports and tables elegantly.
- **Session Management & Report Export:**
  - Multi-session chat support (or persistent session with clear history).
  - One-click **"Export Report"** / **"Copy Markdown"** button to export dossiers and summaries directly to Obsidian-compatible Markdown format.
- **Persona Management:** 
  - A dedicated settings panel in the UI allowing the user to view, edit, and save the system prompt/persona for each agent.
  - Includes a mandatory **"Reset to Default Persona"** button for every agent to recover from faulty prompts.
  - Core JSON/Markdown formatting contracts remain enforced underneath custom persona text.
- **Trigger Mechanism:** Manual trigger. The user clicks a button or types a prompt (e.g., "Analyze today's business news and recommend top stocks") to kick off the multi-agent workflow.

## 4. Technical Stack & Environment Constraints
- **Target Environment & Portability:**
  - High portability across Linux, macOS, and Windows with minimal system prerequisites.
  - Standard Python (3.10+) runtime using a virtual environment (`venv`) with zero heavy database daemons or mandatory Docker overhead.
  - The FastAPI backend should serve the pre-built static frontend assets directly (or provide a single unified launcher), so end-users only need Python installed to run the application.
- **Version Control:** Git and GitHub. The repository is hosted at `https://github.com/caivictor/F_R_I.git`. All phases must be developed on separate branches and merged via GitHub Pull Requests.
- **Backend:** Python (FastAPI, LangChain/LangGraph, `feedparser`, `beautifulsoup4`, `httpx`, `yfinance`).
- **Frontend:** React / Next.js with Tailwind CSS for a minimal UI focused on chat interaction, loading indicators, Markdown rendering, and settings modals.
- **Database:** Local SQLite (storing: 1. `positions` table with cost basis, shares, dividends; 2. `transactions` table with full trade/cash audit history; 3. `portfolio_summary` with cash balance ($100k initial) and realized gains; 4. `agent_personas` for custom prompt persistence).
- **Network / Tool Timeouts:** 15–20 seconds max per external request (`yfinance`, Google News RSS).

## 5. Phased Execution Roadmap

### Phase 1: Proof of Concept (PoC) & Core Agent Wiring
- Set up the FastAPI backend and minimal React chat frontend.
- Implement the Manager Agent connected to Gemini Pro and establish the chat loop with the user.
- Build dummy/mock versions of the 3 sub-agents to verify the Manager can successfully delegate tasks and return a final aggregated response to the frontend.

### Phase 2: Agent Tooling & Real Data (Research & Analysis)
- Build the Research Agent's Google News Business parser using `feedparser` / `httpx` with top 3–5 company ranking cap.
- Equip the Analysis Agent with financial data tools (`yfinance` with 15s timeout, Previous Close support for off-hours) and integrate Gemini Flash to process the Research Agent's handoff.
- Implement the dynamic retry logic (up to 3 times) and error handling in the Manager Agent.

### Phase 3: Portfolio Tracking & Cash Management (Investment Agent)
- Initialize the local SQLite database for paper trading with $100,000 default cash.
- Equip the Investment Agent with trade validation, cash deposit/withdraw/reset, and CRUD capabilities for the local database.
- Wire the Manager Agent to pass user execution commands (e.g., "Buy 10 shares of NVDA", "Deposit $5,000") and two-step confirmation prompts.

### Phase 4: UX Polish, Session Export, & Persona Management
- Refine Markdown rendering in the chat UI with one-click Markdown copy/export for Obsidian.
- Add clear loading states/indicators in the chat displaying real-time agent handoffs.
- Implement the Persona Management UI with editable prompts and a "Reset to Default" failsafe button.

## 6. Documentation, Installation & User Manual Mandates
To ensure the application is easily installed, operated, and maintained by any user, the AI builder MUST produce and maintain:

1. **`INSTALL.md` (Installation Guide):**
   - Step-by-step installation instructions for Linux, macOS, and Windows.
   - Python virtual environment setup (`python3 -m venv venv`) and dependency installation (`pip install -r requirements.txt`).
   - Configuration instructions for `.env` (Gemini API Key setup).
   - Single-command start scripts (`start.sh` for Linux/macOS and `start.bat` for Windows).

2. **`USER_MANUAL.md` (Operations Manual):**
   - Comprehensive end-user operational guide with screenshots / ASCII diagrams of the UI.
   - Walkthrough of the Manager Agent chat commands, sample prompts for research runs, and analysis deep dives.
   - Guide on executing paper trades, depositing/resetting cash, and understanding financial metrics (ROIC, FCF, D/E, etc.).
   - Instructions on accessing the Persona Management settings panel to customize or reset agent system prompts.
   - Guide on exporting reports to Markdown / Obsidian.

3. **`README.md` & `CHANGELOG.md`:**
   - Standard architectural overview, repository structure, and per-phase progress logs.
   - Comprehensive inline code documentation across all modules, tools, and prompts.
