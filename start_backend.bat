@echo off
REM PriceSense - Start Backend API Server
echo.
echo ====================================================================
echo   Starting PriceSense Backend API
echo ====================================================================
echo.
echo API will be available at: http://localhost:8000
echo API Docs at: http://localhost:8000/api/docs
echo.

cd /d "%~dp0backend"
C:\Users\mezen\AppData\Local\Python\pythoncore-3.14-64\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
