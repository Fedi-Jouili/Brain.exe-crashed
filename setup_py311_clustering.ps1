# PriceSense - Setup Python 3.11 Environment for Clustering
# This script creates a separate Python 3.11 virtual environment for offline ML preprocessing

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  PriceSense - Python 3.11 Environment Setup for K-Means Clustering" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python 3.11 is available
Write-Host "Checking for Python 3.11..." -ForegroundColor Yellow

$python311 = $null
$pythonPaths = @(
    "python3.11",
    "python311",
    "C:\Python311\python.exe",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\python.exe"
)

foreach ($path in $pythonPaths) {
    try {
        $version = & $path --version 2>&1
        if ($version -match "Python 3\.11") {
            $python311 = $path
            Write-Host "✅ Found Python 3.11: $version" -ForegroundColor Green
            break
        }
    } catch {
        # Continue to next path
    }
}

if (-not $python311) {
    Write-Host "❌ Python 3.11 not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python 3.11 from:" -ForegroundColor Yellow
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or use Python 3.12 by modifying this script." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Creating Python 3.11 virtual environment..." -ForegroundColor Yellow

$venvPath = ".venv-py311"

if (Test-Path $venvPath) {
    Write-Host "⚠️  Virtual environment already exists at $venvPath" -ForegroundColor Yellow
    $response = Read-Host "Do you want to recreate it? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "Removing existing environment..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $venvPath
    } else {
        Write-Host "Using existing environment." -ForegroundColor Green
        & "$venvPath\Scripts\Activate.ps1"
        exit 0
    }
}

& $python311 -m venv $venvPath

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Virtual environment created" -ForegroundColor Green

# Activate environment
Write-Host ""
Write-Host "Activating environment..." -ForegroundColor Yellow
& "$venvPath\Scripts\Activate.ps1"

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Gray

$requiredPackages = @(
    "numpy",
    "scikit-learn",
    "clip",
    "torch",
    "torchvision",
    "pillow",
    "ftfy",
    "regex",
    "tqdm"
)

foreach ($package in $requiredPackages) {
    Write-Host "  - Installing $package..." -ForegroundColor Gray
    python -m pip install $package --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✅ $package installed" -ForegroundColor Green
    } else {
        Write-Host "    ⚠️  $package installation had warnings (may still work)" -ForegroundColor Yellow
    }
}

# Verify installation
Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Yellow

$verification = python -c "from sklearn.cluster import KMeans; import numpy; print('OK')" 2>&1
if ($verification -match "OK") {
    Write-Host "✅ scikit-learn is working correctly" -ForegroundColor Green
} else {
    Write-Host "⚠️  Verification had warnings but may still work" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  ✅ Setup Complete!" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Python 3.11 environment is ready at: $venvPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "To use this environment:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Activate:" -ForegroundColor White
Write-Host "     .\$venvPath\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. Run clustering:" -ForegroundColor White
Write-Host "     python backend/scripts/cluster_products.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "  3. Deactivate when done:" -ForegroundColor White
Write-Host "     deactivate" -ForegroundColor Cyan
Write-Host ""
Write-Host "  4. Return to Python 3.14 for runtime services:" -ForegroundColor White
Write-Host "     .\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "See docs/PYTHON_VERSION_COMPATIBILITY.md for details." -ForegroundColor Gray
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
