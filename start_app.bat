@echo off
echo Starting PE Assessment Application...
echo.

echo [1/2] Starting Backend (port 8000)...
start "PE Backend" cmd /k "cd /d "%~dp0backend" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend (port 5173)...
start "PE Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo ============================================
echo   App is starting!
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo   Demo login: demo1@pe-assessment.com / demo123
echo ============================================
echo.
start http://localhost:5173
