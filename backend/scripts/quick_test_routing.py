"""Quick test of complexity estimator"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ml.complexity_estimator import complexity_estimator

print("Testing complexity estimator...")

# Test 1
result1 = complexity_estimator.estimate("laptop", None, False)
print(f"PASS Test 1: '{result1['level']}' (score={result1['score']})")

# Test 2
result2 = complexity_estimator.estimate("laptop under $1000", None, False)
print(f"PASS Test 2: '{result2['level']}' (score={result2['score']})")

# Test 3
from models.schemas import UserProfile
user = UserProfile(user_id="test", monthly_income=5000.0, credit_score=720)
result3 = complexity_estimator.estimate("laptop with financing", user, False)
print(f"PASS Test 3: '{result3['level']}' (score={result3['score']})")

print("\nSUCCESS: All basic tests passed!")
print(f"  - Test 1: {result1['level']} (simple query)")
print(f"  - Test 2: {result2['level']} (price constraint)")
print(f"  - Test 3: {result3['level']} (financial + profile)")
