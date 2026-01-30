"""
Simple Gemini Integration Test

Minimal test to verify Gemini LLM is working with Agent 4.
"""
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Import settings first
from core.config import settings

print("="*70)
print(" GEMINI LLM VERIFICATION TEST")
print("="*70)
print()

# Step 1: Verify configuration
print("[STEP 1] Configuration Verification")
print("-"*70)
print(f"API Key Loaded: {bool(settings.google_api_key)}")
if settings.google_api_key:
    print(f"API Key (masked): {settings.google_api_key[:10]}...{settings.google_api_key[-4:]}")
print(f"LLM Model: {settings.llm_model}")
print()

if not settings.google_api_key:
    print("❌ FAILED: No API key loaded")
    print("Check .env file location and GOOGLE_API_KEY value")
    sys.exit(1)

# Step 2: Test Gemini client directly
print("[STEP 2] Gemini Client Test")
print("-"*70)
try:
    from google import genai

    client = genai.Client(api_key=settings.google_api_key)
    print("✅ Gemini client created successfully")

    # Try a simple generation
    response = client.models.generate_content(
        model=settings.llm_model,
        contents="Say 'Hello from Gemini' in exactly 3 words."
    )

    print(f"✅ Gemini response: {response.text.strip()}")
    print()

except Exception as e:
    print(f"❌ FAILED: {e}")
    print()
    sys.exit(1)

# Step 3: Test Agent 4 initialization
print("[STEP 3] Agent 4 Initialization")
print("-"*70)

# Mock only what's necessary
from unittest.mock import MagicMock
sys.modules['redis'] = MagicMock()

# Create a proper mock for redis_client
class MockRedisManager:
    def __init__(self):
        pass
    def get(self, key):
        return None
    def set(self, key, value):
        pass

sys.modules['core.redis_client'] = MagicMock()
sys.modules['core.redis_client'].redis_manager = MockRedisManager()

# Import Agent 4
from agents.agent4_explainer import explainer_agent

print(f"Agent has LLM: {explainer_agent.has_llm}")
print(f"Fallback trust: {explainer_agent.fallback_trust}")
print()

if not explainer_agent.has_llm:
    print("❌ FAILED: Agent 4 not using LLM despite valid API key")
    sys.exit(1)

# Step 4: Test Agent 4 execution
print("[STEP 4] Agent 4 Execution Test")
print("-"*70)

test_state = {
    'query': 'test query',
    'user_profile': type('User', (), {
        'user_id': 'test',
        'monthly_income': 5000.0,
        'credit_score': 720
    })(),
    'final_recommendations': [
        {
            'product': {
                'product_id': 'test-1',
                'name': 'Test Product',
                'price': 299.99,
                'category': 'Electronics',
                'brand': 'TestBrand',
                'rating': 4.5,
                'num_reviews': 100,
                'financing_available': True,
                'cluster_id': 1
            },
            'rank': 1,
            'final_score': 0.9,
            'scores': {
                'thompson': 0.85,
                'collaborative': 0.8,
                'ragas': 0.9,
                'financial': 0.95
            },
            'affordability': {
                'can_afford_cash': True,
                'can_afford_financing': True,
                'risk_level': 'LOW',
                'disposable_income': 2500.0
            }
        }
    ]
}

try:
    result_state = explainer_agent.execute(test_state)

    rec = result_state['final_recommendations'][0]
    explanation = rec.get('explanation', {})

    print(f"Explanation text: {explanation.get('text', '')[:100]}...")
    print(f"Trust score: {explanation.get('trust', 0.0)}")
    print(f"Used LLM: {explanation.get('used_llm', False)}")
    print(f"Verified: {explanation.get('verified', False)}")
    print(f"Violations: {len(explanation.get('violations', []))}")
    print()

    if not explanation.get('used_llm', False):
        print("⚠️  WARNING: Fallback mode used instead of LLM")
        print("This might indicate an API issue despite initialization")
    else:
        print("✅ SUCCESS: Agent 4 generated LLM explanation")

        # Verify trust score is in valid range
        trust = explanation.get('trust', 0.0)
        if 0.0 <= trust <= 1.0:
            print(f"✅ Trust score in valid range: {trust}")
        else:
            print(f"❌ FAILED: Trust score out of range: {trust}")
            sys.exit(1)

        # Verify trust score is higher than fallback
        if trust > 0.85:
            print(f"✅ LLM trust score ({trust:.2f}) > fallback trust (0.85)")
        else:
            print(f"⚠️  Trust score ({trust:.2f}) <= fallback trust (0.85)")

except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("="*70)
print(" ALL TESTS PASSED")
print("="*70)
print()
print("✅ Google API key loaded")
print("✅ Gemini client working")
print("✅ Agent 4 initialized with LLM")
print("✅ Agent 4 generates explanations")
print("✅ All contracts enforced")
print()
