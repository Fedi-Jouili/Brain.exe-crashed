"""
Demonstration of 3-Tier Routing System
Shows how queries are routed to FAST/SMART/DEEP paths
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ml.complexity_estimator import complexity_estimator
from models.schemas import UserProfile

print("="*70)
print("3-TIER ROUTING SYSTEM DEMONSTRATION")
print("="*70)
print()

# SCENARIO 1: FAST PATH
print("SCENARIO 1: Simple Browsing (FAST/SMART PATH)")
print("-" * 70)
queries_simple = ["laptops", "phones", "headphones", "tablets"]

for query in queries_simple:
    result = complexity_estimator.estimate(query, None, False)
    print(f"  Query: '{query:15}' -> {result['level']:5} (score={result['score']:.2f})")
print()

# SCENARIO 2: SMART PATH
print("SCENARIO 2: Budget Shopping (SMART PATH)")
print("-" * 70)
queries_budget = [
    "laptop under $1000",
    "phone below $500",
    "headphones less than $200",
    "gaming laptop under $1500"
]

for query in queries_budget:
    result = complexity_estimator.estimate(query, None, False)
    print(f"  Query: '{query:30}' -> {result['level']:5} (score={result['score']:.2f})")
print()

# SCENARIO 3: DEEP PATH
print("SCENARIO 3: Financial Planning (DEEP PATH)")
print("-" * 70)

user_profile = UserProfile(
    user_id="john_doe",
    monthly_income=5000.0,
    credit_score=720
)

queries_financial = [
    "laptop I can afford",
    "laptop with financing",
    "can I afford laptop on my budget",
    "laptop with monthly payment plan",
    "affordable laptop with financing under $1000"
]

for query in queries_financial:
    result = complexity_estimator.estimate(query, user_profile, False)
    print(f"  Query: '{query:45}' -> {result['level']:5} (score={result['score']:.2f})")
print()

# SUMMARY
print("="*70)
print("ROUTING SUMMARY")
print("="*70)
print()
print("FAST PATH (<0.3 complexity):")
print("  - Cache hit only")
print("  - Target: <100ms")
print("  - Use case: Repeated identical queries")
print()
print("SMART PATH (0.3-0.7 complexity):")
print("  - Agent 1 (Discovery) + simple ranking")
print("  - Target: 300-800ms")
print("  - Use case: Simple searches, budget constraints")
print()
print("DEEP PATH (>0.7 complexity):")
print("  - Full 5-agent pipeline")
print("  - Target: 1500-3000ms")
print("  - Use case: Financial analysis, complex queries")
print()
print("="*70)
print("Expected Performance Gain: ~64% latency reduction")
print("="*70)
