# ===================================================================
# AURA — Adaptive Universal Routine Assistant (SIH26204)
# ===================================================================

Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "  AURA — Adaptive Universal Routine Assistant (SIH26204)" -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "Starting AURA Core Engine on http://127.0.0.1:8000 ..." -ForegroundColor Yellow

$proc = Start-Process python -ArgumentList "-m uvicorn backend.main:app --host 127.0.0.1 --port 8000" -PassThru -WindowStyle Minimized

Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:8000"

Write-Host "`nAURA is active and running!" -ForegroundColor Green
Write-Host "Dashboard: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C or close this window to stop AURA."
