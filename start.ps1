# Mox v0.2.0 启动脚本
# 保存为 start.ps1，然后运行: powershell -ExecutionPolicy Bypass -File start.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Mox v0.2.0 - 大模型对抗攻防平台" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Ollama
Write-Host "[1/4] 检查 Ollama..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✓ Ollama 已运行" -ForegroundColor Green
    }
} catch {
    Write-Host "  ○ Ollama 未运行" -ForegroundColor Gray
}

# 检查 Redis
Write-Host "[2/4] 检查 Redis..." -ForegroundColor Yellow
try {
    $redisCheck = redis-cli ping 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Redis 已运行" -ForegroundColor Green
    } else {
        Write-Host "  ○ Redis 未运行，使用内存缓存" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ○ Redis 未运行，使用内存缓存" -ForegroundColor Gray
}

# 启动后端
Write-Host "[3/4] 启动后端服务..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location $args[0]
    python -m uvicorn mox.api:app --host 0.0.0.0 --port 8000 --reload
} -ArgumentList $PWD

Write-Host "  ✓ 后端已启动 (Job ID: $($backendJob.Id))" -ForegroundColor Green

# 启动前端
Write-Host "[4/4] 启动前端..." -ForegroundColor Yellow
Start-Process "npm" -ArgumentList "run","dev" -WorkingDirectory "$PWD\frontend" -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  启动完成！" -ForegroundColor Green
Write-Host "  前端:    http://localhost:3000" -ForegroundColor White
Write-Host "  后端:    http://localhost:8000" -ForegroundColor White
Write-Host "  API文档: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  WebSocket: ws://localhost:8000/ws" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
