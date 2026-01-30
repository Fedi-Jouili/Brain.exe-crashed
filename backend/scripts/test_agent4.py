"""
Test Agent 4: Explainer
Tests LLM explanation generation, fact verification, and trust scoring
"""
import sys
import logging
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from agents.agent1_discovery import product_discovery_agent
from agents.agent2_financial import financial_analyzer_agent
from agents.agent3_recommender import smart_recommender_agent
from agents.agent4_explainer import explainer_agent
from models.schemas import UserProfile
from models.state import AgentState

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')


def test_agent4_full_pipeline():
    """Test Agent 4 with full pipeline (Agents 1 → 2 → 3 → 4)"""
    
    print("=" * 80)
    print("🧪 TESTING AGENT 4: EXPLAINER")
    print("=" * 80)
    print()
    
    # Test Scenario 1: Medium Income User
    print("📊 TEST 1: Medium Income User - Professional Laptop")
    print("-" * 80)
    
    user = UserProfile(
        user_id="test_user_agent4",
        monthly_income=6000.0,
        monthly_expenses=3800.0,
        savings=20000.0,
        current_debt=5000.0,
        credit_score=720
    )
    
    state = AgentState(
        query="professional laptop for software development",
        user_profile=user,
        recommendations=[],
        path_taken="DEEP"
    )
    
    print(f"User Profile:")
    print(f"  Monthly Income: ${user.monthly_income:.2f}")
    print(f"  Disposable Income: ${user.monthly_income - user.monthly_expenses:.2f}")
    print(f"  Credit Score: {user.credit_score}")
    print(f"  Savings: ${user.savings:.2f}")
    print(f"  Query: '{state['query']}'")
    print()
    
    # Run Agent 1
    print("Step 1: Agent 1 (Product Discovery)...")
    state = product_discovery_agent.execute(state)
    candidates = len(state.get('candidate_products', []))
    print(f"   ✅ Found {candidates} candidates")
    
    if candidates == 0:
        print("   ⚠️  No products found - skipping test")
        print()
        return
    
    # Run Agent 2
    print("Step 2: Agent 2 (Financial Analyzer)...")
    state = financial_analyzer_agent.execute(state)
    affordable = len(state.get('affordable_products', []))
    print(f"   ✅ {affordable} affordable products")
    
    if affordable == 0:
        print("   ⚠️  No affordable products - skipping test")
        print()
        return
    
    # Run Agent 3
    print("Step 3: Agent 3 (Smart Recommender)...")
    state = smart_recommender_agent.execute(state)
    recommendations = len(state.get('final_recommendations', []))
    print(f"   ✅ Generated {recommendations} recommendations")
    print(f"   ⏱️  Execution time: {state.get('recommender_time_ms', 0):.0f}ms")
    
    if recommendations == 0:
        print("   ⚠️  No recommendations - skipping test")
        print()
        return
    
    # Run Agent 4
    print("Step 4: Agent 4 (Explainer)...")
    state = explainer_agent.execute(state)
    print(f"   ✅ Generated explanations")
    print(f"   ⏱️  Execution time: {state.get('agent4_execution_time', 0):.0f}ms")
    print()
    
    # Display results
    print("=" * 80)
    print("🏆 TOP 3 RECOMMENDATIONS WITH EXPLANATIONS")
    print("=" * 80)
    print()
    
    top_3 = state['recommendations'][:3]
    
    for i, rec in enumerate(top_3, 1):
        product = rec['product']
        scores = rec.get('scores', {})
        
        print(f"#{i}. {product.name}")
        print(f"{'=' * 80}")
        print()
        
        # Product Details
        print(f"📦 Product Information:")
        print(f"   Price: ${product.price:.2f}")
        print(f"   Category: {product.category.upper()}")
        print(f"   Rating: {product.rating}/5 ⭐ ({product.num_reviews} reviews)")
        print(f"   Financing: {'Available' if product.financing_available else 'Cash Only'}")
        print()
        
        # Score Breakdown
        print(f"📊 Scoring Breakdown:")
        print(f"   Thompson Sampling:    {scores.get('thompson', 0):6.1f}/100")
        print(f"   Collaborative Filter: {scores.get('collaborative', 0):6.1f}/100")
        print(f"   RAGAS Relevancy:      {scores.get('ragas', 0):6.1f}/100")
        print(f"   Financial Score:      {scores.get('financial', 0):6.1f}/100")
        print(f"   {'─' * 40}")
        print(f"   FINAL SCORE:          {rec.get('final_score', 0):6.1f}/100")
        print()
        
        # Original Explanation (from Agent 3)
        print(f"💬 Quick Summary:")
        print(f"   {rec.get('explanation', 'N/A')}")
        print()
        
        # Detailed Explanation (from Agent 4)
        detailed = rec.get('detailed_explanation', '')
        trust = rec.get('trust_score', 0)
        verified = rec.get('verified', False)
        
        if detailed:
            print(f"📝 Detailed Explanation:")
            print(f"   {detailed}")
            print()
            
            # Trust Score
            trust_icon = "✅" if verified else "⚠️"
            print(f"🔍 Fact Verification:")
            print(f"   Trust Score: {trust:.1f}/100 {trust_icon}")
            print(f"   Status: {'VERIFIED' if verified else 'NEEDS REVIEW'}")
        else:
            print(f"❌ No detailed explanation generated")
        
        print()
    
    # Summary Statistics
    print("=" * 80)
    print("📊 AGENT 4 STATISTICS")
    print("=" * 80)
    print()
    
    trust_scores = [r.get('trust_score', 0) for r in top_3 if r.get('trust_score')]
    
    if trust_scores:
        verified_count = sum(1 for r in top_3 if r.get('verified', False))
        
        print(f"Trust Scores:")
        print(f"  Highest: {max(trust_scores):.1f}/100")
        print(f"  Lowest:  {min(trust_scores):.1f}/100")
        print(f"  Average: {sum(trust_scores)/len(trust_scores):.1f}/100")
        print()
        print(f"Verification:")
        print(f"  Verified: {verified_count}/{len(top_3)}")
        print(f"  Success Rate: {(verified_count/len(top_3))*100:.0f}%")
    else:
        print("⚠️  No trust scores available (LLM not configured or fallback used)")
    
    print()
    print("=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)
    print()


def test_agent4_verification():
    """Test Agent 4 fact verification logic with mock data"""
    
    print("=" * 80)
    print("🧪 TEST 2: FACT VERIFICATION LOGIC")
    print("=" * 80)
    print()
    
    from agents.agent4_explainer import ExplainerAgent
    
    agent = ExplainerAgent()
    
    # Test Case 1: Correct explanation
    print("Test Case 1: Correct Facts")
    print("-" * 80)
    
    context = {
        'product_name': 'Gaming Laptop RTX 3060',
        'product_price': 1499.99,
        'product_rating': 4.7,
        'product_reviews': 290,
        'can_afford_cash': True,
        'can_afford_financing': True,
        'risk_level': 'SAFE',
        'monthly_income': 6000.0,
        'final_score': 85.0
    }
    
    correct_explanation = """This Gaming Laptop RTX 3060 at $1499.99 is an excellent choice 
for your needs. With a 4.7/5 rating from 290 reviews, it's highly regarded. Your monthly 
income of $6000 makes this well within your budget, and the risk level is SAFE."""
    
    trust = agent._verify_explanation(correct_explanation, context)
    print(f"Explanation: {correct_explanation[:100]}...")
    print(f"Trust Score: {trust:.1f}/100")
    print(f"Status: {'✅ PASS' if trust >= 70 else '❌ FAIL'}")
    print()
    
    # Test Case 2: Wrong price
    print("Test Case 2: Incorrect Price")
    print("-" * 80)
    
    wrong_price_explanation = """This Gaming Laptop RTX 3060 at $999.99 is a great deal. 
With a 4.7/5 rating, it's highly regarded and well within your budget."""
    
    trust = agent._verify_explanation(wrong_price_explanation, context)
    print(f"Explanation: {wrong_price_explanation[:100]}...")
    print(f"Trust Score: {trust:.1f}/100")
    print(f"Status: {'⚠️ LOW TRUST' if trust < 70 else '✅ OK'}")
    print(f"Expected: Lower score due to wrong price ($999.99 vs $1499.99)")
    print()
    
    # Test Case 3: Contradictory affordability claim
    print("Test Case 3: Contradictory Affordability")
    print("-" * 80)
    
    context_unaffordable = {
        'product_name': 'Premium Laptop',
        'product_price': 2999.99,
        'product_rating': 4.8,
        'product_reviews': 150,
        'can_afford_cash': False,
        'can_afford_financing': False,
        'risk_level': 'RISKY',
        'monthly_income': 3000.0,
        'final_score': 45.0
    }
    
    contradictory_explanation = """This Premium Laptop is easily affordable and a safe choice 
for your budget. At $2999.99, it's well within your means."""
    
    trust = agent._verify_explanation(contradictory_explanation, context_unaffordable)
    print(f"Explanation: {contradictory_explanation[:100]}...")
    print(f"Trust Score: {trust:.1f}/100")
    print(f"Status: {'⚠️ LOW TRUST' if trust < 70 else '❌ UNEXPECTED'}")
    print(f"Expected: Lower score due to false affordability claims")
    print()
    
    # Test Case 4: Number extraction
    print("Test Case 4: Number Extraction")
    print("-" * 80)
    
    text_with_numbers = """The laptop costs $1,499.99 and has 4.7 stars. 
Your income is $6000 per month, giving you a 85/100 match score."""
    
    numbers = agent._extract_numbers(text_with_numbers)
    print(f"Text: {text_with_numbers}")
    print(f"Extracted numbers: {numbers}")
    print(f"Expected: [1499.99, 4.7, 6000, 85]")
    print(f"Status: {'✅ PASS' if len(numbers) >= 4 else '❌ FAIL'}")
    print()
    
    print("=" * 80)
    print("✅ VERIFICATION TESTS COMPLETE")
    print("=" * 80)
    print()


if __name__ == "__main__":
    try:
        # Run full pipeline test
        test_agent4_full_pipeline()
        
        # Run verification logic test
        test_agent4_verification()
        
        print()
        print("=" * 80)
        print("✨ ALL TESTS COMPLETED")
        print("=" * 80)
        print()
        print("Agent 4 Features Tested:")
        print("   ✅ Full pipeline integration (Agents 1 → 2 → 3 → 4)")
        print("   ✅ Context gathering from previous agents")
        print("   ✅ LLM explanation generation (if API key configured)")
        print("   ✅ Fact verification with regex")
        print("   ✅ Trust scoring (0-100)")
        print("   ✅ Fallback to template explanations")
        print("   ✅ Number extraction from text")
        print("   ✅ Price verification")
        print("   ✅ Affordability claim verification")
        
    except Exception as e:
        print(f"❌ Test failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
