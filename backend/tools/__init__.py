"""
MCP Tools Module - Model Context Protocol Tool Abstraction Layer

This module provides a standardized tool abstraction layer that decouples
agents from direct service calls, enabling:
- Clean architecture (agents depend on interfaces, not implementations)
- Independent agent testing (tools can be mocked)
- Tool reusability across agents
- Type-safe, auto-discoverable tools
- LangGraph native tool integration

Architecture:
    tools/
    ├── base.py              # Base tool interface
    ├── qdrant_tools.py      # Qdrant vector DB tools (4 tools)
    ├── ml_tools.py          # ML/RL tools (5 tools)
    ├── llm_tools.py         # LLM & evaluation tools (3 tools)
    ├── mcp_tools.py         # Unified tool registry
    └── test_mcp_tools.py    # Tool tests

Usage:
    # Import tools from registry
    from tools.mcp_tools import (
        qdrant_search_products,
        calculate_affordability,
        thompson_sample_ranking
    )

    # Use tool with type-safe input
    result = qdrant_search_products.invoke({
        "query_vector": embedding,
        "top_k": 50,
        "filters": {"category": "Electronics"}
    })

    # Handle result
    if result["success"]:
        products = result["data"]["products"]
    else:
        logger.error(f"Tool failed: {result['error']}")

Design Principles:
- Interface Segregation: Each tool has a focused responsibility
- Dependency Inversion: Agents depend on abstractions (tools), not concretions (services)
- Single Responsibility: Each tool does one thing well
- Type Safety: Pydantic validation ensures correct inputs
- Error Handling: All tools return success/error format
"""

__version__ = "1.0.0"

# Import will be added after tools are created
__all__ = [
    "base",
    "qdrant_tools",
    "ml_tools",
    "llm_tools",
    "mcp_tools",
]
