@echo off
echo ============================================
echo   PE Assessment - Full Setup Script
echo ============================================
echo.

echo [1/5] Installing backend dependencies...
cd /d "%~dp0backend"
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (echo FAILED: pip install & pause & exit /b 1)
echo.

echo [2/5] Generating synthetic dataset (5000 records)...
python scripts/generate_dataset.py --records 5000
if %ERRORLEVEL% NEQ 0 (echo FAILED: dataset generation & pause & exit /b 1)
echo.

echo [3/5] Training ML models (BPNN + RF + XGBoost)...
python scripts/train_models.py
if %ERRORLEVEL% NEQ 0 (echo FAILED: model training & pause & exit /b 1)
echo.

echo [4/5] Seeding database with demo users...
python scripts/seed_db.py
if %ERRORLEVEL% NEQ 0 (echo FAILED: database seeding & pause & exit /b 1)
echo.

echo [5/5] Installing frontend dependencies...
cd /d "%~dp0frontend"
call npm install
if %ERRORLEVEL% NEQ 0 (echo FAILED: npm install & pause & exit /b 1)
echo.

echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo   To start the app, run:
echo     start_app.bat
echo.
echo   Or manually:
echo     Terminal 1: cd backend ^& python -m uvicorn app.main:app --port 8000
echo     Terminal 2: cd frontend ^& npm run dev
echo.
echo   Then open: http://localhost:5173
echo   Demo login: demo1@pe-assessment.com / demo123
echo ============================================
pause
