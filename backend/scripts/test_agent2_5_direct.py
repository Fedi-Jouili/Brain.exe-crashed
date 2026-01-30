"""
Direct test of Agent 2.5 with manually crafted scenario
"""
import sys
import logging
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from agents.agent2_5_pathfinder import budget_pathfinder_agent
from models.schemas import UserProfile, Product
from models.state import AgentState

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')


def test_agent2_5_direct():
    """Test Agent 2.5 with manually created unaffordable scenario"""
    
    print("=" * 70)
    print("🧪 DIRECT TEST: AGENT 2.5 BUDGET PATHFINDER")
    print("=" * 70)
    print()
    
    # Create a very low income user
    low_income_user = UserProfile(
        user_id="test_low",
        monthly_income=2000.0,
        monthly_expenses=1800.0,
        savings=1500.0,
        current_debt=1000.0,
        credit_score=620
    )
    
    # Create expensive products that are unaffordable
    expensive_products = [
        Product(
            product_id="PROD_EXPENSIVE_1",
            name="High-End Gaming Laptop",
            description="Top tier gaming machine",
            price=1899.99,
            category="laptop",
            rating=4.8,
            num_reviews=150,
            in_stock=True,
            financing_available=True,
            financing_terms="12 months, 9.9% APR",
            cluster_id=5,
            image_url="",
            embedding=[0.1] * 512
        ),
        Product(
            product_id="PROD_EXPENSIVE_2",
            name="Professional Workstation",
            description="Enterprise grade workstation",
            price=2499.99,
            category="laptop",
            rating=4.9,
            num_reviews=89,
            in_stock=True,
            financing_available=True,
            financing_terms="12 months, 8.9% APR",
            cluster_id=5,
            image_url="",
            embedding=[0.1] * 512
        ),
        Product(
            product_id="PROD_CHEAPER",
            name="Budget Student Laptop",
            description="Entry level laptop",
            price=599.99,
            category="laptop",
            rating=4.2,
            num_reviews=300,
            in_stock=True,
            financing_available=False,
            financing_terms=None,
            cluster_id=5,
            image_url="",
            embedding=[0.1] * 512
        )
    ]
    
    # Create state with all_unaffordable = True
    state = AgentState(
        query="gaming laptop",
        user_profile=low_income_user,
        candidate_products=expensive_products,
        affordable_products=[],
        all_unaffordable=True,  # Trigger Agent 2.5
        recommendations=[],
        path_taken="DEEP"
    )
    
    print(f"User Profile:")
    print(f"  Monthly Income: ${low_income_user.monthly_income:.2f}")
    print(f"  Monthly Expenses: ${low_income_user.monthly_expenses:.2f}")
    print(f"  Disposable Income: ${low_income_user.monthly_income - low_income_user.monthly_expenses:.2f}")
    print(f"  Savings: ${low_income_user.savings:.2f}")
    print(f"  Debt: ${low_income_user.current_debt:.2f}")
    print(f"  Credit Score: {low_income_user.credit_score}")
    print()
    
    print(f"Candidate Products (All Unaffordable):")
    for p in expensive_products:
        print(f"  - {p.name}: ${p.price:.2f}")
    print()
    
    # Run Agent 2.5
    print("Running Agent 2.5 (Budget Pathfinder)...")
    state = budget_pathfinder_agent.execute(state)
    
    print(f"\n✅ Agent 2.5 Complete:")
    print(f"   Execution time: {state.get('agent2_5_execution_time', 0):.0f}ms")
    print(f"   Alternative paths found: {len(state.get('alternative_paths', []))}")
    print(f"   All still unaffordable: {state.get('all_unaffordable', True)}")
    print()
    
    # Display results
    if state.get('alternative_paths'):
        print("💡 ALTERNATIVE PATHS GENERATED:")
        print("=" * 70)
        
        for i, path in enumerate(state['alternative_paths'], 1):
            print(f"\n{i}. [{path['type'].upper()}] {path['difficulty'].upper()}")
            print(f"   {path['description']}")
            print(f"   Viability Score: {path['viability_score']:.1f}/100")
            print(f"   Affordable: {'✅ YES' if path['is_affordable'] else '❌ Not yet'}")
            
            if path['type'] == 'savings_plan':
                print(f"\n   📊 Savings Plan Details:")
                print(f"      Target: {path['product_name']} (${path['price']:.2f})")
                print(f"      Timeline: {path['timeline_months']} months")
                print(f"      Monthly Savings Required: ${path['monthly_savings_required']:.2f}")
                print(f"      Total to Save: ${path['total_saved']:.2f}")
                
            elif path['type'] == 'extended_financing':
                print(f"\n   💳 Extended Financing Details:")
                print(f"      Product: {path['product_name']} (${path['price']:.2f})")
                print(f"      Timeline: {path['timeline_months']} months")
                print(f"      Monthly Payment: ${path['monthly_payment']:.2f}")
                print(f"      APR: {path['apr']:.1f}%")
                print(f"      Total Cost: ${path['total_cost']:.2f}")
                print(f"      Extra Cost (Interest): ${path['total_cost'] - path['price']:.2f}")
                
            elif path['type'] == 'cluster_alternative':
                print(f"\n   🔄 Cheaper Alternative:")
                print(f"      Original: {path['original_product']} (${path['original_price']:.2f})")
                print(f"      Alternative: {path['product_name']} (${path['price']:.2f})")
                print(f"      💰 Savings: ${path['savings_amount']:.2f} ({path['savings_percent']:.0f}%)")
    else:
        print("❌ No alternative paths generated")
    
    # Check if affordable alternatives were found
    print()
    print("=" * 70)
    if state.get('affordable_products'):
        print(f"✅ Found {len(state['affordable_products'])} affordable alternatives!")
        print("   Pipeline can continue to Agent 3")
        for item in state['affordable_products']:
            prod = item['product']
            print(f"   - {prod['name']}: ${prod['price']:.2f}")
    else:
        print("⚠️  No immediately affordable alternatives")
        print("   User can choose from aspirational paths above")
    
    print("=" * 70)


if __name__ == "__main__":
    test_agent2_5_direct()
