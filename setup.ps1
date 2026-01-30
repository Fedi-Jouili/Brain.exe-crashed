# PriceSense - PowerShell Setup Script
# Run this to set up everything automatically

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "  🚀 FINCOMMERCE ENGINE - AUTOMATED SETUP" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Step 1: Check if .env exists
Write-Host "📝 Step 1: Checking environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "   Creating .env from template..." -ForegroundColor Gray
    Copy-Item ".env.example" ".env"
    Write-Host "   ⚠️  IMPORTANT: Edit .env and add your GOOGLE_API_KEY" -ForegroundColor Red
    Write-Host "   Get it here: https://makersuite.google.com/app/apikey (FREE)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   Press Enter after you've added your API key..." -ForegroundColor Yellow
    Read-Host
} else {
    Write-Host "   ✅ .env file exists" -ForegroundColor Green
}

# Step 2: Start Docker services
Write-Host ""
Write-Host "🐳 Step 2: Starting Docker services..." -ForegroundColor Yellow
try {
    docker-compose up -d qdrant redis
    Start-Sleep -Seconds 5
    Write-Host "   ✅ Qdrant and Redis started" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Docker error: $_" -ForegroundColor Red
    exit 1
}

# Step 3: Check Docker containers
Write-Host ""
Write-Host "🔍 Step 3: Verifying Docker containers..." -ForegroundColor Yellow
$qdrantRunning = docker ps | Select-String "fincommerce-qdrant"
$redisRunning = docker ps | Select-String "fincommerce-redis"

if ($qdrantRunning -and $redisRunning) {
    Write-Host "   ✅ Both containers running" -ForegroundColor Green
} else {
    Write-Host "   ❌ Containers not running properly" -ForegroundColor Red
    docker ps
    exit 1
}

# Step 4: Install Python dependencies
Write-Host ""
Write-Host "📦 Step 4: Installing Python dependencies..." -ForegroundColor Yellow
Write-Host "   (This may take 5-10 minutes on first run)" -ForegroundColor Gray
try {
    Set-Location backend
    pip install -r requirements.txt --quiet
    Write-Host "   ✅ Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "   ❌ pip install error: $_" -ForegroundColor Red
    exit 1
}

# Step 5: Initialize databases
Write-Host ""
Write-Host "🗄️  Step 5: Initializing databases..." -ForegroundColor Yellow
try {
    python scripts/init_db.py
    Write-Host "   ✅ Qdrant collections created" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Database init error: $_" -ForegroundColor Red
    exit 1
}

# Step 6: Seed sample data
Write-Host ""
Write-Host "🌱 Step 6: Loading sample data..." -ForegroundColor Yellow
try {
    python scripts/seed_data.py
    Write-Host "   ✅ Sample data loaded" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Data seeding error: $_" -ForegroundColor Red
    exit 1
}

# Step 7: Run tests
Write-Host ""
Write-Host "🧪 Step 7: Running system tests..." -ForegroundColor Yellow
try {
    python scripts/test_system.py
} catch {
    Write-Host "   ⚠️  Some tests failed (check output above)" -ForegroundColor Yellow
}

# Success message
Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "  ✅ SETUP COMPLETE!" -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎯 Quick Start Commands:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   # Test CLIP embeddings" -ForegroundColor Gray
Write-Host '   python -c "from core.embeddings import clip_embedder; print(len(clip_embedder.encode_query(\"test\")))"' -ForegroundColor White
Write-Host ""
Write-Host "   # Search for products" -ForegroundColor Gray
Write-Host '   python -c "from core.qdrant_client import qdrant_manager; from core.embeddings import clip_embedder; emb = clip_embedder.encode_query(\"laptop\"); print(len(qdrant_manager.search_products(emb, top_k=3)))"' -ForegroundColor White
Write-Host ""
Write-Host "   # Run all tests again" -ForegroundColor Gray
Write-Host "   python scripts/test_system.py" -ForegroundColor White
Write-Host ""
Write-Host "📚 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Read QUICKSTART.md for detailed testing" -ForegroundColor Gray
Write-Host "   2. Review DEVELOPMENT_GUIDE.md to build Agent 2" -ForegroundColor Gray
Write-Host "   3. Check PROJECT_STATUS.md for roadmap" -ForegroundColor Gray
Write-Host ""
Write-Host "🌐 Access Points:" -ForegroundColor Yellow
Write-Host "   - Qdrant UI: http://localhost:6333/dashboard" -ForegroundColor Gray
Write-Host "   - Redis CLI: docker exec -it fincommerce-redis redis-cli" -ForegroundColor Gray
Write-Host ""
Write-Host "Happy coding! 🚀" -ForegroundColor Cyan
Write-Host ""

Set-Location ..
