@echo off
REM CareBridge AI - Startup Script (Windows)

echo =================================================================
echo   CareBridge AI - ICU Communication Platform
echo =================================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "FRONTEND_DIR=%SCRIPT_DIR%frontend"
set "BACKEND_DIR=%SCRIPT_DIR%backend"

REM Load API key from backend/.env if not already set
if "%ANTHROPIC_API_KEY%"=="" (
    for /f "tokens=1,* delims==" %%a in ('type "%BACKEND_DIR%\.env" 2^>nul ^| findstr "ANTHROPIC_API_KEY"') do (
        set "ANTHROPIC_API_KEY=%%b"
    )
)

echo [1/4] Checking prerequisites...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    exit /b 1
)
for /f "tokens=*" %%a in ('node --version') do echo   Node.js version: %%a
echo.

echo [2/4] Installing frontend dependencies...
cd /d "%FRONTEND_DIR%"
call npm install
if errorlevel 1 (
    echo WARNING: npm install had issues, trying to continue...
)
echo.

echo [3/4] Building frontend...
call npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed!
    exit /b 1
)
echo   Build successful!
echo.

echo [4/4] Starting FastAPI server...
echo =================================================================
echo   Server Ready!
echo =================================================================
echo   Access the app at: http://localhost:8000
echo   API docs at: http://localhost:8000/docs
echo   Press Ctrl+C to stop
echo.

cd /d "%BACKEND_DIR%"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
