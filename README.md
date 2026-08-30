# F.R.I. (Financial Research & Investment) AI Multi-Agent System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v3-38B2AC.svg)](https://tailwindcss.com)

F.R.I. is an automated financial research and portfolio management assistant powered by a coordinated multi-agent AI architecture. Users interact entirely through a modern financial terminal chat interface with a **Manager Agent**, which coordinates specialized sub-agents to gather news, conduct quantitative fundamental equity analysis, and manage a paper trading investment portfolio.

---

## Key Features

- **Multi-Agent Orchestration**:
  - **Manager Agent**: Natural language intent routing, multi-turn entity resolution, trade confirmation guardrails, and automated 3x retry self-healing engine.
  - **Research Agent**: Scrapes and synthesizes live Google News Business headlines, extracts publisher metadata, and ranks the top 3–5 trending US public companies.
  - **Analysis Agent**: Quantitative fundamental equity valuation via `yfinance` extracting ROIC, ROE, FCF yield, Debt-to-Equity, Interest Coverage, PEG, EV/EBITDA, and generating structured investment dossiers. Enforces strict NYSE/NASDAQ public equity filtering.
  - **Investment Agent**: SQLite-backed paper portfolio manager with $100,000 baseline cash, real-time NAV valuation, weighted average cost basis tracking, cash adjustments, and dividend logging.
- **Single-Process Lightweight Architecture**: Zero Docker or heavy database daemons required. Runs in a standard Python virtual environment with local SQLite storage and directly serves pre-compiled static React UI assets.
- **Agent Guardrails**: Explicit two-step trade confirmation interlocks, private company rejections (e.g. OpenAI, SpaceX, Stripe), and hard 15-second tool timeouts.
- **Obsidian & Markdown Export**: One-click raw Markdown copy and Obsidian-compatible export with YAML frontmatter tags and multi-agent execution traces.
- **Custom Persona Management**: In-app UI settings panel to inspect, edit, and reset agent system prompts to default fail-safes.

---

## Architecture Overview

```
                          +-------------------------+
                          |   React / Tailwind UI   |
                          | (Financial Terminal)    |
                          +------------+------------+
                                       |
                            HTTP / SSE Stream
                                       v
                          +-------------------------+
                          |      FastAPI Server     |
                          |  Single Unified Process |
                          +------------+------------+
                                       |
                +----------------------+----------------------+
                |                      |                      |
                v                      v                      v
     +--------------------+ +--------------------+ +--------------------+
     |   Manager Agent    | |   Research Agent   | |   Analysis Agent   |
     | Intent & Memory    | | Google News RSS    | | yfinance Valuation |
     +----------+---------+ +--------------------+ +--------------------+
                |
                v
     +--------------------+
     |  Investment Agent  |
     | SQLite Persistence |
     +--------------------+
```

---

## Quick Start

### 1. Single-Command Launch (Linux & macOS)
```bash
chmod +x start.sh
./start.sh
```

### 2. Single-Command Launch (Windows)
```cmd
start.bat
```

### 3. Open Browser
Navigate to `http://localhost:8000`.

For detailed setup instructions, virtual environment management, and manual installation, see [INSTALL.md](./INSTALL.md).
For a comprehensive walkthrough of user commands and financial metrics, see [USER_MANUAL.md](./USER_MANUAL.md).

---

## Repository Structure

```
F_R_I/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── analysis.py      # Analysis Agent (yfinance, fundamental metrics, dossiers)
│   │   │   ├── investment.py    # Investment Agent (trade orders, cash ops, valuation)
│   │   │   ├── llm.py           # Gemini API client & intelligent reasoning fallback
│   │   │   ├── manager.py       # Manager Agent (routing, memory, 2-step trade, retries)
│   │   │   ├── personas.py      # System prompts & persona manager
│   │   │   └── research.py      # Research Agent (Google News RSS parser, top 3-5 rank)
│   │   ├── db/
│   │   │   └── database.py      # SQLite persistence layer (positions, tx, summary, WAL)
│   │   ├── routers/
│   │   │   ├── chat.py          # REST & SSE streaming chat endpoints
│   │   │   ├── personas.py      # Persona inspection & reset endpoints
│   │   │   └── portfolio.py     # Portfolio status, trades, and cash REST endpoints
│   │   ├── config.py            # Pydantic settings & timeouts
│   │   └── main.py              # FastAPI application & static asset mounting
│   └── tests/                   # Backend pytest suite (56 unit & integration tests)
├── frontend/
│   ├── src/
│   │   ├── components/          # ChatInterface, Header, PersonaModal, StepProgress, etc.
│   │   ├── services/            # SSE and REST API client
│   │   └── utils/               # Obsidian markdown export generator
│   └── dist/                    # Pre-built production static web bundle
├── e2e/                         # Playwright end-to-end test suite (22 browser tests)
├── screenshots/                 # Captured UI and testing evidence
├── ADVERSARIAL_REVIEW.md        # Adversarial findings ledger
├── DEFECTS.md                   # Defect tracking ledger
├── INSTALL.md                   # Multi-platform installation guide
├── PRD.md                       # Product requirements document contract
├── USER_MANUAL.md               # End-user operations manual
├── CHANGELOG.md                 # Project version changelog
├── start.sh                     # Single-command Linux/macOS launcher
└── start.bat                    # Single-command Windows launcher
```

---

## Testing

Run the full automated test suites across backend, frontend, and end-to-end layers:

```bash
# Backend pytest suite
pytest -v

# Frontend unit suite
cd frontend && npm test && cd ..

# End-to-End browser suite
cd e2e && npx playwright test && cd ..
```

---

## License

This project is licensed under the MIT License.
