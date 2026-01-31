@echo off
echo ====================================
echo   FinCommerce Engine - Backend
echo ====================================
echo.

cd /d "%~dp0"

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Starting backend server...
echo URL: http://localhost:8000
echo API Docs: http://localhost:8000/api/docs
echo.
echo Press Ctrl+C to stop the server
echo.

cd backend
python main.py
