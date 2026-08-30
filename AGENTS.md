# F.R.I. (Financial Research & Investment) AI Multi-Agent System — Agent Instructions

Compact guidance for agents working in this repository.

---

## 1. Quick Verification & Execution Commands

### Full Verification Pipeline
Required order when validating changes: `Frontend Build -> Backend Unit Tests -> Frontend Unit Tests -> E2E Tests`

```bash
# 1. Build frontend production assets (required before running backend single-process)
cd frontend && npm run build && cd ..

# 2. Run backend pytest suite (all 58 unit & integration tests)
pytest -v
# Run a single backend test file or test function:
pytest backend/tests/test_phase3.py -v
pytest backend/tests/test_defects.py::test_def_013_contrary_cancellation_precedence_in_trade_confirmation -v

# 3. Run frontend unit & component tests (Vitest)
cd frontend && npm test -- --run && cd ..
# Run a single frontend test file:
cd frontend && npm test -- src/test/ChatMessageItem.test.tsx --run && cd ..

# 4. Run End-to-End browser tests (Playwright)
cd e2e && npx playwright test && cd ..
# Run a single E2E spec:
cd e2e && npx playwright test phase3.spec.ts && cd ..
```

### Running the Application Locally
- **Single unified process (FastAPI serving static frontend at `/` and API at `/api`)**:
  ```bash
  ./start.sh
  # Or directly via uvicorn:
  python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
  ```

---

## 2. Architecture & Directory Ownership

- `backend/app/`: FastAPI application, agent orchestrator, and SQLite persistence.
  - `backend/app/main.py`: App entrypoint. Mounts routers and serves `frontend/dist` at `/`.
  - `backend/app/agents/manager.py`: Manager Agent (master orchestrator, intent routing, conversational memory, 2-step trade confirmation, 3x retry self-healing).
  - `backend/app/agents/research.py`: Research Agent (Google News RSS scraping via `httpx`/`feedparser`, top 3–5 public companies ranking).
  - `backend/app/agents/analysis.py`: Analysis Agent (`yfinance` quantitative metrics, ROIC/FCF/debt ratios, long-term dossiers, US-public filters).
  - `backend/app/agents/investment.py`: Investment Agent (paper portfolio, $100k cash baseline, BUY/SELL execution, cost basis, dividend tracking).
  - `backend/app/db/database.py`: SQLite database (`positions`, `transactions`, `portfolio_summary`, `agent_personas`).
- `frontend/`: React 18 + TypeScript + Vite + Tailwind CSS financial terminal.
  - Build output goes to `frontend/dist/`. FastAPI serves this directory directly in production.
- `e2e/`: Playwright test suite.
- `screenshots/`: Evidence screenshots captured during QA and adversarial passes.
- `.agent/` / `.opencode/agents/`: Sub-agent persona definitions (`orchestrator`, `backend-dev`, `frontend-dev`, `qa`, `adversary`, `security`).

---

## 3. Sub-Agent Roles & Responsibilities

- **`orchestrator`**: Delivery lead. Plans phases, delegates coding specs to developers, reviews evidence/diffs/screenshots, triages adversary and security findings.
- **`backend-dev`**: Backend implementation. FastAPI, agent logic, SQLite persistence, and backend unit tests.
- **`frontend-dev`**: Frontend implementation. React components, Vite build, Tailwind styling, and Vitest unit tests.
- **`qa`**: Quality assurance. E2E browser tests (Playwright), full test runs, screenshot inspection, and owns `DEFECTS.md`.
- **`adversary`**: Adversarial reviewer. Unscripted hostile testing to uncover edge cases and breaks; logs findings to `ADVERSARIAL_REVIEW.md`.
- **`security`**: Security reviewer and auditor. Static analysis, dependency audits, OWASP Top 10 compliance, authentication/input validation, and security posture auditing; logs findings to `SECURITY.md`.

---

## 4. Critical Technical Constraints & Guardrails

- **Zero Heavy Infrastructure**: The application MUST run inside a standard Python 3.10+ virtual environment with local SQLite (`data/fri_portfolio.db`). Never introduce Docker, PostgreSQL, Redis, or external DB daemons.
- **Single Process**: Do NOT run separate frontend dev servers in production. The FastAPI backend must directly serve `frontend/dist` static assets.
- **Trade Confirmation Guardrail**:
  - The Manager Agent MUST intercept all BUY and SELL trade orders and issue an explicit two-step confirmation prompt showing cash balance, unit price, and total estimated cost.
  - In confirmation processing, cancellation/negation tokens (`cancel`, `no`, `don't`, `stop`, `instead`) MUST take strict precedence over casual affirmation tokens (`ok`, `sure`, `proceed`).
- **Equity Eligibility Guardrail**:
  - The Analysis Agent and trade execution pipeline MUST reject private companies (e.g. OpenAI, SpaceX, Stripe, Canva) and OTC/non-US equities.
  - Use regex word boundaries (`\b`) when matching private company names and ticker aliases (e.g. avoid false positives where `DIS` is matched against `Discord` or `AMDOCS` against `AMD`).
- **External Tooling Timeouts & Error Propagation**:
  - Enforce a hard 15–20s timeout on external network requests (`yfinance`, Google News RSS).
  - Sub-agents must raise errors or propagate failure status on timeouts/invalid assets so the Manager Agent's automated 3x retry self-healing engine can dynamically adapt. Never silently swallow errors with synthetic data for invalid assets.
- **SQLite Concurrency**: Always initialize SQLite connections with `PRAGMA journal_mode = WAL;` and `PRAGMA busy_timeout = 5000;`.
- **Code Style**: No emojis in code, comments, print statements, or logging.

---

## 5. Defect, Adversarial & Security Ledgers

- **`DEFECTS.md`**: Defect lifecycle is strictly controlled:
  - Status flow: `OPEN` -> `FIX-READY` -> `CLOSED`.
  - Only `qa` opens and closes defects. Developers report fixes to orchestrator; orchestrator sets `FIX-READY`.
- **`ADVERSARIAL_REVIEW.md`**: Adversary records anomalies with `Disposition: PENDING`. Orchestrator resolves to `ACCEPTED -> DEF-NNN` or `REJECTED - reason`.
- **`SECURITY.md`**: Security vulnerability ledger:
  - Security posture, vulnerability assessments, and dependency/endpoint audit findings are tracked in `SECURITY.md`.
  - Only the `security` agent logs and updates security entries in `SECURITY.md`. Developers remediate vulnerabilities and report fixes for orchestrator triage and security re-verification.
