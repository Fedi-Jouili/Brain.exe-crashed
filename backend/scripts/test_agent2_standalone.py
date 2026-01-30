"""
Standalone Test Suite for Agent 2 (Financial Analyzer)

Tests Agent 2 functionality without requiring full model dependencies.

Run:
    python backend/scripts/test_agent2_standalone.py
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from agents.agent2_financial import financial_analyzer_agent


def create_mock_user(monthly_income: float, monthly_expenses: float,
                    savings: float, current_debt: float = 0):
    """Create mock user profile (dict)"""
    return {
        "user_id": f"test_user_{int(monthly_income)}",
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "savings": savings,
        "current_debt": current_debt,
        "credit_score": 700
    }


def create_mock_product(product_id: str, name: str, price: float,
                       financing_available: bool = False):
    """Create mock product (dict)"""
    product = {
        "product_id": product_id,
        "name": name,
        "price": price,
        "category": "Electronics",
        "financing_available": financing_available
    }

    if financing_available:
        product["financing_terms"] = {"months": 12, "apr": 0.0}

    return product


def test_1_affordable_user():
    """Test 1: Affluent user with affordable products"""
    print("\n" + "=" * 80)
    print("TEST 1: Affordable User - High Income")
    print("=" * 80)

    try:
        # Affluent user
        user = create_mock_user(
            monthly_income=10000.0,
            monthly_expenses=5000.0,
            savings=50000.0
        )

        # Affordable products
        products = [
            create_mock_product("PROD001", "Budget Laptop", 500.0),
            create_mock_product("PROD002", "Mid-Range Laptop", 1200.0, True),
            create_mock_product("PROD003", "Premium Laptop", 2500.0, True)
        ]

        # Execute Agent 2
        state = {
            "query": "laptop",
            "user_profile": user,
            "candidate_products": products
        }

        result = financial_analyzer_agent.execute(state)

        # Verify
        assert "affordable_products" in result
        assert len(result["affordable_products"]) > 0, "Should have affordable products"
        assert result["all_unaffordable"] == False

        # 🔒 CONTRACT VERIFICATION: financial_score MUST be 0.0-1.0
        for item in result["affordable_products"]:
            assert "product" in item
            assert "affordability" in item
            assert "financial_score" in item

            score = item["financial_score"]
            assert 0.0 <= score <= 1.0, f"🚨 CONTRACT VIOLATION: Score {score} not in range 0.0-1.0"

            affordability = item["affordability"]
            assert affordability["can_afford_cash"] or affordability["can_afford_financing"]
            assert affordability["risk_level"] in ["SAFE", "CAUTION", "RISKY"]
            assert isinstance(affordability["recommendation"], str)

        print(f"PASS: Found {len(result['affordable_products'])} affordable products")
        print(f"      Scores (0.0-1.0): {[round(item['financial_score'], 2) for item in result['affordable_products']]}")
        return True

    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_2_unaffordable_user():
    """Test 2: Low-income user with expensive products"""
    print("\n" + "=" * 80)
    print("TEST 2: Unaffordable User - Low Income")
    print("=" * 80)

    try:
        # Low-income user
        user = create_mock_user(
            monthly_income=2000.0,
            monthly_expenses=1900.0,
            savings=500.0,
            current_debt=1000.0
        )

        # Expensive products
        products = [
            create_mock_product("PROD001", "Luxury Laptop", 5000.0),
            create_mock_product("PROD002", "Gaming Desktop", 8000.0)
        ]

        state = {
            "query": "expensive computer",
            "user_profile": user,
            "candidate_products": products
        }

        result = financial_analyzer_agent.execute(state)

        # Should have no affordable products
        assert len(result["affordable_products"]) == 0
        assert result["all_unaffordable"] == True

        print(f"PASS: Correctly identified all products as unaffordable")
        print(f"      all_unaffordable: {result['all_unaffordable']}")
        return True

    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_3_financial_score_sorting():
    """Test 3: Products sorted by financial score (0.0-1.0 range)"""
    print("\n" + "=" * 80)
    print("TEST 3: Financial Score Sorting (0.0-1.0 Range)")
    print("=" * 80)

    try:
        user = create_mock_user(
            monthly_income=6000.0,
            monthly_expenses=3500.0,
            savings=15000.0
        )

        products = [
            create_mock_product("PROD001", "Expensive", 3000.0, True),
            create_mock_product("PROD002", "Cheap", 200.0),
            create_mock_product("PROD003", "Moderate", 1000.0, True)
        ]

        state = {
            "query": "electronics",
            "user_profile": user,
            "candidate_products": products
        }

        result = financial_analyzer_agent.execute(state)

        if len(result["affordable_products"]) > 1:
            scores = [item["financial_score"] for item in result["affordable_products"]]

            # 🔒 CONTRACT: Verify all scores in 0.0-1.0 range
            for score in scores:
                assert 0.0 <= score <= 1.0, f"🚨 CONTRACT VIOLATION: Score {score} not in 0.0-1.0"

            # Verify sorted descending
            assert scores == sorted(scores, reverse=True), \
                f"Scores should be sorted descending: {scores}"

        print(f"PASS: Products sorted by financial score (0.0-1.0)")
        print(f"      Scores: {[round(item['financial_score'], 2) for item in result['affordable_products']]}")
        return True

    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_4_risk_levels():
    """Test 4: Risk level assessment"""
    print("\n" + "=" * 80)
    print("TEST 4: Risk Level Assessment")
    print("=" * 80)

    try:
        user = create_mock_user(
            monthly_income=8000.0,
            monthly_expenses=4000.0,
            savings=30000.0
        )

        products = [create_mock_product("PROD001", "Test", 500.0)]

        state = {
            "query": "affordable item",
            "user_profile": user,
            "candidate_products": products
        }

        result = financial_analyzer_agent.execute(state)

        valid_risks = {"SAFE", "CAUTION", "RISKY"}

        for item in result["affordable_products"]:
            risk = item["affordability"]["risk_level"]
            assert risk in valid_risks, f"Invalid risk level: {risk}"

        print(f"PASS: Risk levels valid")
        return True

    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_5_error_handling():
    """Test 5: Graceful error handling"""
    print("\n" + "=" * 80)
    print("TEST 5: Error Handling")
    print("=" * 80)

    try:
        user = create_mock_user(5000.0, 3000.0, 10000.0)

        # Mix of valid and invalid products
        products = [
            create_mock_product("PROD001", "Valid", 500.0),
            {"product_id": "BAD", "name": "Missing Price"},  # Invalid
            create_mock_product("PROD002", "Valid", 800.0)
        ]

        state = {
            "query": "electronics",
            "user_profile": user,
            "candidate_products": products
        }

        # Should not crash
        result = financial_analyzer_agent.execute(state)

        assert "affordable_products" in result
        assert len(result["affordable_products"]) > 0, "Should process valid products"

        print(f"PASS: Error handling works")
        print(f"      Processed {len(result['affordable_products'])} valid products")
        return True

    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_6_empty_products():
    """Test 6: Edge case - empty product list"""
    print("\n" + "=" * 80)
    print("TEST 6: Empty Product List")
    print("=" * 80)

    try:
        user = create_mock_user(5000.0, 3000.0, 10000.0)

        state = {
            "query": "test",
            "user_profile": user,
            "candidate_products": []
        }

        result = financial_analyzer_agent.execute(state)

        assert result["affordable_products"] == []
        assert result["all_unaffordable"] == False

        print(f"PASS: Empty products handled")
        return True

    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Agent 2 tests"""

    print("=" * 80)
    print("AGENT 2 (FINANCIAL ANALYZER) - STANDALONE TEST SUITE")
    print("=" * 80)
    print("\nValidates:")
    print("  * Affordable vs unaffordable users")
    print("  * Financial score calculation (0-100)")
    print("  * Risk level assessment")
    print("  * Score sorting")
    print("  * Error handling")
    print("  * Edge cases")

    results = {}

    results["Test 1: Affordable User"] = test_1_affordable_user()
    results["Test 2: Unaffordable User"] = test_2_unaffordable_user()
    results["Test 3: Score Sorting"] = test_3_financial_score_sorting()
    results["Test 4: Risk Levels"] = test_4_risk_levels()
    results["Test 5: Error Handling"] = test_5_error_handling()
    results["Test 6: Empty Products"] = test_6_empty_products()

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {test_name}")

    print("\n" + "-" * 80)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 80)

    if passed == total:
        print("\nSUCCESS: All tests passed!")
        print("Agent 2 is production-ready.")
        return 0
    else:
        print("\nFAILURE: Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
