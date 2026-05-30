# Bento ML Studio Run Script for Windows PowerShell
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   BENTO ML STUDIO - LOCAL RUN SERVICE   " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Launching Frontend SPA & Backend API..." -ForegroundColor Yellow

# Start Backend in a separate PowerShell console window
Write-Host "[1/2] Spinning up ElysiaJS Backend on Port 3000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; bun run dev" -WindowStyle Normal

# Start Frontend in another separate PowerShell console window
Write-Host "[2/2] Spinning up Vite React Frontend on Port 5173..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; bun run dev" -WindowStyle Normal

Write-Host "-----------------------------------------" -ForegroundColor Cyan
Write-Host "Demo launchers launched successfully!" -ForegroundColor Green
Write-Host "Verify the status in the opened terminal windows." -ForegroundColor White
Write-Host "LAN Access details can be checked inside the app UI." -ForegroundColor White
Write-Host "=========================================" -ForegroundColor Cyan
