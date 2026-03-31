@echo off
REM Ollama 本地模型攻击测试脚本
REM 使用前请确保 Ollama 服务正在运行

echo ============================================================
echo    Mox - Ollama 本地模型攻击测试
echo ============================================================
echo.

REM 检查 Ollama 是否运行
echo 检查 Ollama 服务...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Ollama 服务未运行
    echo.
    echo 请先启动 Ollama:
    echo   ollama serve
    echo.
    echo 然后下载模型:
    echo   ollama pull llama3
    echo.
    pause
    exit /b 1
)

echo [OK] Ollama 服务已运行
echo.

REM 运行攻击测试
echo 启动攻击测试...
echo.
python examples\ollama_attack.py

pause