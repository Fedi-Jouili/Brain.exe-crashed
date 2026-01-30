"""
MCP Tools Registry - Unified Tool Access Point

This module provides centralized access to all 12 MCP tools:

QDRANT TOOLS (4):
1. qdrant_search_products - Semantic product search
2. qdrant_retrieve_financial_rules - RAG retrieval
3. qdrant_find_similar_users - Collaborative filtering
4. cluster_alternatives - K-Means alternatives

ML/RL TOOLS (5):
5. calculate_affordability - Financial affordability analysis
6. thompson_sample_ranking - Thompson Sampling ranking
7. update_thompson_sampling - RL parameter updates
8. generate_creative_financing_paths - Financing options
9. estimate_query_complexity - Complexity routing

LLM TOOLS (3):
10. generate_explanation - Gemini 2.0 Flash explanations
11. verify_explanation_facts - Fact verification
12. evaluate_with_ragas - RAG quality evaluation

Usage:
    # Import all tools from registry
    from tools.mcp_tools import (
        qdrant_search_products,
        calculate_affordability,
        thompson_sample_ranking,
        generate_explanation
    )

    # Or import by category
    from tools.mcp_tools import get_tools_by_category
    qdrant_tools = get_tools_by_category("qdrant")

    # Or list all available tools
    from tools.mcp_tools import list_tools
    all_tool_names = list_tools()

    # Or get tool by name
    from tools.mcp_tools import get_tool_by_name
    tool = get_tool_by_name("qdrant_search_products")

Architecture:
    - Centralized registry for tool discovery
    - Category-based organization
    - Name-based lookup
    - LangGraph integration support
"""

from typing import List, Dict, Any
from .base import BaseTool

# Import all tool instances
from .qdrant_tools import (
    qdrant_search_products,
    qdrant_retrieve_financial_rules,
    qdrant_find_similar_users,
    cluster_alternatives
)

from .ml_tools import (
    calculate_affordability,
    thompson_sample_ranking,
    update_thompson_sampling,
    generate_creative_financing_paths,
    estimate_query_complexity
)

from .llm_tools import (
    generate_explanation,
    verify_explanation_facts,
    evaluate_with_ragas
)


# ============================================================================
# TOOL REGISTRY
# ============================================================================

ALL_TOOLS: List[BaseTool] = [
    # Qdrant tools (4)
    qdrant_search_products,
    qdrant_retrieve_financial_rules,
    qdrant_find_similar_users,
    cluster_alternatives,

    # ML/RL tools (5)
    calculate_affordability,
    thompson_sample_ranking,
    update_thompson_sampling,
    generate_creative_financing_paths,
    estimate_query_complexity,

    # LLM tools (3)
    generate_explanation,
    verify_explanation_facts,
    evaluate_with_ragas
]


TOOL_CATEGORIES = {
    "qdrant": [
        qdrant_search_products,
        qdrant_retrieve_financial_rules,
        qdrant_find_similar_users,
        cluster_alternatives
    ],
    "ml_rl": [
        calculate_affordability,
        thompson_sample_ranking,
        update_thompson_sampling,
        generate_creative_financing_paths,
        estimate_query_complexity
    ],
    "llm": [
        generate_explanation,
        verify_explanation_facts,
        evaluate_with_ragas
    ]
}


# Tool name to instance mapping (for fast lookup)
TOOL_MAP = {tool.name: tool for tool in ALL_TOOLS}


# ============================================================================
# REGISTRY FUNCTIONS
# ============================================================================

def get_tool_by_name(name: str) -> BaseTool:
    """
    Get tool by name.

    Args:
        name: Tool name (e.g., "qdrant_search_products")

    Returns:
        Tool instance

    Raises:
        ValueError: If tool not found

    Example:
        >>> tool = get_tool_by_name("qdrant_search_products")
        >>> result = tool.invoke({"query_vector": [...], "top_k": 10})
    """
    if name not in TOOL_MAP:
        available = ", ".join(TOOL_MAP.keys())
        raise ValueError(
            f"Tool '{name}' not found. Available tools: {available}"
        )
    return TOOL_MAP[name]


def list_tools() -> List[str]:
    """
    List all tool names.

    Returns:
        List of tool names

    Example:
        >>> tools = list_tools()
        >>> print(f"Available: {len(tools)} tools")
        >>> for tool_name in tools:
        ...     print(f"  - {tool_name}")
    """
    return [tool.name for tool in ALL_TOOLS]


def get_tools_by_category(category: str) -> List[BaseTool]:
    """
    Get tools by category.

    Args:
        category: Category name ("qdrant", "ml_rl", or "llm")

    Returns:
        List of tools in category

    Raises:
        ValueError: If category not found

    Example:
        >>> qdrant_tools = get_tools_by_category("qdrant")
        >>> print(f"Qdrant tools: {len(qdrant_tools)}")
    """
    if category not in TOOL_CATEGORIES:
        available = ", ".join(TOOL_CATEGORIES.keys())
        raise ValueError(
            f"Category '{category}' not found. Available: {available}"
        )
    return TOOL_CATEGORIES[category]


def get_tool_schemas() -> List[Dict[str, Any]]:
    """
    Get tool schemas for LangGraph integration.

    Returns:
        List of tool schema dicts with name, description, input_schema

    Example:
        >>> schemas = get_tool_schemas()
        >>> for schema in schemas:
        ...     print(f"{schema['name']}: {schema['description']}")
    """
    return [tool.get_schema() for tool in ALL_TOOLS]


def get_tool_summary() -> Dict[str, Any]:
    """
    Get summary of all tools organized by category.

    Returns:
        Dictionary with tool counts and listings by category

    Example:
        >>> summary = get_tool_summary()
        >>> print(f"Total tools: {summary['total_count']}")
        >>> print(f"Qdrant tools: {summary['by_category']['qdrant']['count']}")
    """
    return {
        "total_count": len(ALL_TOOLS),
        "by_category": {
            category: {
                "count": len(tools),
                "tools": [tool.name for tool in tools]
            }
            for category, tools in TOOL_CATEGORIES.items()
        },
        "all_tools": [tool.name for tool in ALL_TOOLS]
    }


def validate_registry() -> Dict[str, Any]:
    """
    Validate tool registry integrity.

    Checks:
    - All tools have unique names
    - All tools have valid schemas
    - All categories have tools
    - Tool map matches ALL_TOOLS

    Returns:
        Validation result with status and issues

    Example:
        >>> result = validate_registry()
        >>> if result["valid"]:
        ...     print("✅ Registry valid")
        >>> else:
        ...     print(f"❌ Issues: {result['issues']}")
    """
    issues = []

    # Check unique names
    names = [tool.name for tool in ALL_TOOLS]
    if len(names) != len(set(names)):
        duplicates = [name for name in names if names.count(name) > 1]
        issues.append(f"Duplicate tool names: {set(duplicates)}")

    # Check tool schemas
    for tool in ALL_TOOLS:
        try:
            schema = tool.get_schema()
            if not isinstance(schema, dict):
                issues.append(f"Tool {tool.name} has invalid schema type")
            if "name" not in schema or "description" not in schema:
                issues.append(f"Tool {tool.name} missing required schema fields")
        except Exception as e:
            issues.append(f"Tool {tool.name} schema error: {e}")

    # Check categories
    for category, tools in TOOL_CATEGORIES.items():
        if not tools:
            issues.append(f"Category '{category}' is empty")

    # Check tool map
    if len(TOOL_MAP) != len(ALL_TOOLS):
        issues.append(f"TOOL_MAP size mismatch: {len(TOOL_MAP)} vs {len(ALL_TOOLS)}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "total_tools": len(ALL_TOOLS),
        "categories": list(TOOL_CATEGORIES.keys())
    }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Registry constants
    "ALL_TOOLS",
    "TOOL_CATEGORIES",
    "TOOL_MAP",

    # Registry functions
    "get_tool_by_name",
    "list_tools",
    "get_tools_by_category",
    "get_tool_schemas",
    "get_tool_summary",
    "validate_registry",

    # Qdrant tools
    "qdrant_search_products",
    "qdrant_retrieve_financial_rules",
    "qdrant_find_similar_users",
    "cluster_alternatives",

    # ML/RL tools
    "calculate_affordability",
    "thompson_sample_ranking",
    "update_thompson_sampling",
    "generate_creative_financing_paths",
    "estimate_query_complexity",

    # LLM tools
    "generate_explanation",
    "verify_explanation_facts",
    "evaluate_with_ragas",
]
