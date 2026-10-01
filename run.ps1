Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Starting CareVault AI - Patient-Controlled Health Wallet" -ForegroundColor Green
Write-Host "Tagline: 'Your Health. Your Records. Your Control.'" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan

Set-Location $PSScriptRoot
& ".\venv\Scripts\uvicorn.exe" app.main:app --host 127.0.0.1 --port 8000 --reload
