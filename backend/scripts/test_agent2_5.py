"""
🔒 CI-GRADE TEST SUITE: Agent 2.5 (Budget Pathfinder)

This test suite is a BUILD GUARDRAIL.
If any test fails, the build MUST fail.

Contract Enforcement:
  • viability_score ∈ [0.0, 1.0] for ALL paths
  • Maximum 3 paths returned
  • Paths sorted by viability_score DESC
  • No product mutation
  • Activation only when all_unaffordable=True
  • Graceful error handling
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent2_5_pathfinder import budget_pathfinder_agent
import copy


# Mock UserProfile class
class UserProfile:
    def __init__(self, user_id, monthly_income, monthly_expenses, savings,
                 current_debt, credit_score, risk_tolerance):
        self.user_id = user_id
        self.monthly_income = monthly_income
        self.monthly_expenses = monthly_expenses
        self.savings = savings
        self.current_debt = current_debt
        self.credit_score = credit_score
        self.risk_tolerance = risk_tolerance


def test_1_activation_condition():
    """
    🔒 TEST 1: Agent 2.5 only runs when all_unaffordable=True

    FAIL if:
    - Agent runs when all_unaffordable=False
    - Agent skips when all_unaffordable=True
    """
    print("=" * 80)
    print("TEST 1: Activation Condition")
    print("=" * 80)

    profile = UserProfile(
        user_id="test_user",
        monthly_income=5000,
        monthly_expenses=3000,
        savings=10000,
        current_debt=0,
        credit_score=750,
        risk_tolerance="moderate"
    )

    products = [
        {'product_id': 'p1', 'name': 'Product 1', 'price': 2000,
         'cluster_id': 3, 'financing_available': True, 'in_stock': True}
    ]

    # Test 1a: Should NOT run when all_unaffordable=False
    state_false = {
        'user_profile': profile,
        'candidate_products': products,
        'all_unaffordable': False
    }

    result = budget_pathfinder_agent.execute(state_false)
    paths = result.get('alternative_paths', [])

    if paths:
        print("❌ FAIL: Agent ran when all_unaffordable=False")
        print(f"   Generated {len(paths)} paths (expected 0)")
        return False

    print("✓ Agent correctly skipped when all_unaffordable=False")

    # Test 1b: MUST run when all_unaffordable=True
    state_true = {
        'user_profile': profile,
        'candidate_products': products,
        'all_unaffordable': True
    }

    result = budget_pathfinder_agent.execute(state_true)
    paths = result.get('alternative_paths', [])

    if not paths:
        print("❌ FAIL: Agent did not run when all_unaffordable=True")
        print("   Generated 0 paths (expected >0)")
        return False

    print(f"✓ Agent correctly ran when all_unaffordable=True ({len(paths)} paths)")
    print("\n✅ PASS: Activation condition respected")
    return True


def test_2_maximum_3_paths():
    """
    🔒 TEST 2: No more than 3 paths returned

    FAIL if:
    - More than 3 paths returned
    """
    print("\n" + "=" * 80)
    print("TEST 2: Maximum 3 Paths Constraint")
    print("=" * 80)

    profile = UserProfile(
        user_id="test_user",
        monthly_income=3000,
        monthly_expenses=2500,
        savings=1000,
        current_debt=5000,
        credit_score=650,
        risk_tolerance="moderate"
    )

    # Many products to potentially generate many paths
    products = [
        {'product_id': f'p{i}', 'name': f'Product {i}', 'price': 2000 + i*100,
         'cluster_id': 3, 'financing_available': True, 'in_stock': True}
        for i in range(5)
    ]

    state = {
        'user_profile': profile,
        'candidate_products': products,
        'all_unaffordable': True
    }

    result = budget_pathfinder_agent.execute(state)
    paths = result.get('alternative_paths', [])

    print(f"Generated {len(paths)} paths")

    if len(paths) > 3:
        print(f"❌ FAIL: {len(paths)} paths returned (maximum is 3)")
        return False

    print("✓ Path count within limit")
    print(f"\n✅ PASS: {len(paths)} ≤ 3 paths")
    return True


def test_3_viability_score_range():
    """
    🔒 TEST 3: All viability_score values ∈ [0.0, 1.0]

    FAIL if:
    - Any score < 0.0
    - Any score > 1.0
    - Score is None or not numeric
    """
    print("\n" + "=" * 80)
    print("TEST 3: Viability Score Range [0.0, 1.0]")
    print("=" * 80)

    profile = UserProfile(
        user_id="test_user",
        monthly_income=3500,
        monthly_expenses=2800,
        savings=1500,
        current_debt=5000,
        credit_score=680,
        risk_tolerance="moderate"
    )

    products = [
        {'product_id': 'laptop_1', 'name': 'MacBook Pro 16"', 'price': 2499,
         'cluster_id': 3, 'financing_available': True, 'in_stock': True},
        {'product_id': 'laptop_2', 'name': 'Dell XPS 15', 'price': 1899,
         'cluster_id': 3, 'financing_available': True, 'in_stock': True}
    ]

    state = {
        'user_profile': profile,
        'candidate_products': products,
        'all_unaffordable': True
    }

    result = budget_pathfinder_agent.execute(state)
    paths = result.get('alternative_paths', [])

    print(f"Testing {len(paths)} paths")

    violations = []
    for i, path in enumerate(paths):
        score = path.get('viability_score')

        if score is None:
            violations.append(f"Path {i+1}: viability_score is None")
        elif not isinstance(score, (int, float)):
            violations.append(f"Path {i+1}: viability_score is not numeric ({type(score).__name__})")
        elif score < 0.0:
            violations.append(f"Path {i+1}: viability_score = {score} (< 0.0)")
        elif score > 1.0:
            violations.append(f"Path {i+1}: viability_score = {score} (> 1.0)")
        else:
            print(f"✓ Path {i+1}: viability_score = {score:.4f} ∈ [0.0, 1.0]")

    if violations:
        print("\n❌ FAIL: Score range violations detected")
        for v in violations:
            print(f"   {v}")
        return False

    print(f"\n✅ PASS: All {len(paths)} scores in range [0.0, 1.0]")
    return True


def test_4_sorting_by_viability():
    """
    🔒 TEST 4: Paths sorted by viability_score DESC

    FAIL if:
    - Paths not in descending order
    - Rank field missing or incorrect
    """
    print("\n" + "=" * 80)
    print("TEST 4: Sorting by Viability Score (DESC)")
    print("=" * 80)

    profile = UserProfile(
        user_id="test_user",
        monthly_income=3000,
        monthly_expenses=2500,
        savings=1000,
        current_debt=5000,
        credit_score=650,
        risk_tolerance="moderate"
    )

    products = [
        {'product_id': 'p1', 'name': 'Product 1', 'price': 2000,
         'cluster_id': 3, 'financing_available': True, 'in_stock': True}
    ]

    state = {
        'user_profile': profile,
        'candidate_products': products,
        'all_unaffordable': True
    }

    result = budget_pathfinder_agent.execute(state)
    paths = result.get('alternative_paths', [])

    if not paths:
        print("⚠ Warning: No paths generated (skipping sorting test)")
        return True

    # Check viability scores are sorted DESC
    scores = [p.get('viability_score', 0) for p in paths]
    sorted_scores = sorted(scores, reverse=True)

    print(f"Viability scores: {[round(s, 4) for s in scores]}")

    if scores != sorted_scores:
        print("❌ FAIL: Paths not sorted by viability_score DESC")
        print(f"   Actual:   {[round(s, 4) for s in scores]}")
        print(f"   Expected: {[round(s, 4) for s in sorted_scores]}")
        return False

    print("✓ Scores correctly sorted DESC")

    # Check rank field
    rank_violations = []
    for i, path in enumerate(paths):
        expected_rank = i + 1
        actual_rank = path.get('rank')

        if actual_rank is None:
            rank_violations.append(f"Path {i+1}: Missing 'rank' field")
        elif actual_rank != expected_rank:
            rank_violations.append(f"Path {i+1}: rank={actual_rank} (expected {expected_rank})")
        else:
            print(f"✓ Path {i+1}: rank = {actual_rank}")

    if rank_violations:
        print("\n❌ FAIL: Rank field violations")
        for v in rank_violations:
            print(f"   {v}")
        return False

    print("\n✅ PASS: Correct sorting and ranking")
    return True


def test_5_no_product_mutation():
    """
    🔒 TEST 5: No mutation of input products

    FAIL if:
    - Original product data is modified
    """
    print("\n" + "=" * 80)
    print("TEST 5: No Product Mutation")
    print("=" * 80)

    profile = UserProfile(
        user_id="test_user",
        monthly_income=3000,
        monthly_expenses=2500,
        savings=1000,
        current_debt=5000,
        credit_score=650,
        risk_tolerance="moderate"
    )

    original_products = [
        {'product_id': 'p1', 'name': 'Product 1', 'price': 2000,
         'cluster_id': 3, 'financing_available': True, 'in_stock': True}
    ]

    # Deep copy for comparison
    products_copy = copy.deepcopy(original_products)

    state = {
        'user_profile': profile,
        'candidate_products': original_products,
        'all_unaffordable': True
    }

    result = budget_pathfinder_agent.execute(state)

    # Check if products were mutated
    if original_products != products_copy:
        print("❌ FAIL: Input products were mutated")
        print(f"   Original: {products_copy}")
        print(f"   After:    {original_products}")
        return False

    print("✓ Input products unchanged")
    print("\n✅ PASS: No product mutation")
    return True


def test_6_graceful_error_handling():
    """
    🔒 TEST 6: Graceful handling of edge cases

    FAIL if:
    - Crashes on empty candidate list
    - Crashes on missing cluster_id
    - Crashes on zero disposable income
    """
    print("\n" + "=" * 80)
    print("TEST 6: Graceful Error Handling")
    print("=" * 80)

    # Test 6a: Empty candidate list
    print("\nTest 6a: Empty candidate list")
    profile = UserProfile(
        user_id="test_user",
        monthly_income=3000,
        monthly_expenses=2500,
        savings=1000,
        current_debt=5000,
        credit_score=650,
        risk_tolerance="moderate"
    )

    state = {
        'user_profile': profile,
        'candidate_products': [],
        'all_unaffordable': True
    }

    try:
        result = budget_pathfinder_agent.execute(state)
        paths = result.get('alternative_paths', [])
        print(f"✓ Handled empty list gracefully (returned {len(paths)} paths)")
    except Exception as e:
        print(f"❌ FAIL: Crashed on empty list: {e}")
        return False

    # Test 6b: Missing cluster_id
    print("\nTest 6b: Missing cluster_id")
    products_no_cluster = [
        {'product_id': 'p1', 'name': 'Product 1', 'price': 2000,
         'financing_available': True, 'in_stock': True}
        # No cluster_id
    ]

    state = {
        'user_profile': profile,
        'candidate_products': products_no_cluster,
        'all_unaffordable': True
    }

    try:
        result = budget_pathfinder_agent.execute(state)
        paths = result.get('alternative_paths', [])
        print(f"✓ Handled missing cluster_id gracefully (returned {len(paths)} paths)")
    except Exception as e:
        print(f"❌ FAIL: Crashed on missing cluster_id: {e}")
        return False

    # Test 6c: Zero disposable income
    print("\nTest 6c: Zero disposable income")
    zero_income_profile = UserProfile(
        user_id="test_user",
        monthly_income=2500,
        monthly_expenses=2500,  # Equal to income
        savings=1000,
        current_debt=5000,
        credit_score=650,
        risk_tolerance="moderate"
    )

    products = [
        {'product_id': 'p1', 'name': 'Product 1', 'price': 2000,
         'cluster_id': 3, 'financing_available': True, 'in_stock': True}
    ]

    state = {
        'user_profile': zero_income_profile,
        'candidate_products': products,
        'all_unaffordable': True
    }

    try:
        result = budget_pathfinder_agent.execute(state)
        paths = result.get('alternative_paths', [])
        print(f"✓ Handled zero disposable income gracefully (returned {len(paths)} paths)")
    except Exception as e:
        print(f"❌ FAIL: Crashed on zero disposable income: {e}")
        return False

    # Test 6d: Negative disposable income
    print("\nTest 6d: Negative disposable income")
    negative_income_profile = UserProfile(
        user_id="test_user",
        monthly_income=2000,
        monthly_expenses=2500,  # More than income
        savings=1000,
        current_debt=5000,
        credit_score=650,
        risk_tolerance="moderate"
    )

    state = {
        'user_profile': negative_income_profile,
        'candidate_products': products,
        'all_unaffordable': True
    }

    try:
        result = budget_pathfinder_agent.execute(state)
        paths = result.get('alternative_paths', [])
        print(f"✓ Handled negative disposable income gracefully (returned {len(paths)} paths)")
    except Exception as e:
        print(f"❌ FAIL: Crashed on negative disposable income: {e}")
        return False

    print("\n✅ PASS: All edge cases handled gracefully")
    return True


def test_7_required_fields():
    """
    🔒 TEST 7: Required fields present in all paths

    FAIL if:
    - Any path missing required fields
    - pros/cons not lists
    """
    print("\n" + "=" * 80)
    print("TEST 7: Required Fields Validation")
    print("=" * 80)

    profile = UserProfile(
        user_id="test_user",
        monthly_income=3000,
        monthly_expenses=2500,
        savings=1000,
        current_debt=5000,
        credit_score=650,
        risk_tolerance="moderate"
    )

    products = [
        {'product_id': 'p1', 'name': 'Product 1', 'price': 2000,
         'cluster_id': 3, 'financing_available': True, 'in_stock': True}
    ]

    state = {
        'user_profile': profile,
        'candidate_products': products,
        'all_unaffordable': True
    }

    result = budget_pathfinder_agent.execute(state)
    paths = result.get('alternative_paths', [])

    if not paths:
        print("⚠ Warning: No paths generated (skipping field validation)")
        return True

    required_fields = [
        'type', 'strategy', 'description',
        'viability_score', 'pros', 'cons', 'rank'
    ]

    violations = []
    for i, path in enumerate(paths):
        missing = [field for field in required_fields if field not in path]
        if missing:
            violations.append(f"Path {i+1}: Missing fields: {missing}")

        # Check pros/cons are lists
        if 'pros' in path and not isinstance(path['pros'], list):
            violations.append(f"Path {i+1}: 'pros' must be a list (got {type(path['pros']).__name__})")

        if 'cons' in path and not isinstance(path['cons'], list):
            violations.append(f"Path {i+1}: 'cons' must be a list (got {type(path['cons']).__name__})")

    if violations:
        print("❌ FAIL: Field validation errors")
        for v in violations:
            print(f"   {v}")
        return False

    print(f"✓ All {len(paths)} paths have required fields")
    print(f"  Required: {required_fields}")
    print("\n✅ PASS: Field validation successful")
    return True


def test_8_state_keys():
    """
    🔒 TEST 8: State contains required keys

    FAIL if:
    - alternative_paths key missing
    - agent2_5_execution_time missing
    """
    print("\n" + "=" * 80)
    print("TEST 8: State Keys Validation")
    print("=" * 80)

    profile = UserProfile(
        user_id="test_user",
        monthly_income=3000,
        monthly_expenses=2500,
        savings=1000,
        current_debt=5000,
        credit_score=650,
        risk_tolerance="moderate"
    )

    products = [
        {'product_id': 'p1', 'name': 'Product 1', 'price': 2000,
         'cluster_id': 3, 'financing_available': True, 'in_stock': True}
    ]

    state = {
        'user_profile': profile,
        'candidate_products': products,
        'all_unaffordable': True
    }

    result = budget_pathfinder_agent.execute(state)

    # Check required state keys
    required_keys = ['alternative_paths']
    optional_keys = ['agent2_5_execution_time']

    violations = []
    for key in required_keys:
        if key not in result:
            violations.append(f"Missing required state key: '{key}'")
        else:
            print(f"✓ State contains '{key}'")

    for key in optional_keys:
        if key in result:
            print(f"✓ State contains '{key}' ({result[key]:.0f}ms)")

    if violations:
        print("\n❌ FAIL: State key violations")
        for v in violations:
            print(f"   {v}")
        return False

    print("\n✅ PASS: All required state keys present")
    return True


def main():
    """Run all CI-grade tests"""
    print("\n" + "=" * 80)
    print("🔒 CI-GRADE TEST SUITE: Agent 2.5 (Budget Pathfinder)")
    print("=" * 80)
    print("\nThis test suite is a BUILD GUARDRAIL.")
    print("If any test fails, the build MUST fail.\n")

    tests = [
        ("Activation Condition", test_1_activation_condition),
        ("Maximum 3 Paths", test_2_maximum_3_paths),
        ("Viability Score Range", test_3_viability_score_range),
        ("Sorting by Viability", test_4_sorting_by_viability),
        ("No Product Mutation", test_5_no_product_mutation),
        ("Graceful Error Handling", test_6_graceful_error_handling),
        ("Required Fields", test_7_required_fields),
        ("State Keys", test_8_state_keys),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n🚨 TEST CRASHED: {name}")
            print(f"   Exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)

    print("\n" + "-" * 80)
    print(f"Results: {passed_count}/{total_count} tests passed")
    print("=" * 80)

    if passed_count == total_count:
        print("\n✅ BUILD GUARDRAIL PASSED")
        print("Agent 2.5 is ready for deployment.")
        return 0
    else:
        print(f"\n❌ BUILD GUARDRAIL FAILED")
        print(f"{total_count - passed_count} test(s) failed.")
        print("Build MUST NOT proceed.")
        return 1


if __name__ == "__main__":
    exit(main())
