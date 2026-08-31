@echo off
title AURA — Adaptive Universal Routine Assistant
color 0B

echo ===================================================================
echo   AURA — Adaptive Universal Routine Assistant (SIH26204)
echo ===================================================================
echo Starting AURA Core Engine and Dashboard on http://127.0.0.1:8000 ...
echo.

:: Start FastAPI Backend Server
start "AURA Backend Server" /min python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

:: Wait 2 seconds for server to bind
timeout /t 2 /nobreak >nul

:: Open in default browser
start http://127.0.0.1:8000

echo.
echo AURA is running!
echo Access the Dashboard at: http://127.0.0.1:8000
echo.
echo Press any key to stop AURA...
pause >nul
taskkill /F /IM uvicorn.exe /T 2>nul
