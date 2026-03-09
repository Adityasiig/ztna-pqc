@echo off
title ZTNA-PQC Server
echo ================================================
echo   ZTNA-PQC  ^|  Post-Quantum Secure Gateway
echo ================================================
echo.

cd /d "%~dp0backend"

echo Starting FastAPI server on http://localhost:8000
echo Press Ctrl+C to stop.
echo.

C:\Users\admin\AppData\Local\Programs\Python\Python314\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000

pause
