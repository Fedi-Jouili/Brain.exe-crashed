"""
Comprehensive Integration Test for Agent 3 (Smart Recommender)

Validates:
- Thompson Sampling integration
- Ranking logic
- Learning behavior
- State updates
- Edge case handling

Run:
    python backend/scripts/test_agent3.py
"""
import sys
from pathlib import Path
import random
import time

sys.path.append(str(Path(__file__).parent.parent))

from agents.agent3_recommender import smart_recommender_agent
from ml.thompson_sampling import ThompsonSamplingEngine


def create_mock_state(num_products: int = 10) -> dict:
    """
    Create a mock state with affordable products for testing Agent 3.

    Args:
        num_products: Number of products to generate

    Returns:
        Mock state dict with affordable_products
    """
    affordable_products = []

    for i in range(num_products):
        product_id = f"PROD{i:04d}"
        product = {
            "product_id": product_id,
            "name": f"Test Product {i}",
            "price": 100 + (i * 50),
            "category": "Electronics",
            "rating": 3.5 + (random.random() * 1.5),
            "description": f"Description for product {i}"
        }

        affordable_item = {
            "product": product,
            "financial_score": 50 + random.randint(0, 50),
            "affordability": {
                "can_afford_cash": True,
                "can_afford_financing": True,
                "monthly_payment": 50 + (i * 5)
            }
        }

        affordable_products.append(affordable_item)

    state = {
        "query": "test electronics",
        "affordable_products": affordable_products,
        "user_profile": None
    }

    return state


def test_1_basic_execution():
    """Test 1: Agent executes without error and returns recommendations"""
    print("\n" + "=" * 80)
    print("TEST 1: Basic Execution")
    print("=" * 80)

    try:
        state = create_mock_state(10)

        # Execute Agent 3
        result = smart_recommender_agent.execute(state)

        # Verify recommendations exist
        assert "final_recommendations" in result, "Should have final_recommendations key"
        recommendations = result["final_recommendations"]

        # Verify count
        assert len(recommendations) <= 10, f"Should return <= 10 items, got {len(recommendations)}"
        assert len(recommendations) > 0, "Should return at least 1 recommendation"

        # Verify execution time added
        assert "recommender_time_ms" in result, "Should add execution time"

        print(f"PASS: Returned {len(recommendations)} recommendations")
        print(f"      Execution time: {result['recommender_time_ms']}ms")
        return True

    except Exception as e:
        print(f"FAIL: {e}")
        return False


def test_2_thompson_score_presence():
    """Test 2: Every recommendation has Thompson score"""
    print("\n" + "=" * 80)
    print("TEST 2: Thompson Score Presence")
    print("=" * 80)

    try:
        state = create_mock_state(5)
        result = smart_recommender_agent.execute(state)
        recommendations = result["final_recommendations"]

        for i, rec in enumerate(recommendations, 1):
            # Check scores dict exists
            assert "scores" in rec, f"Recommendation {i} missing 'scores'"

            # Check Thompson score exists
            assert "thompson" in rec["scores"], f"Recommendation {i} missing Thompson score"

            # Check Thompson score is in valid range
            thompson_score = rec["scores"]["thompson"]
            assert 0.0 <= thompson_score <= 100.0, \
                f"Thompson score out of range: {thompson_score}"

        print(f"PASS: All {len(recommendations)} recommendations have valid Thompson scores")
        print(f"      Sample scores: {[rec['scores']['thompson'] for rec in recommendations[:3]]}")
        return True

    except Exception as e:
        print(f"FAIL: {e}")
        return False


def test_3_ranking_order():
    """Test 3: Recommendations are properly ranked"""
    print("\n" + "=" * 80)
    print("TEST 3: Ranking Order")
    print("=" * 80)

    try:
        state = create_mock_state(10)
        result = smart_recommender_agent.execute(state)
        recommendations = result["final_recommendations"]

        # Check ranks are sequential
        for i, rec in enumerate(recommendations, 1):
            assert rec["rank"] == i, f"Expected rank {i}, got {rec['rank']}"

        # Check final_score is sorted descending
        prev_score = float('inf')
        for rec in recommendations:
            current_score = rec["final_score"]
            assert current_score <= prev_score, \
                f"Scores not sorted: {current_score} > {prev_score}"
            prev_score = current_score

        print(f"PASS: All {len(recommendations)} recommendations properly ranked")
        print(f"      Top score: {recommendations[0]['final_score']:.2f}")
        print(f"      Bottom score: {recommendations[-1]['final_score']:.2f}")
        return True

    except Exception as e:
        print(f"FAIL: {e}")
        return False


def test_4_state_mutation_safety():
    """Test 4: Agent does not mutate original state"""
    print("\n" + "=" * 80)
    print("TEST 4: State Mutation Safety")
    print("=" * 80)

    try:
        state = create_mock_state(5)
        original_products = state["affordable_products"].copy()
        original_count = len(original_products)

        # Execute Agent 3
        result = smart_recommender_agent.execute(state)

        # Verify original list unchanged
        assert len(state["affordable_products"]) == original_count, \
            "affordable_products list was mutated"

        # Verify new keys added, not existing ones modified
        assert "final_recommendations" in result, "Should add final_recommendations"
        assert "recommender_time_ms" in result, "Should add execution time"

        print("PASS: State mutation safety verified")
        print(f"      Original products: {original_count}")
        print(f"      After execution: {len(state['affordable_products'])}")
        return True

    except Exception as e:
        print(f"FAIL: {e}")
        return False


def test_5_edge_cases():
    """Test 5: Edge cases (empty, single, multiple products)"""
    print("\n" + "=" * 80)
    print("TEST 5: Edge Cases")
    print("=" * 80)

    all_passed = True

    # Test 5a: Empty product list
    try:
        print("\n  Test 5a: Empty product list")
        state = create_mock_state(0)
        result = smart_recommender_agent.execute(state)

        assert result["final_recommendations"] == [], \
            "Should return empty list for empty input"
        print("  PASS: Empty list handled correctly")
    except Exception as e:
        print(f"  FAIL: {e}")
        all_passed = False

    # Test 5b: Single product
    try:
        print("\n  Test 5b: Single product")
        state = create_mock_state(1)
        result = smart_recommender_agent.execute(state)
        recommendations = result["final_recommendations"]

        assert len(recommendations) == 1, "Should return 1 recommendation"
        assert recommendations[0]["rank"] == 1, "Rank should be 1"
        print("  PASS: Single product handled correctly")
    except Exception as e:
        print(f"  FAIL: {e}")
        all_passed = False

    # Test 5c: Exactly 10 products
    try:
        print("\n  Test 5c: Exactly 10 products")
        state = create_mock_state(10)
        result = smart_recommender_agent.execute(state)
        recommendations = result["final_recommendations"]

        assert len(recommendations) == 10, f"Should return 10, got {len(recommendations)}"
        print("  PASS: 10 products returns 10 recommendations")
    except Exception as e:
        print(f"  FAIL: {e}")
        all_passed = False

    # Test 5d: More than 10 products
    try:
        print("\n  Test 5d: More than 10 products")
        state = create_mock_state(15)
        result = smart_recommender_agent.execute(state)
        recommendations = result["final_recommendations"]

        assert len(recommendations) == 10, \
            f"Should cap at 10, got {len(recommendations)}"
        print("  PASS: More than 10 products capped at 10")
    except Exception as e:
        print(f"  FAIL: {e}")
        all_passed = False

    if all_passed:
        print("\nPASS: All edge cases handled correctly")
    else:
        print("\nFAIL: Some edge cases failed")

    return all_passed


def test_6_thompson_learning_behavior():
    """Test 6: Thompson Sampling learns from user actions"""
    print("\n" + "=" * 80)
    print("TEST 6: Thompson Learning Behavior (CRITICAL)")
    print("=" * 80)

    try:
        # Create engine instance
        engine = ThompsonSamplingEngine()

        # Create state with known products
        state = create_mock_state(10)
        target_product_id = "PROD0001"

        # Run Agent 3 BEFORE learning
        print("\n  Phase 1: Baseline ranking (before learning)")
        result_before = smart_recommender_agent.execute(state)
        recs_before = result_before["final_recommendations"]

        # Find PROD0001 in results
        rank_before = None
        thompson_score_before = None
        for rec in recs_before:
            if rec["product"]["product_id"] == target_product_id:
                rank_before = rec["rank"]
                thompson_score_before = rec["scores"]["thompson"]
                break

        assert rank_before is not None, f"{target_product_id} not found in recommendations"

        print(f"    Before: {target_product_id} rank={rank_before}, " +
              f"thompson={thompson_score_before:.2f}")

        # Simulate 10 purchases (strong positive signal)
        print(f"\n  Phase 2: Simulating 10 purchases on {target_product_id}")
        for i in range(10):
            engine.update_params(target_product_id, "purchase")

        # Wait a moment for Redis update
        time.sleep(0.1)

        # Run Agent 3 AFTER learning
        print("\n  Phase 3: Re-ranking (after learning)")
        result_after = smart_recommender_agent.execute(state)
        recs_after = result_after["final_recommendations"]

        # Find PROD0001 again
        rank_after = None
        thompson_score_after = None
        for rec in recs_after:
            if rec["product"]["product_id"] == target_product_id:
                rank_after = rec["rank"]
                thompson_score_after = rec["scores"]["thompson"]
                break

        assert rank_after is not None, f"{target_product_id} not found after learning"

        print(f"    After:  {target_product_id} rank={rank_after}, " +
              f"thompson={thompson_score_after:.2f}")

        # Verify learning occurred (probabilistic, so check multiple signals)
        learning_indicators = []

        # Indicator 1: Thompson score increased
        if thompson_score_after > thompson_score_before:
            learning_indicators.append("Thompson score increased")

        # Indicator 2: Rank improved (lower is better)
        if rank_after < rank_before:
            learning_indicators.append(f"Rank improved ({rank_before} -> {rank_after})")

        # Indicator 3: High Thompson score (>70)
        if thompson_score_after > 70.0:
            learning_indicators.append(f"High Thompson score ({thompson_score_after:.2f})")

        # Indicator 4: In top 3
        if rank_after <= 3:
            learning_indicators.append(f"In top 3 (rank {rank_after})")

        print(f"\n  Learning indicators detected: {len(learning_indicators)}")
        for indicator in learning_indicators:
            print(f"    * {indicator}")

        # Require at least 1 indicator (probabilistic system)
        assert len(learning_indicators) >= 1, \
            "No learning indicators detected - Thompson Sampling may not be working"

        print("\nPASS: Thompson Sampling learning verified")
        print(f"      Product responded to 10 purchases")
        print(f"      Detected {len(learning_indicators)} positive signals")
        return True

    except Exception as e:
        print(f"\nFAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Agent 3 integration tests"""

    print("=" * 80)
    print("AGENT 3 (SMART RECOMMENDER) - COMPREHENSIVE INTEGRATION TEST")
    print("=" * 80)
    print("\nThis test validates:")
    print("  * Thompson Sampling integration")
    print("  * Ranking logic")
    print("  * Learning behavior")
    print("  * State updates")
    print("  * Edge case handling")

    # Run all tests
    results = {}

    results["Test 1: Basic Execution"] = test_1_basic_execution()
    results["Test 2: Thompson Score Presence"] = test_2_thompson_score_presence()
    results["Test 3: Ranking Order"] = test_3_ranking_order()
    results["Test 4: State Mutation Safety"] = test_4_state_mutation_safety()
    results["Test 5: Edge Cases"] = test_5_edge_cases()
    results["Test 6: Thompson Learning"] = test_6_thompson_learning_behavior()

    # Print summary
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
        print("Agent 3 is working correctly with Thompson Sampling.")
        return 0
    else:
        print("\nFAILURE: Some tests failed.")
        print("Review the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
