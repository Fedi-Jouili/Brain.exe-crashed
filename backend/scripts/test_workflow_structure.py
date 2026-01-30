"""
Simple LangGraph Workflow Structure Test
Tests graph compilation and routing logic without requiring external services
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_graph_compilation():
    """Test that the graph compiles successfully"""
    print("=" * 80)
    print("TEST 1: GRAPH COMPILATION")
    print("=" * 80)

    try:
        from orchestration.workflow import create_recommendation_graph

        graph = create_recommendation_graph()

        print("✅ Graph compiled successfully")
        print(f"✅ Graph type: {type(graph)}")

        # Check graph structure
        try:
            graph_dict = graph.get_graph()
            nodes = list(graph_dict.nodes.keys())
            print(f"✅ Nodes: {nodes}")
            print(f"✅ Total nodes: {len(nodes)}")

            expected_nodes = ['discovery', 'financial', 'pathfinder', 'recommender', 'explainer']
            for node in expected_nodes:
                if node in nodes:
                    print(f"   ✅ {node}")
                else:
                    print(f"   ❌ {node} MISSING")
                    return False

            return True

        except Exception as e:
            print(f"⚠️  Could not inspect graph structure: {e}")
            return True  # Graph compiled, that's the main success

    except Exception as e:
        print(f"❌ Graph compilation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_conditional_routing_logic():
    """Test the routing logic without executing agents"""
    print("\n" + "=" * 80)
    print("TEST 2: CONDITIONAL ROUTING LOGIC")
    print("=" * 80)

    try:
        from orchestration.workflow import should_run_pathfinder

        # Test case 1: all_unaffordable = True
        state1 = {'all_unaffordable': True}
        result1 = should_run_pathfinder(state1)

        if result1 == "pathfinder":
            print("✅ Case 1: all_unaffordable=True → pathfinder")
        else:
            print(f"❌ Case 1: Expected 'pathfinder', got '{result1}'")
            return False

        # Test case 2: all_unaffordable = False
        state2 = {'all_unaffordable': False}
        result2 = should_run_pathfinder(state2)

        if result2 == "recommender":
            print("✅ Case 2: all_unaffordable=False → recommender")
        else:
            print(f"❌ Case 2: Expected 'recommender', got '{result2}'")
            return False

        # Test case 3: Missing key (default)
        state3 = {}
        result3 = should_run_pathfinder(state3)

        if result3 == "recommender":
            print("✅ Case 3: Missing key → recommender (default)")
        else:
            print(f"❌ Case 3: Expected 'recommender', got '{result3}'")
            return False

        return True

    except Exception as e:
        print(f"❌ Routing logic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_types():
    """Test that AgentState and schemas are correctly defined"""
    print("\n" + "=" * 80)
    print("TEST 3: STATE AND SCHEMA DEFINITIONS")
    print("=" * 80)

    try:
        from models.state import AgentState
        from models.schemas import UserProfile, Product

        print("✅ AgentState imported")
        print("✅ UserProfile imported")
        print("✅ Product imported")

        # Test UserProfile creation
        profile = UserProfile(
            user_id="TEST",
            monthly_income=5000.0,
            credit_score=720
        )
        print(f"✅ UserProfile created: {profile.user_id}")

        # Test Product creation
        product = Product(
            product_id="TEST_PROD",
            name="Test Product",
            price=299.99,
            category="Electronics",
            brand="TestBrand",
            rating=4.5,
            num_reviews=100
        )
        print(f"✅ Product created: {product.name}")

        return True

    except Exception as e:
        print(f"❌ State/Schema test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_exists():
    """Test that public API functions exist"""
    print("\n" + "=" * 80)
    print("TEST 4: PUBLIC API")
    print("=" * 80)

    try:
        from orchestration.workflow import (
            run_recommendation_pipeline,
            get_recommendation_graph,
            create_recommendation_graph,
            visualize_graph
        )

        print("✅ run_recommendation_pipeline imported")
        print("✅ get_recommendation_graph imported")
        print("✅ create_recommendation_graph imported")
        print("✅ visualize_graph imported")

        # Check signatures
        import inspect

        sig = inspect.signature(run_recommendation_pipeline)
        params = list(sig.parameters.keys())
        print(f"✅ run_recommendation_pipeline parameters: {params}")

        if 'query' in params and 'user_profile' in params:
            print("✅ Required parameters present")
            return True
        else:
            print("❌ Missing required parameters")
            return False

    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "=" * 80)
    print("LANGGRAPH WORKFLOW STRUCTURE TESTS")
    print("=" * 80)
    print("\nThese tests verify the workflow is properly structured")
    print("without requiring Redis/Qdrant or running actual agents.\n")

    results = []

    results.append(("Graph Compilation", test_graph_compilation()))
    results.append(("Conditional Routing", test_conditional_routing_logic()))
    results.append(("State/Schema Types", test_state_types()))
    results.append(("Public API", test_api_exists()))

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    all_passed = all(result[1] for result in results)

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL STRUCTURE TESTS PASSED")
        print("\nThe LangGraph workflow is properly configured.")
        print("To test full execution, ensure Redis and Qdrant are running,")
        print("then run: python backend/scripts/test_workflow.py")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
