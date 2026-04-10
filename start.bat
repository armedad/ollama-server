@echo off
REM Ollama Server - Windows launch script

cd /d "%~dp0"

REM Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Python not found. Please install Python 3.
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import fastapi, uvicorn, httpx" 2>nul
if %ERRORLEVEL% neq 0 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
)

REM Create config.json from example if it doesn't exist
if not exist config.json (
    echo Creating config.json from example...
    copy config.example.json config.json
)

REM Start the server
echo Starting Ollama Server...
echo Web UI: http://localhost:11435
echo Press Ctrl+C to stop
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 11435
pause
