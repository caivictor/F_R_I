---
tags: [prd, ai-build, finance]
status: Ready
---
# PRD: F.R.I. (Financial Research & Investment) AI Multi-Agent System

## 1. Overview
A standalone web application powered by a multi-agent AI system. The application serves as an automated financial research and portfolio management assistant. The user interacts entirely via a chat interface with a Manager Agent, which delegates tasks to specialized sub-agents to gather data, analyze investments, and track portfolio performance.

## 2. Core Architecture & Agent Definitions

- **Manager Agent (Model: Gemini Pro Latest):**
  - **Role:** Orchestrator and primary user interface.
  - **Responsibilities:** Receives manual triggers/prompts from the user via chat, coordinates sub-agents, tracks task progression, and ensures system stability.
  - **Error Handling:** If a sub-agent gets stuck, it dynamically retries with adjusted prompts and approaches up to 3 times before alerting the user in the chat UI for manual intervention.

- **Research Agent (Model: Gemini Flash Latest):**
  - **Role:** Financial Data & News Gatherer.
  - **Data Source (MVP):** Google News Business Section.
  - **Access Mechanism:** Free / No-API-Key approach using Google News RSS feeds (e.g., `https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en`) and HTML scraping with `feedparser`, `httpx`, and `beautifulsoup4`.
  - **Responsibilities:**
    1. Fetches and parses the latest top business and market headlines on demand without requiring paid API keys.
    2. Extracts essential metadata: title, source publisher, publication timestamp, summary snippet, and article URL.
    3. Synthesizes and filters the raw news feed into a structured markdown report highlighting major market themes and trending public companies.
    4. Passes the consolidated research briefing downstream to the Analysis Agent.

- **Analysis Agent (Model: Gemini Flash Latest):**
  - **Role:** Quantitative & Fundamental Equity Analyst.
  - **Public Company Filter:** Enforces a strict filter to verify that entities identified in the research briefing are publicly traded equities with valid exchange ticker symbols (e.g., NASDAQ, NYSE). Private companies (e.g., OpenAI, SpaceX, Stripe) are flagged and excluded from the fundamental investment scorecard.
  - **Data Ingestion Tooling:** Uses `yfinance` to retrieve historical market data, fundamental financial statements (Income Statement, Balance Sheet, Cash Flow), and valuation multiples without requiring paid Bloomberg/FactSet APIs.
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
  - **Role:** Portfolio Manager.
  - **Responsibilities:** Tracks the current simulated paper-trading portfolio (stored in a local database), reports performance metrics, and executes simulated buy/sell orders based on user decisions routed through the Manager Agent.

## 3. User Experience & Interface
- **Primary Interface:** A clean, modern chat-based UI communicating directly with the Manager Agent. The chat UI must support full Markdown rendering for displaying financial reports and tables elegantly.
- **Persona Management:** A dedicated settings/configuration modal or panel in the UI allowing the user to view, edit, and save the system prompt/persona for each agent. Changes are stored in SQLite and persist across app reboots without touching CLI/code.
- **Trigger Mechanism:** Manual trigger. The user clicks a button or types a prompt (e.g., "Analyze today's business news and recommend top stocks") to kick off the multi-agent workflow.

## 4. Technical Stack & Environment Constraints
- **Target Environment:** Ubuntu 24.04 (User's laptop/host).
- **Version Control:** Git and GitHub. The repository is hosted at `https://github.com/caivictor/F_R_I.git`. All phases must be developed on separate branches and merged via GitHub Pull Requests.
- **Backend:** Python (FastAPI, LangChain/LangGraph, `feedparser`, `beautifulsoup4`, `httpx`, `yfinance`).
- **Frontend:** React / Next.js with Tailwind CSS for a minimal UI focused on the chat interaction, loading indicators, and Markdown rendering.
- **Database:** Local SQLite (for simulated paper-trading portfolio, agent execution history, and persisting editable agent personas).

## 5. Phased Execution Roadmap

### Phase 1: Proof of Concept (PoC) & Core Agent Wiring
- Set up the FastAPI backend and minimal React chat frontend.
- Implement the Manager Agent connected to Gemini Pro and establish the chat loop with the user.
- Build dummy/mock versions of the 3 sub-agents to verify the Manager can successfully delegate tasks and return a final aggregated response to the frontend.

### Phase 2: Agent Tooling & Real Data (Research & Analysis)
- Build the Research Agent's Google News Business parser using `feedparser` / `httpx` (no external API key required).
- Equip the Analysis Agent with financial data tools (e.g., `yfinance` API) and integrate Gemini Flash to process the Research Agent's handoff.
- Implement the dynamic retry logic (up to 3 times) in the Manager Agent for handling tool execution failures in these sub-agents.

### Phase 3: Portfolio Tracking (Investment Agent)
- Initialize the local SQLite database for paper trading.
- Equip the Investment Agent with CRUD capabilities for the local database.
- Wire the Manager Agent to pass user execution commands (e.g., "Buy 10 shares of NVDA") to the Investment Agent and report back on portfolio performance.

### Phase 4: UX Polish, Edge Cases & Persona Management
- Refine Markdown rendering in the chat UI.
- Add clear loading states/indicators in the chat so the user knows exactly which sub-agent is currently working and what step the system is on.
- Implement the Persona Management UI, allowing users to edit and save each agent's persona directly to the SQLite database.

## 6. Documentation & Handover Mandates
For *every single phase* completed above, the AI builder MUST:
1. Write comprehensive inline code documentation explaining agent prompts, RSS parser logic, and tool definitions.
2. Update the `README.md` with step-by-step installation instructions, dependency requirements, and environment variable setup (including API keys).
3. Maintain a `CHANGELOG.md` detailing what was built in the phase.
