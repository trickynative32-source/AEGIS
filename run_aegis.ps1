# ===================================================================
#   AEGIS — Assisted Executive Guidance and Intelligence System (SIH26204)
# ===================================================================

Write-Host "Starting AEGIS Core Engine on http://127.0.0.1:8000 ..." -ForegroundColor Cyan

# Start Backend Server
$proc = Start-Process -FilePath "python" -ArgumentList "-m uvicorn backend.main:app --host 127.0.0.1 --port 8000" -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 2

# Open browser
Start-Process "http://127.0.0.1:8000"

Write-Host "AEGIS is live at http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Press any key to stop AEGIS..." -ForegroundColor Yellow

$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force -ErrorAction SilentlyContinue
