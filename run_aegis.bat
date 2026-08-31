@echo off
title AEGIS — Assisted Executive Guidance and Intelligence System
color 0B

echo ===================================================================
echo   AEGIS — Assisted Executive Guidance and Intelligence System (SIH26204)
echo ===================================================================
echo Starting AEGIS Core Engine and Dashboard on http://127.0.0.1:8000 ...
echo.

:: Start FastAPI Backend Server
start "AEGIS Backend Server" /min python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

:: Wait 2 seconds for server to bind
timeout /t 2 /nobreak >nul

:: Open in default browser
start http://127.0.0.1:8000

echo.
echo AEGIS is running!
echo Access the Dashboard at: http://127.0.0.1:8000
echo.
echo Press any key to stop AEGIS...
pause >nul
taskkill /F /IM uvicorn.exe /T 2>nul
