#!/usr/bin/env pwsh
# Ollama 本地模型攻击测试脚本
# 使用前请确保 Ollama 服务正在运行

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   Mox - Ollama 本地模型攻击测试" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Ollama 是否运行
Write-Host "检查 Ollama 服务..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[OK] Ollama 服务已运行" -ForegroundColor Green
    
    # 显示可用模型
    $models = ($response.Content | ConvertFrom-Json).models
    if ($models) {
        Write-Host ""
        Write-Host "已安装的模型:" -ForegroundColor Yellow
        foreach ($model in $models) {
            Write-Host "  - $($model.name)" -ForegroundColor White
        }
    }
} catch {
    Write-Host "[错误] Ollama 服务未运行" -ForegroundColor Red
    Write-Host ""
    Write-Host "请先启动 Ollama:" -ForegroundColor Yellow
    Write-Host "  ollama serve" -ForegroundColor White
    Write-Host ""
    Write-Host "然后下载模型:" -ForegroundColor Yellow
    Write-Host "  ollama pull llama3" -ForegroundColor White
    Write-Host ""
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""
Write-Host "启动攻击测试..." -ForegroundColor Yellow
Write-Host ""

# 运行攻击测试
python examples\ollama_attack.py

Read-Host "按回车键退出"