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
  - **Role:** Data Gatherer.
  - **Responsibilities:** Scrapes the web for the latest news and financial information on requested sectors/companies. Passes a comprehensive raw text report to the Analysis Agent.

- **Analysis Agent (Model: Gemini Flash Latest):**
  - **Role:** Financial Analyst.
  - **Responsibilities:** Receives the research report, identifies top public companies, downloads financial data, and evaluates investment potential based on its skill definitions. Outputs a structured report containing the company name, latest news, and a data-backed investment thesis.

- **Investment Agent (Model: Gemini Flash Latest):**
  - **Role:** Portfolio Manager.
  - **Responsibilities:** Tracks the current simulated paper-trading portfolio (stored in a local database), reports performance metrics, and executes simulated buy/sell orders based on user decisions routed through the Manager Agent.

## 3. User Experience & Interface
- **Persona Management:** The UI must include a settings/configuration area where the user can view, edit, and save the system prompt/persona for each individual agent. Changes must be persisted for future sessions without requiring code or CLI modifications.
- **Primary Interface:** A chat-based UI communicating directly with the Manager Agent. The chat UI should support Markdown rendering for displaying financial reports and tables elegantly.
- **Trigger Mechanism:** Manual trigger. The user clicks a button or types a prompt (e.g., "Research AI hardware companies and recommend an investment") to kick off the research and analysis cycle.

## 4. Technical Stack & Environment Constraints
- **Target Environment:** Ubuntu 24.04 (User's laptop/host).
- **Version Control:** Git and GitHub. The project must be initialized as a Git repository. All phases must be developed on separate branches and merged via GitHub Pull Requests.
- **Backend:** Python (FastAPI/LangChain/LangGraph) to orchestrate the AI agents.
- **Frontend:** React / Next.js for a minimal UI focused on the chat interaction and Markdown rendering.
- **Database:** Local SQLite- **Version Control & Collaboration:** Git and GitHub. All work must be logically committed. Features and phases must be developed on branches and merged via Pull Requests.
- **Database:** Local SQLite (for simulated paper trading portfolio, agent state tracking, and persisting editable agent personas - ideal for the MVP).

## 5. Phased Execution Roadmap
To ensure the AI coding agent builds this successfully without context collapse, development must strictly follow these phases:

### Phase 1: Proof of Concept (PoC) & Core Agent Wiring
- Set up the FastAPI backend and minimal React chat frontend.
- Implement the Manager Agent connected to Gemini Pro and establish the chat loop with the user.
- Build dummy/mock versions of the 3 sub-agents to verify the Manager can successfully delegate tasks and return a final aggregated response to the frontend.

### Phase 2: Agent Tooling & Real Data (Research & Analysis)
- Equip the Research Agent with web scraping/search tools (e.g., Tavily, DuckDuckGo, or BeautifulSoup) and integrate Gemini Flash.
- Equip the Analysis Agent with financial data tools (e.g., yfinance API) and integrate Gemini Flash to process the Research Agent's handoff.
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
1. Write comprehensive inline code documentation explaining agent prompts and tool definitions.
2. Update the `README.md` with step-by-step installation instructions, dependency requirements, and environment variable setup (including API keys).
3. Maintain a `CHANGELOG.md` detailing what was built in the phase.