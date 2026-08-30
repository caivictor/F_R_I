@echo off
echo ==================================================================
echo     F.R.I. - Financial Research ^& Investment AI Multi-Agent System
echo ==================================================================

:: Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [Error] Python 3 is required but not installed or not in PATH.
    pause
    exit /b 1
)

:: Setup Virtual Environment if not present
if not exist "venv" (
    if not exist ".venv" (
        echo [Init] Creating Python virtual environment in .\venv...
        python -m venv venv
    )
)

:: Activate Virtual Environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

:: Install requirements
echo [Init] Verifying backend dependencies...
pip install -r requirements.txt --quiet

:: Check .env
if not exist ".env" (
    if exist ".env.example" (
        echo [Init] Initializing .env from .env.example...
        copy .env.example .env
    )
)

set HOST=0.0.0.0
set PORT=8000

echo ==================================================================
echo  Starting F.R.I. unified single-process application...
echo  Server URL: http://localhost:%PORT%
echo  Health check: http://localhost:%PORT%/api/health
echo ==================================================================

python -m uvicorn backend.app.main:app --host %HOST% --port %PORT%
pause
