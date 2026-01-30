"""
Test script for Agent 2: Financial Analyzer
"""
import sys
import logging
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from agents.agent1_discovery import product_discovery_agent
from agents.agent2_financial import financial_analyzer_agent
from models.schemas import UserProfile
from models.state import AgentState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


def test_agent2():
    """Test Agent 2 with different financial profiles"""
    
    print("=" * 70)
    print("🧪 TESTING AGENT 2: FINANCIAL ANALYZER")
    print("=" * 70)
    print()
    
    # Test Case 1: Low income user
    print("📊 TEST 1: Low Income Profile")
    print("-" * 70)
    
    low_income_profile = UserProfile(
        user_id="test_user_low",
        monthly_income=2500.0,
        monthly_expenses=2200.0,
        savings=5000.0,
        current_debt=1000.0,
        credit_score=680
    )
    
    state = AgentState(
        query="budget laptop under $500",
        user_profile=low_income_profile,
        candidate_products=[],
        affordable_products=[],
        recommendations=[],
        path_taken="DEEP"
    )
    
    # Run Agent 1 first to get candidates
    print("Running Agent 1 (Discovery)...")
    state = product_discovery_agent.execute(state)
    print(f"✅ Found {len(state['candidate_products'])} candidate products")
    print()
    
    # Run Agent 2
    print("Running Agent 2 (Financial Analyzer)...")
    state = financial_analyzer_agent.execute(state)
    
    print(f"✅ Analysis complete:")
    print(f"   - Affordable products: {len(state['affordable_products'])}")
    print(f"   - All unaffordable: {state['all_unaffordable']}")
    print(f"   - Execution time: {state['agent2_execution_time']:.0f}ms")
    print()
    
    # Show top 3 affordable products
    if state['affordable_products']:
        print("Top 3 Affordable Products:")
        for i, item in enumerate(state['affordable_products'][:3], 1):
            product = item['product']
            affordability = item['affordability']
            score = item['financial_score']
            
            print(f"\n{i}. {product.name} - ${product.price:.2f}")
            print(f"   Financial Score: {score:.1f}/100")
            print(f"   Can afford cash: {affordability['can_afford_cash']}")
            print(f"   Can afford financing: {affordability['can_afford_financing']}")
            print(f"   Risk level: {affordability['risk_level']}")
            print(f"   Recommendation: {affordability['recommendation']}")
    else:
        print("❌ No affordable products found")
    
    print()
    print("=" * 70)
    print()
    
    # Test Case 2: Medium income user
    print("📊 TEST 2: Medium Income Profile")
    print("-" * 70)
    
    medium_income_profile = UserProfile(
        user_id="test_user_medium",
        monthly_income=5000.0,
        monthly_expenses=3500.0,
        savings=15000.0,
        current_debt=5000.0,
        credit_score=720
    )
    
    state = AgentState(
        query="laptop for work and gaming",
        user_profile=medium_income_profile,
        candidate_products=[],
        affordable_products=[],
        recommendations=[],
        path_taken="DEEP"
    )
    
    # Run Agent 1
    print("Running Agent 1 (Discovery)...")
    state = product_discovery_agent.execute(state)
    print(f"✅ Found {len(state['candidate_products'])} candidate products")
    print()
    
    # Run Agent 2
    print("Running Agent 2 (Financial Analyzer)...")
    state = financial_analyzer_agent.execute(state)
    
    print(f"✅ Analysis complete:")
    print(f"   - Affordable products: {len(state['affordable_products'])}")
    print(f"   - All unaffordable: {state['all_unaffordable']}")
    print(f"   - Execution time: {state['agent2_execution_time']:.0f}ms")
    print()
    
    # Show top 3 with details
    if state['affordable_products']:
        print("Top 3 Affordable Products:")
        for i, item in enumerate(state['affordable_products'][:3], 1):
            product = item['product']
            affordability = item['affordability']
            score = item['financial_score']
            
            print(f"\n{i}. {product.name} - ${product.price:.2f}")
            print(f"   Financial Score: {score:.1f}/100")
            
            if affordability['can_afford_cash']:
                cash = affordability['cash_metrics']
                print(f"   Cash Purchase:")
                print(f"     - Safe limit: ${cash.get('safe_cash_limit', 0):.2f}")
                print(f"     - Emergency fund after: ${cash.get('emergency_fund_after', 0):.2f}")
                print(f"     - Emergency months: {cash.get('emergency_fund_months', 0):.1f}")
            
            if affordability['can_afford_financing']:
                financing = affordability['financing_metrics']
                print(f"   Financing Option:")
                print(f"     - Monthly payment: ${financing.get('monthly_payment', 0):.2f}")
                print(f"     - PTI ratio: {financing.get('pti_ratio', 0)*100:.1f}%")
                print(f"     - DTI after: {financing.get('dti_after', 0)*100:.1f}%")
            
            print(f"   Risk: {affordability['risk_level']}")
    
    print()
    print("=" * 70)
    print()
    
    # Test Case 3: High income user looking at expensive product
    print("📊 TEST 3: High Income Profile (Expensive Product)")
    print("-" * 70)
    
    high_income_profile = UserProfile(
        user_id="test_user_high",
        monthly_income=10000.0,
        monthly_expenses=6000.0,
        savings=50000.0,
        current_debt=10000.0,
        credit_score=780
    )
    
    state = AgentState(
        query="professional workstation laptop",
        user_profile=high_income_profile,
        candidate_products=[],
        affordable_products=[],
        recommendations=[],
        path_taken="DEEP"
    )
    
    # Run Agent 1
    print("Running Agent 1 (Discovery)...")
    state = product_discovery_agent.execute(state)
    print(f"✅ Found {len(state['candidate_products'])} candidate products")
    print()
    
    # Run Agent 2
    print("Running Agent 2 (Financial Analyzer)...")
    state = financial_analyzer_agent.execute(state)
    
    print(f"✅ Analysis complete:")
    print(f"   - Affordable products: {len(state['affordable_products'])}")
    print(f"   - All unaffordable: {state['all_unaffordable']}")
    print(f"   - Execution time: {state['agent2_execution_time']:.0f}ms")
    print()
    
    # Show financial scores distribution
    if state['affordable_products']:
        scores = [item['financial_score'] for item in state['affordable_products']]
        print(f"Financial Score Distribution:")
        print(f"   - Highest: {max(scores):.1f}")
        print(f"   - Lowest: {min(scores):.1f}")
        print(f"   - Average: {sum(scores)/len(scores):.1f}")
        print()
        
        print("Top 3 by Financial Score:")
        for i, item in enumerate(state['affordable_products'][:3], 1):
            product = item['product']
            score = item['financial_score']
            print(f"   {i}. {product.name} - Score: {score:.1f}/100")
    
    print()
    print("=" * 70)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_agent2()
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
