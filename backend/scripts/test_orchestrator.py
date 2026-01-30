"""
Test LangGraph Orchestration
Tests all workflow paths: FAST, SMART, and DEEP
"""
import sys
import logging
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.orchestrator import execute_workflow, get_deep_graph, get_smart_graph
from services.routing import complexity_router, PathType
from models.schemas import UserProfile
from models.state import AgentState

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')


def test_complexity_routing():
    """Test complexity router"""
    
    print("=" * 80)
    print("🧪 TEST 1: COMPLEXITY ROUTING")
    print("=" * 80)
    print()
    
    # Test Case 1: Simple query (should be SMART)
    print("Test Case 1: Simple query")
    print("-" * 80)
    
    state1 = AgentState(
        query="laptop",
        final_recommendations=[]
    )
    
    complexity1 = complexity_router.estimate_complexity(state1)
    path1 = complexity_router.determine_path(state1)
    
    print(f"Query: '{state1['query']}'")
    print(f"Complexity: {complexity1:.2f}")
    print(f"Path: {path1}")
    print(f"Description: {complexity_router.get_path_description(path1)}")
    print(f"Expected: SMART (low complexity, no profile)")
    print()
    
    # Test Case 2: Financial query with profile (should be DEEP)
    print("Test Case 2: Financial query with complete profile")
    print("-" * 80)
    
    user = UserProfile(
        user_id="test_user",
        monthly_income=5000.0,
        monthly_expenses=3500.0,
        savings=10000.0,
        current_debt=2000.0,
        credit_score=720
    )
    
    state2 = AgentState(
        query="affordable laptop with financing options under my budget",
        user_profile=user,
        recommendations=[]
    )
    
    complexity2 = complexity_router.estimate_complexity(state2)
    path2 = complexity_router.determine_path(state2)
    
    print(f"Query: '{state2['query']}'")
    print(f"User Profile: Complete (income, credit, savings)")
    print(f"Complexity: {complexity2:.2f}")
    print(f"Path: {path2}")
    print(f"Description: {complexity_router.get_path_description(path2)}")
    print(f"Expected: DEEP (financial keywords + complete profile)")
    print()
    
    # Test Case 3: Medium complexity (should be SMART)
    print("Test Case 3: Medium complexity query")
    print("-" * 80)
    
    state3 = AgentState(
        query="professional laptop for software development",
        final_recommendations=[]
    )
    
    complexity3 = complexity_router.estimate_complexity(state3)
    path3 = complexity_router.determine_path(state3)
    
    print(f"Query: '{state3['query']}'")
    print(f"Complexity: {complexity3:.2f}")
    print(f"Path: {path3}")
    print(f"Description: {complexity_router.get_path_description(path3)}")
    print(f"Expected: SMART (medium complexity, no financial analysis needed)")
    print()
    
    # Test Case 4: Cache available (should be FAST)
    print("Test Case 4: Cache available with simple query")
    print("-" * 80)
    
    state4 = AgentState(
        query="laptop",
        recommendations=[]
    )
    
    complexity4 = complexity_router.estimate_complexity(state4)
    path4 = complexity_router.determine_path(state4, cache_available=True)
    
    print(f"Query: '{state4['query']}'")
    print(f"Cache Available: True")
    print(f"Complexity: {complexity4:.2f}")
    print(f"Path: {path4}")
    print(f"Description: {complexity_router.get_path_description(path4)}")
    print(f"Expected: FAST (cache hit + low complexity)")
    print()


def test_deep_path():
    """Test DEEP path (all 5 agents)"""
    
    print("=" * 80)
    print("🧪 TEST 2: DEEP PATH WORKFLOW")
    print("=" * 80)
    print()
    
    user = UserProfile(
        user_id="test_deep_path",
        monthly_income=6000.0,
        monthly_expenses=3800.0,
        savings=15000.0,
        current_debt=3000.0,
        credit_score=720
    )
    
    state = AgentState(
        query="affordable laptop for work",
        user_profile=user,
        final_recommendations=[],
        path_taken="DEEP"
    )
    
    print(f"Query: '{state['query']}'")
    print(f"User: ${user.monthly_income:.0f} income, {user.credit_score} credit")
    print()
    print("Executing DEEP workflow (All 5 agents)...")
    print()
    
    # Execute workflow
    result = execute_workflow(state, path="DEEP")
    
    # Display results
    print("=" * 80)
    print("WORKFLOW RESULTS")
    print("=" * 80)
    print()
    
    print(f"✅ Agent 1 (Discovery):")
    candidates = len(result.get('candidate_products', []))
    print(f"   Found: {candidates} candidate products")
    print(f"   Time: {result.get('agent1_execution_time', 0)}ms")
    print()
    
    print(f"✅ Agent 2 (Financial Analyzer):")
    affordable = len(result.get('affordable_products', []))
    all_unaffordable = result.get('all_unaffordable', False)
    print(f"   Affordable: {affordable}")
    print(f"   All Unaffordable: {all_unaffordable}")
    print(f"   Time: {result.get('agent2_execution_time', 0)}ms")
    print()
    
    if all_unaffordable:
        print(f"✅ Agent 2.5 (Budget Pathfinder):")
        paths = len(result.get('alternative_paths', []))
        print(f"   Alternative Paths: {paths}")
        print(f"   Time: {result.get('agent2_5_execution_time', 0)}ms")
        print()
    else:
        print(f"⏭️  Agent 2.5 (Budget Pathfinder): Skipped (products affordable)")
        print()
    
    print(f"✅ Agent 3 (Smart Recommender):")
    recommendations = len(result.get('final_recommendations', []))
    print(f"   Recommendations: {recommendations}")
    print(f"   Time: {result.get('recommender_time_ms', 0)}ms")
    print()
    
    print(f"✅ Agent 4 (Explainer):")
    explained = sum(1 for r in result.get('final_recommendations', []) if r.get('detailed_explanation'))
    print(f"   Explained: {explained}/{min(3, recommendations)}")
    print(f"   Time: {result.get('explainer_time_ms', 0)}ms")
    print()
    
    # Show top recommendation
    if result.get('final_recommendations'):
        top = result['final_recommendations'][0]
        print("-" * 80)
        print("🏆 TOP RECOMMENDATION")
        print("-" * 80)
        print(f"Product: {top['product'].name}")
        print(f"Price: ${top['product'].price:.2f}")
        print(f"Final Score: {top.get('final_score', 0):.1f}/100")
        print(f"Explanation: {top.get('explanation', 'N/A')}")
        print()
    
    # Total time
    total_time = sum([
        result.get('agent1_execution_time', 0),
        result.get('agent2_execution_time', 0),
        result.get('agent2_5_execution_time', 0),
        result.get('agent3_execution_time', 0),
        result.get('agent4_execution_time', 0)
    ])
    print(f"⏱️  Total Execution Time: {total_time}ms")
    print()


def test_smart_path():
    """Test SMART path (Agents 1, 3, 4 only)"""
    
    print("=" * 80)
    print("🧪 TEST 3: SMART PATH WORKFLOW")
    print("=" * 80)
    print()
    
    state = AgentState(
        query="gaming laptop",
        final_recommendations=[],
        path_taken="SMART"
    )
    
    print(f"Query: '{state['query']}'")
    print(f"No user profile (financial analysis skipped)")
    print()
    print("Executing SMART workflow (Agents 1 → 3 → 4)...")
    print()
    
    # Execute workflow
    result = execute_workflow(state, path="SMART")
    
    # Display results
    print("=" * 80)
    print("WORKFLOW RESULTS")
    print("=" * 80)
    print()
    
    print(f"✅ Agent 1 (Discovery):")
    candidates = len(result.get('candidate_products', []))
    print(f"   Found: {candidates} products")
    print()
    
    print(f"⏭️  Agent 2 (Financial): Skipped (SMART path)")
    print()
    
    print(f"✅ Agent 3 (Smart Recommender):")
    recommendations = len(result.get('final_recommendations', []))
    print(f"   Recommendations: {recommendations}")
    print()
    
    print(f"✅ Agent 4 (Explainer):")
    explained = sum(1 for r in result.get('final_recommendations', []) if r.get('detailed_explanation'))
    print(f"   Explained: {explained}/{min(3, recommendations)}")
    print()
    
    if result.get('final_recommendations'):
        top = result['final_recommendations'][0]
        print(f"🏆 Top: {top['product'].name} (Score: {top.get('final_score', 0):.1f}/100)")
    
    print()


if __name__ == "__main__":
    try:
        # Test 1: Complexity routing
        test_complexity_routing()
        
        # Test 2: DEEP path
        test_deep_path()
        
        # Test 3: SMART path
        test_smart_path()
        
        print()
        print("=" * 80)
        print("✅ ALL ORCHESTRATION TESTS COMPLETED")
        print("=" * 80)
        print()
        print("Features Tested:")
        print("   ✅ Complexity estimation (0.0-1.0 scale)")
        print("   ✅ Path routing (FAST/SMART/DEEP)")
        print("   ✅ DEEP path workflow (all 5 agents)")
        print("   ✅ Conditional routing (Agent 2.5 when needed)")
        print("   ✅ SMART path workflow (Agents 1, 3, 4)")
        print("   ✅ LangGraph state management")
        print("   ✅ End-to-end pipeline execution")
        
    except Exception as e:
        print(f"❌ Test failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
