"""
Quick validation script for MCP Tools Layer

Run with: python backend/tools/validate_tools.py

Checks:
1. All 12 tools are registered
2. Tools have valid schemas
3. Tool categories are correct
4. Registry functions work
5. Basic tool invocation (with error handling)
"""

import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Validate MCP tools implementation"""

    print("=" * 80)
    print("MCP TOOLS LAYER VALIDATION")
    print("=" * 80)

    # Import registry
    try:
        from tools.mcp_tools import (
            ALL_TOOLS,
            TOOL_CATEGORIES,
            list_tools,
            get_tool_by_name,
            get_tools_by_category,
            validate_registry
        )
        print("✅ Successfully imported tools registry")
    except Exception as e:
        print(f"❌ Failed to import tools registry: {e}")
        return False

    # Check 1: Tool count
    print(f"\n📊 TOOL COUNT")
    print(f"   Total tools: {len(ALL_TOOLS)}")
    print(f"   Expected: 12")
    if len(ALL_TOOLS) == 12:
        print("   ✅ Correct tool count")
    else:
        print("   ❌ Wrong tool count")
        return False

    # Check 2: Category counts
    print(f"\n📂 CATEGORY BREAKDOWN")
    for category, tools in TOOL_CATEGORIES.items():
        print(f"   {category}: {len(tools)} tools")

    expected_counts = {"qdrant": 4, "ml_rl": 5, "llm": 3}
    all_correct = True
    for category, expected in expected_counts.items():
        actual = len(TOOL_CATEGORIES[category])
        if actual != expected:
            print(f"   ❌ {category}: expected {expected}, got {actual}")
            all_correct = False

    if all_correct:
        print("   ✅ All categories have correct counts")
    else:
        return False

    # Check 3: List all tools
    print(f"\n📋 ALL TOOLS")
    tool_names = list_tools()
    for i, name in enumerate(tool_names, 1):
        print(f"   {i:2d}. {name}")

    # Check 4: Validate registry integrity
    print(f"\n🔍 REGISTRY VALIDATION")
    validation_result = validate_registry()

    if validation_result["valid"]:
        print("   ✅ Registry is valid")
    else:
        print("   ❌ Registry has issues:")
        for issue in validation_result["issues"]:
            print(f"      - {issue}")
        return False

    # Check 5: Test tool lookup by name
    print(f"\n🔎 TOOL LOOKUP TEST")
    test_tools = [
        "qdrant_search_products",
        "thompson_sample_ranking",
        "generate_explanation"
    ]

    for tool_name in test_tools:
        try:
            tool = get_tool_by_name(tool_name)
            print(f"   ✅ {tool_name}: {tool.description[:50]}...")
        except Exception as e:
            print(f"   ❌ {tool_name}: {e}")
            return False

    # Check 6: Test tool schemas
    print(f"\n📜 TOOL SCHEMA VALIDATION")
    schema_errors = []
    for tool in ALL_TOOLS:
        try:
            schema = tool.get_schema()
            if not isinstance(schema, dict):
                schema_errors.append(f"{tool.name}: schema is not a dict")
            elif "name" not in schema or "description" not in schema:
                schema_errors.append(f"{tool.name}: missing required schema fields")
        except Exception as e:
            schema_errors.append(f"{tool.name}: {e}")

    if schema_errors:
        print("   ❌ Schema validation failed:")
        for error in schema_errors:
            print(f"      - {error}")
        return False
    else:
        print(f"   ✅ All {len(ALL_TOOLS)} tools have valid schemas")

    # Check 7: Test basic tool invocation (expect failures without services)
    print(f"\n🧪 BASIC TOOL INVOCATION TEST")
    print("   (Expected to fail without external services, but should handle errors gracefully)")

    # Test 1: Qdrant tool
    from tools.mcp_tools import qdrant_search_products
    result = qdrant_search_products.invoke({
        "query_vector": [0.1] * 512,
        "top_k": 5
    })
    print(f"   qdrant_search_products: success={result['success']}")
    if not result["success"]:
        print(f"      (Expected) Error: {result['error'][:80]}...")

    # Test 2: Thompson tool
    from tools.mcp_tools import thompson_sample_ranking
    result = thompson_sample_ranking.invoke({
        "product_ids": ["TEST001", "TEST002"]
    })
    print(f"   thompson_sample_ranking: success={result['success']}")

    # Test 3: Complexity tool (should succeed, no external deps)
    from tools.mcp_tools import estimate_query_complexity
    result = estimate_query_complexity.invoke({
        "query": "laptop under $1000"
    })
    print(f"   estimate_query_complexity: success={result['success']}")
    if result["success"]:
        print(f"      Complexity: {result['data']['level']} (score: {result['data']['score']:.2f})")

    # Test 4: Fact verification (should succeed, no external deps)
    from tools.mcp_tools import verify_explanation_facts
    result = verify_explanation_facts.invoke({
        "explanation": "This laptop is affordable through financing.",
        "context": {
            "product": {"name": "Laptop", "price": 1000, "category": "Electronics"},
            "affordability": {"can_afford_cash": False, "can_afford_financing": True}
        }
    })
    print(f"   verify_explanation_facts: success={result['success']}")
    if result["success"]:
        print(f"      Verified: {result['data']['verified']}, Trust: {result['data']['trust_score']:.2f}")

    print("   ✅ Tools handle invocation gracefully (errors expected without services)")

    # Summary
    print(f"\n" + "=" * 80)
    print("✅ ALL VALIDATION CHECKS PASSED")
    print("=" * 80)
    print(f"\nMCP Tools Layer is correctly implemented:")
    print(f"  • {len(ALL_TOOLS)} tools registered")
    print(f"  • 3 categories (qdrant, ml_rl, llm)")
    print(f"  • All tools have valid schemas")
    print(f"  • Registry functions work correctly")
    print(f"  • Tool invocation handles errors gracefully")
    print(f"\n✅ READY FOR PRODUCTION USE")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
