# Installation Guide: F.R.I. (Financial Research & Investment AI Multi-Agent System)

This guide provides step-by-step instructions for installing and running the F.R.I. application on Linux, macOS, and Windows.

---

## 1. Prerequisites

- **Python**: Version 3.10, 3.11, 3.12, 3.13, or 3.14.
- **Git**: For cloning the repository.
- **Node.js (Optional for Developers)**: Node.js 18+ and npm are only required if you modify frontend source code. The application serves pre-built static frontend assets directly via Python.

---

## 2. Quick Start (Single-Command Launchers)

### Linux & macOS
1. Open a terminal and clone the repository:
   ```bash
   git clone https://github.com/caivictor/F_R_I.git
   cd F_R_I
   ```
2. Run the automated startup script:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```
3. Open your browser to:
   ```
   http://localhost:8000
   ```

### Windows
1. Open Command Prompt or PowerShell and clone the repository:
   ```cmd
   git clone https://github.com/caivictor/F_R_I.git
   cd F_R_I
   ```
2. Double-click `start.bat` or run:
   ```cmd
   start.bat
   ```
3. Open your browser to `http://localhost:8000`.

---

## 3. Manual Installation Step-by-Step

If you prefer to configure your environment manually, follow the steps below:

### Step 1: Create and Activate a Python Virtual Environment

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Open `.env` in any text editor and configure:
```env
# Optional: Set your Google Gemini API Key for live AI synthesis.
# If left empty, F.R.I. operates with high-fidelity deterministic reasoning and mock data fallbacks.
GEMINI_API_KEY=your_gemini_api_key_here

# Server Bind Address & Port
HOST=0.0.0.0
PORT=8000

# External Request Timeouts (Seconds)
DEFAULT_TIMEOUT_SECONDS=15
```

### Step 4: Build Frontend Assets (If Building From Source)
If you clone a fresh checkout without `frontend/dist/`:
```bash
cd frontend
npm install
npm run build
cd ..
```

### Step 5: Start the Server
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Access the UI at `http://localhost:8000`.

---

## 4. Running the Test Suites

### Backend Unit & Integration Tests (pytest)
```bash
pytest -v
```

### Frontend Unit & Component Tests (vitest)
```bash
cd frontend
npm test
cd ..
```

### End-to-End Test Suite (Playwright)
```bash
cd e2e
npx playwright test
cd ..
```

---

## 5. Troubleshooting & FAQ

- **Port 8000 in use:** Set `PORT=8080` in `.env` or run `uvicorn backend.app.main:app --port 8080`.
- **Database Location:** Local SQLite database files are automatically initialized under `data/fri_portfolio.db`. To completely reset the database file, remove the `data/` folder and restart the app.
- **Offline / Air-gapped Mode:** F.R.I. is fully operational even without internet access or Gemini API keys, utilizing built-in quantitative calculations, mock financial models, and graceful fallback news datasets.
