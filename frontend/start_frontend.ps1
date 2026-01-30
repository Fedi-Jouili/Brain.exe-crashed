# FinCommerce Engine - Frontend Startup Script
# Run this script to start the Streamlit frontend

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   FinCommerce Engine - Frontend    " -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if backend is running
Write-Host "1. Checking backend status..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -Method GET -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ Backend is running!" -ForegroundColor Green
    }
}
catch {
    Write-Host "   ❌ Backend is NOT running!" -ForegroundColor Red
    Write-Host "   Please start the backend first:" -ForegroundColor Yellow
    Write-Host "   cd backend" -ForegroundColor White
    Write-Host "   python main.py" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit
    }
}

Write-Host ""
Write-Host "2. Checking Python packages..." -ForegroundColor Yellow

# Check if virtual environment exists
$venvPath = "..\..\.venv"
if (Test-Path $venvPath) {
    Write-Host "   ✅ Virtual environment found" -ForegroundColor Green
}
else {
    Write-Host "   ⚠️  No virtual environment detected" -ForegroundColor Yellow
}

# Check if streamlit is installed
try {
    $streamlitVersion = (python -m streamlit --version 2>&1)
    Write-Host "   ✅ Streamlit: $streamlitVersion" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ Streamlit not installed!" -ForegroundColor Red
    Write-Host "   Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host ""
Write-Host "3. Starting Streamlit frontend..." -ForegroundColor Yellow
Write-Host "   URL: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""

# Start Streamlit
streamlit run app.py
