"""
🔒 CONTRACT VALIDATION: Agent 2.5 (Budget Pathfinder)

Tests that Agent 2.5 strictly complies with the formal scoring contract:
  • viability_score ∈ [0.0, 1.0] for ALL paths
  • Maximum 3 paths returned
  • Paths ranked by viability_score DESC
  • Rank field present (1-based)
  • Required fields present
  • Graceful failure (never crash)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent2_5_pathfinder import budget_pathfinder_agent


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


# Mock AgentState as dict
def AgentState(**kwargs):
    return kwargs


def test_contract_compliance():
    """
    🔒 CRITICAL TEST: Verify all paths have viability_score ∈ [0.0, 1.0]
    """
    print("=" * 80)
    print("CONTRACT TEST 1: viability_score Range Validation")
    print("=" * 80)

    # Unaffordable user (low income, high expenses)
    profile = UserProfile(
        user_id="test_user",
        monthly_income=3000,
        monthly_expenses=2500,
        savings=1000,
        current_debt=5000,
        credit_score=650,
        risk_tolerance="moderate"
    )

    # Mock products (all unaffordable)
    products = [
        {
            'product_id': 'laptop_1',
            'name': 'MacBook Pro 16"',
            'price': 2500,
            'cluster_id': 3,
            'financing_available': True,
            'in_stock': True
        },
        {
            'product_id': 'laptop_2',
            'name': 'Dell XPS 15',
            'price': 2000,
            'cluster_id': 3,
            'financing_available': True,
            'in_stock': True
        }
    ]

    state = AgentState(
        user_profile=profile,
        candidate_products=products,
        all_unaffordable=True  # Trigger Agent 2.5
    )

    # Execute Agent 2.5
    result = budget_pathfinder_agent.execute(state)
    paths = result.get('alternative_paths', [])

    print(f"\nGenerated {len(paths)} paths")

    # 🔒 CONTRACT CHECK 1: viability_score range
    violations = []
    for i, path in enumerate(paths):
        viability = path.get('viability_score')

        if viability is None:
            violations.append(f"Path {i+1}: Missing viability_score")
        elif not isinstance(viability, (int, float)):
            violations.append(f"Path {i+1}: viability_score is not numeric ({type(viability)})")
        elif viability < 0.0 or viability > 1.0:
            violations.append(f"Path {i+1}: viability_score = {viability} (MUST be 0.0-1.0)")
        else:
            print(f"✓ Path {i+1}: viability_score = {viability:.3f} ∈ [0.0, 1.0]")

    if violations:
        print("\n🚨 CONTRACT VIOLATIONS:")
        for v in violations:
            print(f"   {v}")
        return False

    print("\n✅ PASS: All viability_scores in range [0.0, 1.0]")
    return True


def test_maximum_3_paths():
    """
    🔒 CONTRACT TEST: Maximum 3 paths returned
    """
    print("\n" + "=" * 80)
    print("CONTRACT TEST 2: Maximum 3 Paths")
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

    # Many products to generate many paths
    products = [
        {'product_id': f'p{i}', 'name': f'Product {i}', 'price': 2000 + i*100,
         'cluster_id': 3, 'financing_available': True, 'in_stock': True}
        for i in range(5)
    ]

    state = AgentState(
        user_profile=profile,
        candidate_products=products,
        all_unaffordable=True
    )

    result = budget_pathfinder_agent.execute(state)
    paths = result.get('alternative_paths', [])

    print(f"\nGenerated {len(paths)} paths")

    if len(paths) > 3:
        print(f"🚨 CONTRACT VIOLATION: {len(paths)} paths returned (max is 3)")
        return False

    print(f"✅ PASS: {len(paths)} ≤ 3 paths")
    return True


def test_ranking():
    """
    🔒 CONTRACT TEST: Paths sorted by viability_score DESC with rank field
    """
    print("\n" + "=" * 80)
    print("CONTRACT TEST 3: Ranking and Sorting")
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

    state = AgentState(
        user_profile=profile,
        candidate_products=products,
        all_unaffordable=True
    )

    result = budget_pathfinder_agent.execute(state)
    paths = result.get('alternative_paths', [])

    # Check sorting
    viability_scores = [p.get('viability_score', 0) for p in paths]
    sorted_scores = sorted(viability_scores, reverse=True)

    if viability_scores != sorted_scores:
        print(f"🚨 CONTRACT VIOLATION: Paths not sorted by viability DESC")
        print(f"   Actual:   {[round(v, 3) for v in viability_scores]}")
        print(f"   Expected: {[round(v, 3) for v in sorted_scores]}")
        return False

    print(f"✓ Paths correctly sorted by viability DESC")
    print(f"  Scores: {[round(v, 3) for v in viability_scores]}")

    # Check rank field
    violations = []
    for i, path in enumerate(paths):
        expected_rank = i + 1
        actual_rank = path.get('rank')

        if actual_rank is None:
            violations.append(f"Path {i+1}: Missing 'rank' field")
        elif actual_rank != expected_rank:
            violations.append(f"Path {i+1}: rank = {actual_rank} (expected {expected_rank})")
        else:
            print(f"✓ Path {i+1}: rank = {actual_rank}")

    if violations:
        print("\n🚨 RANK VIOLATIONS:")
        for v in violations:
            print(f"   {v}")
        return False

    print("\n✅ PASS: Correct sorting and ranking")
    return True


def test_required_fields():
    """
    🔒 CONTRACT TEST: Required fields present in all paths
    """
    print("\n" + "=" * 80)
    print("CONTRACT TEST 4: Required Fields")
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

    state = AgentState(
        user_profile=profile,
        candidate_products=products,
        all_unaffordable=True
    )

    result = budget_pathfinder_agent.execute(state)
    paths = result.get('alternative_paths', [])

    # 🔒 CONTRACT: Required fields
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
        if not isinstance(path.get('pros', []), list):
            violations.append(f"Path {i+1}: 'pros' must be a list")
        if not isinstance(path.get('cons', []), list):
            violations.append(f"Path {i+1}: 'cons' must be a list")

    if violations:
        print("🚨 FIELD VIOLATIONS:")
        for v in violations:
            print(f"   {v}")
        return False

    print(f"✅ PASS: All {len(paths)} paths have required fields")
    print(f"   Required: {required_fields}")
    return True


def test_activation_condition():
    """
    🔒 CONTRACT TEST: Only activates when all_unaffordable == True
    """
    print("\n" + "=" * 80)
    print("CONTRACT TEST 5: Activation Condition")
    print("=" * 80)

    profile = UserProfile(
        user_id="test_user",
        monthly_income=10000,
        monthly_expenses=3000,
        savings=20000,
        current_debt=0,
        credit_score=800,
        risk_tolerance="moderate"
    )

    products = [
        {'product_id': 'p1', 'name': 'Product 1', 'price': 500,
         'cluster_id': 3, 'financing_available': True, 'in_stock': True}
    ]

    # Test 1: all_unaffordable = False (should skip)
    state_affordable = AgentState(
        user_profile=profile,
        candidate_products=products,
        all_unaffordable=False
    )

    result = budget_pathfinder_agent.execute(state_affordable)
    paths = result.get('alternative_paths', [])

    if paths:
        print("🚨 VIOLATION: Agent 2.5 ran when all_unaffordable=False")
        return False

    print("✓ Agent 2.5 correctly skipped when all_unaffordable=False")

    # Test 2: all_unaffordable = True (should run)
    state_unaffordable = AgentState(
        user_profile=profile,
        candidate_products=products,
        all_unaffordable=True
    )

    result = budget_pathfinder_agent.execute(state_unaffordable)
    paths = result.get('alternative_paths', [])

    if not paths:
        print("🚨 VIOLATION: Agent 2.5 did not run when all_unaffordable=True")
        return False

    print(f"✓ Agent 2.5 correctly ran when all_unaffordable=True (generated {len(paths)} paths)")

    print("\n✅ PASS: Activation condition respected")
    return True


def test_graceful_failure():
    """
    🔒 CONTRACT TEST: Graceful failure (never crash pipeline)
    """
    print("\n" + "=" * 80)
    print("CONTRACT TEST 6: Graceful Failure")
    print("=" * 80)

    # Test with bad data
    profile = UserProfile(
        user_id="test_user",
        monthly_income=3000,
        monthly_expenses=2500,
        savings=1000,
        current_debt=5000,
        credit_score=650,
        risk_tolerance="moderate"
    )

    # Empty products
    state = AgentState(
        user_profile=profile,
        candidate_products=[],
        all_unaffordable=True
    )

    try:
        result = budget_pathfinder_agent.execute(state)
        paths = result.get('alternative_paths', [])
        print(f"✓ Handled empty products gracefully (returned {len(paths)} paths)")
    except Exception as e:
        print(f"🚨 VIOLATION: Crashed on empty products: {e}")
        return False

    print("\n✅ PASS: Graceful failure handling")
    return True


def main():
    """Run all contract validation tests"""
    print("\n" + "=" * 80)
    print("🔒 AGENT 2.5 CONTRACT VALIDATION")
    print("=" * 80)
    print("\nContract Requirements:")
    print("  • viability_score ∈ [0.0, 1.0] (NOT 0-100)")
    print("  • Maximum 3 paths")
    print("  • Sorted by viability DESC")
    print("  • Rank field (1-based)")
    print("  • Required fields: type, strategy, description, pros, cons")
    print("  • Activation: only when all_unaffordable=True")
    print("  • Graceful failure (never crash)")
    print()

    tests = [
        ("viability_score ∈ [0.0, 1.0]", test_contract_compliance),
        ("Maximum 3 paths", test_maximum_3_paths),
        ("Ranking and sorting", test_ranking),
        ("Required fields", test_required_fields),
        ("Activation condition", test_activation_condition),
        ("Graceful failure", test_graceful_failure),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n🚨 TEST CRASHED: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
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
        print("\n✅ CONTRACT VALIDATION PASSED")
        print("Agent 2.5 fully complies with the formal scoring contract.")
        return 0
    else:
        print(f"\n❌ CONTRACT VALIDATION FAILED")
        print(f"{total_count - passed_count} test(s) failed.")
        return 1


if __name__ == "__main__":
    exit(main())
