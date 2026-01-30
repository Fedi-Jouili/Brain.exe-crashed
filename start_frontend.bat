@echo off
REM PriceSense - Start Frontend UI
echo.
echo ====================================================================
echo   Starting PriceSense Frontend
echo ====================================================================
echo.
echo Frontend will be available at: http://localhost:8501
echo Make sure backend is running at: http://localhost:8000
echo.

cd /d "%~dp0frontend"
C:\Users\mezen\AppData\Local\Python\pythoncore-3.14-64\python.exe -m streamlit run app.py
