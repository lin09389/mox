@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

title Mox v0.2.0 - LLM 对抗攻防平台

echo ====================================
echo   Mox v0.2.0 - LLM Attack Defense Platform
echo ====================================
echo.

echo Checking services...
echo.

:: Check Ollama (port 11434)
powershell -Command "if (Test-NetConnection -ComputerName localhost -Port 11434 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }" 2>nul
if %errorlevel% equ 0 (
    echo [1/4] ✓ Ollama is running
) else (
    echo [1/4] ○ Ollama not running
)

:: Check Redis (port 6379)  
powershell -Command "if (Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }" 2>nul
if %errorlevel% equ 0 (
    echo [2/4] ✓ Redis is running
) else (
    echo [2/4] ○ Redis not running, using memory cache
)

echo.
echo [3/4] Starting Backend on port 8000...
start "Mox Backend" cmd /k "python -m uvicorn mox.api:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo [4/4] Starting Frontend on port 3000...
start "Mox Frontend" cmd /k "cd /d frontend && npm run dev"

echo.
echo ====================================
echo   Please wait 15 seconds...
echo ====================================
echo.

timeout /t 15 /nobreak >nul

echo.
echo ====================================
echo   Services should be ready!
echo ====================================
echo.
echo   Backend:    http://localhost:8000
echo   Frontend:   http://localhost:3000
echo   API Docs:   http://localhost:8000/docs
echo   WebSocket:  ws://localhost:8000/ws
echo.

start http://localhost:3000

echo Done! Browser should open.
echo.
pause
