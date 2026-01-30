"""
Quick verification script for Gemini LLM integration
Run from project root: python verify_gemini.py
"""
import sys
import os
from pathlib import Path

# Set up paths
project_root = Path(__file__).parent
backend_dir = project_root / 'backend'
sys.path.insert(0, str(backend_dir))

# Load .env manually to ensure it's found
from dotenv import load_dotenv
env_file = project_root / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print(f"📂 Loaded .env from: {env_file}")
else:
    print(f"⚠️  .env not found at: {env_file}")

print("=" * 70)
print("GEMINI INTEGRATION VERIFICATION")
print("=" * 70)
print()

# Step 1: Verify imports
print("[1/5] Verifying imports...")
try:
    from google import genai
    print("  ✅ google.genai imported successfully")
except ImportError as e:
    print(f"  ❌ Failed to import google.genai: {e}")
    sys.exit(1)

try:
    from core.config import settings
    print("  ✅ core.config imported successfully")
except ImportError as e:
    print(f"  ❌ Failed to import core.config: {e}")
    sys.exit(1)

# Step 2: Verify API key
print("\n[2/5] Verifying API key configuration...")
if settings.google_api_key:
    masked_key = settings.google_api_key[:20] + "..." + settings.google_api_key[-4:]
    print(f"  ✅ API key loaded: {masked_key}")
else:
    print("  ❌ No API key found")
    sys.exit(1)

# Step 3: Verify model name
print("\n[3/5] Verifying model configuration...")
print(f"  Model: {settings.llm_model}")
if "gemini-2.5" in settings.llm_model or "gemini-2.0" in settings.llm_model:
    print("  ✅ Using supported Gemini 2.x model")
elif "gemini-1.5" in settings.llm_model:
    print("  ⚠️  WARNING: gemini-1.5-* may not be available for this API key")
    print("     If you see 404 errors, the model is not supported")
else:
    print(f"  ℹ️  Using model: {settings.llm_model}")

# Step 4: Initialize client
print("\n[4/5] Initializing Gemini client...")
try:
    client = genai.Client(api_key=settings.google_api_key)
    print("  ✅ Client created successfully")
except Exception as e:
    print(f"  ❌ Failed to create client: {e}")
    sys.exit(1)

# Step 5: Test generation
print("\n[5/5] Testing content generation...")
try:
    response = client.models.generate_content(
        model=settings.llm_model,
        contents="Write exactly one word: 'SUCCESS'"
    )
    result_text = response.text.strip()
    print(f"  ✅ Generated: {result_text}")
    print(f"  ✅ Model responded successfully")
except Exception as e:
    print(f"  ❌ Generation failed: {e}")
    if "404" in str(e):
        print("\n  💡 FIX: Update backend/core/config.py:")
        print("     llm_model: str = \"gemini-2.5-flash\"")
    sys.exit(1)

# Success
print("\n" + "=" * 70)
print("✅ ALL CHECKS PASSED - Gemini LLM is ready")
print("=" * 70)
print("\nNext steps:")
print("  1. Run integration tests: python backend/scripts/test_agent4_integration.py")
print("  2. Start backend: python backend/main.py")
print()
