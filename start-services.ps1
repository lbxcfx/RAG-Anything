# RAG-Anything 服务启动脚本
Write-Host "启动 RAG-Anything 服务..." -ForegroundColor Green

# 启动后端服务
Write-Host "启动后端服务..." -ForegroundColor Yellow
Set-Location "backend"
$env:PYTHONPATH = "."
$pythonPath = "venv\Scripts\python.exe"
Start-Process -FilePath $pythonPath -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" -WindowStyle Minimized

# 等待一段时间让后端启动
Start-Sleep -Seconds 3

# 启动前端服务
Write-Host "启动前端服务..." -ForegroundColor Yellow
Set-Location "../frontend"
Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WindowStyle Minimized

# 回到根目录
Set-Location ".."

Write-Host "服务已启动!" -ForegroundColor Green
Write-Host "前端服务: http://localhost:4173" -ForegroundColor Cyan
Write-Host "后端服务: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API文档: http://localhost:8000/docs" -ForegroundColor Cyan

# 等待一段时间，然后测试服务
Start-Sleep -Seconds 8
Write-Host "`n测试服务连接状态..." -ForegroundColor Yellow

# 测试后端
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -TimeoutSec 5
    Write-Host "✅ 后端服务正常: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "❌ 后端服务异常: $($_.Exception.Message)" -ForegroundColor Red
}

# 测试前端
try {
    $response = Invoke-WebRequest -Uri "http://localhost:4173" -TimeoutSec 5
    Write-Host "✅ 前端服务正常: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "❌ 前端服务异常: $($_.Exception.Message)" -ForegroundColor Red
}
