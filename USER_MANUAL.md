# F.R.I. (Financial Research & Investment) Operations & User Manual

Welcome to **F.R.I.** — an automated financial research and portfolio management assistant powered by a coordinated multi-agent AI architecture.

---

## 1. System Overview & Architecture

```
+-------------------------------------------------------------------------------+
|                            USER CHAT INTERFACE                                |
|          (React / TypeScript / Tailwind CSS / SSE Stream / Markdown)          |
+---------------------------------------+---------------------------------------+
                                        | HTTP / SSE Stream
                                        v
+-------------------------------------------------------------------------------+
|                                MANAGER AGENT                                  |
|        - Natural Language Intent Router & Workflow Chainer                    |
|        - Conversational Entity & Pronoun Resolution Memory                    |
|        - Two-Step Trade Confirmation Interlock                                |
|        - 3x Self-Healing & Unsticking Engine                                  |
+-------------------+-------------------+-------------------+-------------------+
                    |                   |                   |
                    v                   v                   v
      +---------------------+ +---------------------+ +---------------------+
      |   RESEARCH AGENT    | |   ANALYSIS AGENT    | |  INVESTMENT AGENT   |
      | - Google News RSS   | | - yfinance Toolkit  | | - SQLite DB ($100k) |
      | - Top 3-5 Ranking   | | - US Public Filter  | | - 2-Step Trade Exec |
      | - Market Synthesis  | | - Long-Term Dossier | | - Cash NAV Tracking |
      +---------------------+ +---------------------+ +---------------------+
```

### Agent Roles & Responsibilities

1. **Manager Agent**:
   - Master orchestrator and conversation proxy.
   - Interprets free-form intent and delegates queries to specialist sub-agents.
   - Retains context across multi-turn dialogues (e.g. "Analyze Apple" -> "What is its cost basis in my portfolio?" -> "Buy 10 shares of it").
   - Intercepts all trade orders with a strict two-step confirmation prompt before paper execution.
   - Automatically attempts up to 3 self-healing retries with adaptive query rephrasing if sub-agents encounter timeouts.

2. **Research Agent**:
   - Scans and parses live Google News Business RSS feeds.
   - Sanitizes article summaries, publisher metadata, and links.
   - Extracts and ranks the top 3–5 public companies trending in market headlines.

3. **Analysis Agent**:
   - Fundamental equity valuation engine powered by `yfinance`.
   - Strictly enforces eligibility for US-listed public companies (NYSE/NASDAQ), rejecting private companies (e.g. OpenAI, SpaceX, Stripe) and non-US OTC stocks.
   - Calculates core long-term investment metrics: ROIC, ROE, FCF Yield, Debt-to-Equity, Interest Coverage, PEG ratio, and margins.
   - Produces structured "Long-Term Investment Dossiers" formatted in Markdown tables.

4. **Investment Agent**:
   - Paper-trading portfolio manager backed by local SQLite persistence.
   - Bootstraps accounts with a default baseline of **$100,000.00 USD**.
   - Calculates weighted average cost basis, realized gains, unrealized P/L, Net Asset Value (NAV), and dividend yield on cost.
   - Supports cash management (deposit, withdraw, reset) and dividend distribution logging.

---

## 2. Navigating the User Interface

```
+-------------------------------------------------------------------------------+
| [F.R.I. Terminal]  System: ONLINE   |   [Agent Personas]   [+ New Session]   |
+-------------------------------------------------------------------------------+
|                                                                               |
| [Assistant]: Hello! I am your Financial Research & Investment Manager Agent.  |
|                                                                               |
| [User]: Discover today's business news and analyze top tech stocks            |
|                                                                               |
| [Manager Trace]:                                                              |
|   -> Research Agent: Scanning Google News Business RSS...                     |
|   -> Analysis Agent: Evaluating fundamentals for AAPL, NVDA, MSFT...          |
|   -> Manager Agent: Synthesizing executive investment brief...                |
|                                                                               |
| [Assistant]:                                                                  |
|   ### Executive Market Briefing                                               |
|   | Metric | NVDA | AAPL | MSFT |                                             |
|   |--------|------|------|------|                                             |
|   | ROIC   | 45%  | 52%  | 28%  |                                             |
|                                                                               |
|   [Copy Markdown]   [Export to Obsidian (.md)]                                |
|                                                                               |
+-------------------------------------------------------------------------------+
| [ Discover Market News ] [ Analyze AAPL ] [ View Portfolio ] [ Buy 10 NVDA ]  |
|                                                                               |
| [ Enter message or command...                                      ] [ Send ] |
+-------------------------------------------------------------------------------+
```

---

## 3. Sample Commands & Workflows

### 3.1 Market Discovery & News Research
- `"Discover today's market news and highlight trending companies"`
- `"Scan latest business headlines for semiconductor stocks"`
- `"What are the major macroeconomic themes today?"`

### 3.2 Fundamental Equity Deep Dives
- `"Analyze Apple (AAPL) fundamentals and capital efficiency"`
- `"Generate an investment dossier for NVDA including ROIC and free cash flow"`
- `"Evaluate Microsoft (MSFT) valuation multiples and balance sheet resilience"`

*Note on Guardrails:* Requesting private companies (e.g. `"Analyze SpaceX"` or `"Analyze Stripe"`) or foreign listings will be politely rejected by the Analysis Agent with an explanation of asset eligibility.

### 3.3 Portfolio Management & Paper Trading

#### Viewing Portfolio Status:
- `"Show my portfolio status and Net Asset Value"`
- `"What is my current cash balance and asset allocation?"`
- `"Display my transaction audit history"`

#### Executing Paper Trades (Two-Step Confirmation):
1. **Order Initiation:**
   `"Buy 15 shares of NVDA"` or `"Sell 5 shares of AAPL"`
2. **System Confirmation Prompt:**
   The Manager Agent responds with estimated cost, current market price, and available cash:
   > *"You have $100,000.00 cash. Buying 15 shares of NVDA at ~$125.00/share will cost ~$1,875.00. Confirm purchase? [Yes / No]"*
3. **User Action:**
   - Type `"Yes"` / `"Confirm"` / `"Proceed"` to execute the order.
   - Type `"No"` / `"Cancel"` / `"Abort"` to cancel the order.

#### Cash Adjustments & Dividends:
- `"Deposit $10,000 into my investment account"`
- `"Withdraw $5,000 from cash reserves"`
- `"Log a dividend of $1.50 per share for AAPL"`
- `"Reset my portfolio back to the $100,000 baseline"`

### 3.4 Multi-Turn Conversational Memory
The Manager Agent remembers previous conversation entities:
1. `"Analyze Microsoft fundamentals"`
2. `"What is its current price?"` (resolves to MSFT)
3. `"Buy 10 shares of it"` (resolves to MSFT and enters confirmation)

---

## 4. Persona Management

F.R.I. allows users to inspect and customize the system prompts that dictate each agent's behavior:

1. Click the **"Agent Personas"** button in the top navigation bar.
2. Select the tab for the agent you wish to configure:
   - **Manager Agent**: Master orchestration and communication tone.
   - **Research Agent**: News extraction directives and ranking criteria.
   - **Analysis Agent**: Fundamental scoring guidelines and moat assessment.
   - **Investment Agent**: Risk management parameters and portfolio reporting formats.
3. Edit the directive text and click **"Save Persona"**.
4. To revert customizations, click **"Reset Agent Default"** or **"Reset All Defaults"**.

---

## 5. Exporting Reports to Markdown & Obsidian

Every assistant analysis and portfolio briefing includes action buttons:
- **Copy Markdown**: Copies the raw formatted Markdown directly to your clipboard.
- **Export to Obsidian (.md)**: Downloads a standalone `.md` document equipped with YAML frontmatter tags (`tags: [fri, investment-dossier]`, timestamps, session IDs, and multi-agent execution traces) ready to import directly into your Obsidian vault or personal knowledge base.

---

## 6. Understanding Core Financial Metrics

| Metric | What It Measures | Ideal Long-Term Range |
|---|---|---|
| **ROIC (Return on Invested Capital)** | Profit generated for every dollar of capital invested in the business | > 15% |
| **ROE (Return on Equity)** | Net income returned as a percentage of shareholders' equity | > 20% |
| **FCF Yield (Free Cash Flow Yield)** | Free cash flow per share divided by current share price | > 3% - 5% |
| **D/E (Debt-to-Equity Ratio)** | Proportion of debt used to finance company assets relative to equity | < 1.0 (or manageable by cash flow) |
| **Interest Coverage Ratio** | Times EBIT covers annual debt interest payments | > 5x |
| **Trailing & Forward P/E** | Current price relative to past and estimated future earnings | Contextual to growth rate |
| **PEG Ratio** | P/E ratio divided by projected earnings growth rate | < 1.5 - 2.0 |
| **Current / Quick Ratio** | Short-term assets vs. short-term liabilities | > 1.2x |
