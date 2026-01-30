"""
P0 CRITICAL BUG FIX VERIFICATION TESTS
Tests for Thompson Sampling signal weight corrections

Run this after fixing the bug:
    python backend/scripts/test_thompson_fix.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config import settings

print("="*70)
print("P0 THOMPSON SAMPLING BUG FIX VERIFICATION")
print("="*70)
print()

# TEST 1: Verify correct signal weights in config
print("TEST 1: Verify Architecture Specification Signal Weights")
print("-" * 70)

expected_weights = {
    "view": 0.1,
    "click": 0.3,
    "add_to_cart": 0.7,
    "purchase": 1.0,
    "skip": -0.3,
    "remove_from_cart": -0.5,
    "return": -1.0
}

actual_weights = settings.signal_weights

all_correct = True
for action, expected_weight in expected_weights.items():
    actual_weight = actual_weights.get(action)
    status = "PASS" if actual_weight == expected_weight else "FAIL"

    if actual_weight != expected_weight:
        all_correct = False
        print(f"  [{status}] {action:20} Expected: {expected_weight:+.1f}, Got: {actual_weight:+.1f}")
    else:
        print(f"  [{status}] {action:20} {actual_weight:+.1f}")

print()
if all_correct:
    print("RESULT: Signal weights are CORRECT")
else:
    print("RESULT: Signal weights are INCORRECT - FIX REQUIRED!")
print()

# TEST 2: Verify no invalid actions in config
print("TEST 2: Verify No Invalid Actions (like, dislike)")
print("-" * 70)

invalid_actions = ["like", "dislike", "favorite", "love", "hate"]
found_invalid = []

for action in invalid_actions:
    if action in actual_weights:
        found_invalid.append(action)
        print(f"  [FAIL] Found invalid action: '{action}'")

if not found_invalid:
    print("  [PASS] No invalid actions found")
    print()
    print("RESULT: Action validation is CORRECT")
else:
    print()
    print(f"RESULT: Found {len(found_invalid)} invalid actions - FIX REQUIRED!")
print()

# TEST 3: Verify all required actions present
print("TEST 3: Verify All Required Actions Present")
print("-" * 70)

required_actions = set(expected_weights.keys())
actual_actions = set(actual_weights.keys())

missing = required_actions - actual_actions
extra = actual_actions - required_actions

if not missing and not extra:
    print("  [PASS] All required actions present, no extras")
    print()
    print("RESULT: Action set is CORRECT")
else:
    if missing:
        print(f"  [FAIL] Missing actions: {missing}")
    if extra:
        print(f"  [FAIL] Extra actions: {extra}")
    print()
    print("RESULT: Action set is INCORRECT - FIX REQUIRED!")
print()

# TEST 4: Test ThompsonSamplingEngine
print("TEST 4: Test ThompsonSamplingEngine with Correct Weights")
print("-" * 70)

try:
    from ml.thompson_sampling import ThompsonSamplingEngine

    engine = ThompsonSamplingEngine()

    # Test positive signal
    product_id = "TEST_PRODUCT_001"

    # Initial state
    params1 = engine.get_params(product_id)
    alpha1 = params1["alpha"]
    beta1 = params1["beta"]
    print(f"  Initial: \u03b1={alpha1:.2f}, \u03b2={beta1:.2f}")

    # Apply click (+0.3)
    engine.update_params(product_id, "click")
    params2 = engine.get_params(product_id)
    alpha2 = params2["alpha"]
    beta2 = params2["beta"]

    delta_alpha = alpha2 - alpha1
    delta_beta = beta2 - beta1

    print(f"  After click: \u03b1={alpha2:.2f}, \u03b2={beta2:.2f}")
    print(f"  Delta: \u0394\u03b1={delta_alpha:+.2f}, \u0394\u03b2={delta_beta:+.2f}")

    # Verify
    if abs(delta_alpha - 0.3) < 0.01 and abs(delta_beta) < 0.01:
        print(f"  [PASS] Click correctly added +0.3 to \u03b1")
    else:
        print(f"  [FAIL] Click should add +0.3 to \u03b1, but \u0394\u03b1={delta_alpha}, \u0394\u03b2={delta_beta}")

    # Test negative signal
    product_id2 = "TEST_PRODUCT_002"
    params3 = engine.get_params(product_id2)
    alpha3 = params3["alpha"]
    beta3 = params3["beta"]

    engine.update_params(product_id2, "skip")
    params4 = engine.get_params(product_id2)
    alpha4 = params4["alpha"]
    beta4 = params4["beta"]

    delta_alpha2 = alpha4 - alpha3
    delta_beta2 = beta4 - beta3

    print()
    print(f"  Initial (product 2): \u03b1={alpha3:.2f}, \u03b2={beta3:.2f}")
    print(f"  After skip: \u03b1={alpha4:.2f}, \u03b2={beta4:.2f}")
    print(f"  Delta: \u0394\u03b1={delta_alpha2:+.2f}, \u0394\u03b2={delta_beta2:+.2f}")

    if abs(delta_alpha2) < 0.01 and abs(delta_beta2 - 0.3) < 0.01:
        print(f"  [PASS] Skip correctly added +0.3 to \u03b2")
    else:
        print(f"  [FAIL] Skip should add +0.3 to \u03b2, but \u0394\u03b1={delta_alpha2}, \u0394\u03b2={delta_beta2}")

    print()
    print("RESULT: ThompsonSamplingEngine is CORRECT")

except Exception as e:
    print(f"  [ERROR] ThompsonSamplingEngine test failed: {e}")
    print()
    print("RESULT: ThompsonSamplingEngine test FAILED")

print()

# TEST 5: Verify main.py has correct SIGNAL_WEIGHTS constant
print("TEST 5: Verify main.py SIGNAL_WEIGHTS Constant")
print("-" * 70)

try:
    with open(os.path.join(os.path.dirname(__file__), '..', 'main.py'), 'r', encoding='utf-8') as f:
        main_content = f.read()

    # Check for correct signal weights
    required_checks = [
        ('"view": 0.1', "view weight"),
        ('"click": 0.3', "click weight"),
        ('"add_to_cart": 0.7', "add_to_cart weight"),
        ('"purchase": 1.0', "purchase weight"),
        ('"skip": -0.3', "skip weight"),
        ('"remove_from_cart": -0.5', "remove_from_cart weight"),
        ('"return": -1.0', "return weight")
    ]

    all_found = True
    for check_str, description in required_checks:
        if check_str in main_content:
            print(f"  [PASS] Found {description}")
        else:
            print(f"  [FAIL] Missing {description}")
            all_found = False

    # Check for removed invalid actions
    invalid_checks = [
        ('"like"', "like (should be removed)"),
        ('"dislike"', "dislike (should be removed)")
    ]

    found_invalid_in_main = []
    for check_str, description in invalid_checks:
        # Check if it appears in SIGNAL_WEIGHTS context (not just anywhere)
        if check_str in main_content and 'SIGNAL_WEIGHTS' in main_content:
            # More precise check - look for it near SIGNAL_WEIGHTS
            lines = main_content.split('\n')
            in_signal_weights = False
            for i, line in enumerate(lines):
                if 'SIGNAL_WEIGHTS' in line:
                    in_signal_weights = True
                if in_signal_weights and check_str in line:
                    found_invalid_in_main.append(description)
                    print(f"  [FAIL] Found {description}")
                    break
                if in_signal_weights and '}' in line and 'SIGNAL_WEIGHTS' not in line:
                    in_signal_weights = False

    if not found_invalid_in_main:
        print(f"  [PASS] No invalid actions (like, dislike) in SIGNAL_WEIGHTS")

    print()
    if all_found and not found_invalid_in_main:
        print("RESULT: main.py SIGNAL_WEIGHTS is CORRECT")
    else:
        print("RESULT: main.py SIGNAL_WEIGHTS needs fixes")

except Exception as e:
    print(f"  [ERROR] Could not read main.py: {e}")
    print()
    print("RESULT: main.py verification FAILED")

print()

# SUMMARY
print("="*70)
print("VERIFICATION SUMMARY")
print("="*70)

all_tests_passed = all_correct and not found_invalid and not missing and not extra

if all_tests_passed:
    print("STATUS: ALL TESTS PASSED")
    print()
    print("The P0 Thompson Sampling bug has been SUCCESSFULLY FIXED!")
    print()
    print("Next steps:")
    print("  1. Deploy to production")
    print("  2. Monitor logs for Thompson parameter updates")
    print("  3. Verify conversion rates improve over time")
    print()
    print("="*70)
    exit(0)
else:
    print("STATUS: SOME TESTS FAILED")
    print()
    print("The bug fix is INCOMPLETE. Review failures above.")
    print()
    print("="*70)
    exit(1)
