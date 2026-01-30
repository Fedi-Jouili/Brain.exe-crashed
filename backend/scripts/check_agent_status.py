"""
Comprehensive Agent Status Check: Verify Agents 2, 2.5, and 3 are working
"""
import sys
import logging
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from agents.agent2_financial import financial_analyzer_agent
from agents.agent2_5_pathfinder import budget_pathfinder_agent
from agents.agent3_recommender import smart_recommender_agent
from models.schemas import UserProfile, Product
from models.state import AgentState

logging.basicConfig(level=logging.WARNING)

print("=" * 80)
print("🔍 AGENT STATUS CHECK: Agents 2, 2.5, 3")
print("=" * 80)
print()

# Test User
user = UserProfile(
    user_id="test_status_check",
    monthly_income=4000.0,
    monthly_expenses=3200.0,
    savings=5000.0,
    current_debt=3000.0,
    credit_score=680
)

# Test Products (varying price points)
products = [
    Product(
        product_id="P1", name="Budget Laptop", price=299.99, category="laptop",
        rating=4.0, num_reviews=200, in_stock=True, financing_available=False,
        cluster_id=0, description="Budget laptop"
    ),
    Product(
        product_id="P2", name="Mid-Range Laptop", price=699.99, category="laptop",
        rating=4.5, num_reviews=350, in_stock=True, financing_available=True,
        cluster_id=1, description="Mid-range laptop"
    ),
    Product(
        product_id="P3", name="Premium Laptop", price=1499.99, category="laptop",
        rating=4.8, num_reviews=280, in_stock=True, financing_available=True,
        cluster_id=2, description="Premium laptop"
    ),
    Product(
        product_id="P4", name="High-End Tablet", price=899.99, category="tablet",
        rating=4.6, num_reviews=420, in_stock=True, financing_available=True,
        cluster_id=3, description="High-end tablet"
    ),
]

print("✨ AGENT 2: FINANCIAL ANALYZER")
print("-" * 80)

state = AgentState(
    query="I need a laptop",
    user_profile=user,
    candidate_products=products,
    recommendations=[]
)

try:
    state = financial_analyzer_agent.execute(state)
    
    affordable_count = len(state.get('affordable_products', []))
    unaffordable_count = len(state.get('unaffordable_products', []))
    all_unaffordable = state.get('all_unaffordable', False)
    
    print(f"✅ Agent 2 Executed Successfully")
    print(f"   Affordable Products: {affordable_count}")
    print(f"   Unaffordable Products: {unaffordable_count}")
    print(f"   All Unaffordable: {all_unaffordable}")
    
    if affordable_count > 0:
        sample = state['affordable_products'][0]
        print(f"\n   Sample Affordable Product:")
        print(f"      {sample['product'].name} (${sample['product'].price:.2f})")
        print(f"      Financial Score: {sample.get('financial_score', 'N/A')}")
        print(f"      Risk: {sample['affordability'].get('risk_level', 'N/A')}")
    
    print()
    
except Exception as e:
    print(f"❌ Agent 2 Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("✨ AGENT 2.5: BUDGET PATHFINDER")
print("-" * 80)

# Test scenario where all products are unaffordable
state_unaffordable = AgentState(
    query="I need a premium laptop",
    user_profile=user,
    candidate_products=products,
    affordable_products=[],
    unaffordable_products=[
        {'product': p, 'affordability': {'risk_level': 'RISKY'}, 'financial_score': 30}
        for p in products
    ],
    all_unaffordable=True,
    recommendations=[]
)

try:
    state_unaffordable = budget_pathfinder_agent.execute(state_unaffordable)
    
    paths = state_unaffordable.get('alternative_paths', [])
    print(f"✅ Agent 2.5 Executed Successfully")
    print(f"   Alternative Paths Found: {len(paths)}")
    
    if paths:
        print(f"\n   Path Types Generated:")
        path_types = set()
        for path in paths:
            path_types.add(path.get('path_type', 'unknown'))
        
        for ptype in sorted(path_types):
            count = sum(1 for p in paths if p.get('path_type') == ptype)
            print(f"      • {ptype.replace('_', ' ').title()}: {count}")
        
        # Show sample path
        sample_path = paths[0]
        print(f"\n   Sample Path:")
        print(f"      Type: {sample_path.get('path_type', 'N/A').replace('_', ' ').title()}")
        print(f"      Viability: {sample_path.get('viability_score', 0):.0f}%")
        print(f"      Timeline: {sample_path.get('timeline_months', 0)} months")
    
    print()
    
except Exception as e:
    print(f"❌ Agent 2.5 Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("✨ AGENT 3: SMART RECOMMENDER")
print("-" * 80)

# Use state with affordable products for Agent 3
state['recommendations'] = []

try:
    state = smart_recommender_agent.execute(state)
    
    recommendations = state.get('recommendations', [])
    print(f"✅ Agent 3 Executed Successfully")
    print(f"   Recommendations Generated: {len(recommendations)}")
    
    if recommendations:
        print(f"\n   Score Distribution:")
        
        top_rec = recommendations[0]
        print(f"      Highest: {top_rec['final_score']:.1f}")
        
        bottom_rec = recommendations[-1]
        print(f"      Lowest: {bottom_rec['final_score']:.1f}")
        
        avg_score = sum(r['final_score'] for r in recommendations) / len(recommendations)
        print(f"      Average: {avg_score:.1f}")
        
        # Diversity check
        clusters = [r['product'].cluster_id for r in recommendations[:10]]
        unique_clusters = len(set(clusters))
        print(f"\n   Diversity Metrics:")
        print(f"      Unique Clusters: {unique_clusters}/{len(clusters)}")
        print(f"      Diversity Score: {(unique_clusters/max(1, len(clusters)))*100:.0f}%")
        
        print(f"\n   Top Recommendation:")
        top = recommendations[0]
        print(f"      {top['product'].name}")
        print(f"      Final Score: {top['final_score']:.1f}/100")
        print(f"      Explanation: {top['explanation'][:60]}...")
    
    print()
    
except Exception as e:
    print(f"❌ Agent 3 Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 80)
print("✅ ALL AGENTS OPERATIONAL")
print("=" * 80)
print()
print("Status Summary:")
print("  ✅ Agent 2 (Financial Analyzer) - WORKING")
print("  ✅ Agent 2.5 (Budget Pathfinder) - WORKING")
print("  ✅ Agent 3 (Smart Recommender) - WORKING")
print()
print("Next Steps:")
print("  1. Build Agent 4 (Explainer with LLM)")
print("  2. Create LangGraph orchestration")
print("  3. Implement routing logic (FAST/SMART/DEEP)")
print("  4. Build FastAPI backend")
print("  5. Build Streamlit frontend")
print()
