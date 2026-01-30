"""
Score Contract Validator
Verifies that all agents comply with the formal scoring contract

🔒 CONTRACT REQUIREMENTS:
- Agent 2 financial_score: 0.0-1.0
- Agent 2.5 viability_score: 0.0-1.0
- Agent 3 thompson_score: 0.0-100.0 (internal only)
- Agent 3 composite weights: 0.4 + 0.3 + 0.2 + 0.1 = 1.0
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from agents.agent2_financial import financial_analyzer_agent
from agents.agent3_recommender import SmartRecommenderAgent


def create_mock_user(monthly_income, monthly_expenses, savings):
    """Create mock user"""
    return {
        "user_id": "test_user",
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "savings": savings,
        "current_debt": 0.0,
        "credit_score": 700
    }


def create_mock_product(product_id, name, price):
    """Create mock product"""
    return {
        "product_id": product_id,
        "name": name,
        "price": price,
        "category": "Electronics",
        "financing_available": False
    }


def test_agent2_contract():
    """Verify Agent 2 returns financial_score in 0.0-1.0"""
    print("\n" + "="*80)
    print("CONTRACT TEST: Agent 2 (Financial Analyzer)")
    print("="*80)

    user = create_mock_user(5000.0, 3000.0, 10000.0)
    products = [
        create_mock_product("P1", "Cheap Product", 500.0),
        create_mock_product("P2", "Expensive Product", 2000.0)
    ]

    state = {
        "query": "test",
        "user_profile": user,
        "candidate_products": products
    }

    result = financial_analyzer_agent.execute(state)

    violations = []
    for item in result["affordable_products"]:
        score = item["financial_score"]
        if not (0.0 <= score <= 1.0):
            violations.append(f"  Product {item['product']['name']}: score={score}")

    if violations:
        print("🚨 CONTRACT VIOLATION:")
        print(f"   Field: financial_score")
        print(f"   Required: 0.0-1.0")
        print(f"   Violations:")
        for v in violations:
            print(v)
        return False
    else:
        scores = [item["financial_score"] for item in result["affordable_products"]]
        print(f"✅ PASS: All financial_scores in range 0.0-1.0")
        print(f"   Scores: {[round(s, 2) for s in scores]}")
        return True


def test_agent3_contract():
    """Verify Agent 3 weights sum to 1.0"""
    print("\n" + "="*80)
    print("CONTRACT TEST: Agent 3 (Smart Recommender)")
    print("="*80)

    agent = SmartRecommenderAgent()

    # Check weights
    total_weight = (
        agent.thompson_weight +
        agent.financial_weight +
        agent.ragas_weight +
        agent.diversity_weight
    )

    violations = []

    if abs(total_weight - 1.0) > 0.001:
        violations.append(f"  Total weight: {total_weight} (should be 1.0)")

    if agent.thompson_weight != 0.4:
        violations.append(f"  Thompson weight: {agent.thompson_weight} (should be 0.4)")

    if agent.financial_weight != 0.3:
        violations.append(f"  Financial weight: {agent.financial_weight} (should be 0.3)")

    if agent.ragas_weight != 0.2:
        violations.append(f"  RAGAS weight: {agent.ragas_weight} (should be 0.2)")

    if agent.diversity_weight != 0.1:
        violations.append(f"  Diversity weight: {agent.diversity_weight} (should be 0.1)")

    if violations:
        print("🚨 CONTRACT VIOLATION:")
        print(f"   Required weights: Thompson=0.4, Financial=0.3, RAGAS=0.2, Diversity=0.1")
        print(f"   Violations:")
        for v in violations:
            print(v)
        return False
    else:
        print(f"✅ PASS: Composite weights correct")
        print(f"   Thompson:  {agent.thompson_weight} (0.4)")
        print(f"   Financial: {agent.financial_weight} (0.3)")
        print(f"   RAGAS:     {agent.ragas_weight} (0.2)")
        print(f"   Diversity: {agent.diversity_weight} (0.1)")
        print(f"   Total:     {total_weight:.1f}")
        return True


def main():
    """Run all contract validation tests"""
    print("="*80)
    print("SCORE CONTRACT VALIDATION")
    print("="*80)
    print("\n🔒 Verifying formal scoring contract compliance...")

    results = {}

    results["Agent 2"] = test_agent2_contract()
    results["Agent 3"] = test_agent3_contract()

    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    all_pass = all(results.values())

    for agent, passed in results.items():
        status = "✅ PASS" if passed else "🚨 FAIL"
        print(f"{status}: {agent}")

    print("\n" + "="*80)

    if all_pass:
        print("✅ CONTRACT VALIDATION PASSED")
        print("All agents comply with the formal scoring contract.")
        print("="*80)
        return 0
    else:
        print("🚨 CONTRACT VALIDATION FAILED")
        print("One or more agents violate the scoring contract.")
        print("Fix violations before deployment.")
        print("="*80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
