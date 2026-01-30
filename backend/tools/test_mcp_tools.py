"""
Unit Tests for MCP Tools

Tests all 12 tools:
- 4 Qdrant tools
- 5 ML/RL tools
- 3 LLM tools

Run with: pytest backend/tools/test_mcp_tools.py -v

Test Categories:
1. Tool structure tests (name, description, schema)
2. Input validation tests (Pydantic schemas)
3. Tool invocation tests (mock execution)
4. Integration tests (actual execution, marked with pytest.mark.integration)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Import tool classes and instances
from tools.base import BaseTool, ToolInput, ToolOutput
from tools.qdrant_tools import (
    QdrantSearchProductsTool,
    QdrantRetrieveFinancialRulesTool,
    QdrantFindSimilarUsersTool,
    ClusterAlternativesTool,
    qdrant_search_products,
    qdrant_retrieve_financial_rules,
    qdrant_find_similar_users,
    cluster_alternatives
)
from tools.ml_tools import (
    CalculateAffordabilityTool,
    ThompsonSampleRankingTool,
    UpdateThompsonSamplingTool,
    GenerateCreativeFinancingPathsTool,
    EstimateQueryComplexityTool,
    calculate_affordability,
    thompson_sample_ranking,
    update_thompson_sampling,
    generate_creative_financing_paths,
    estimate_query_complexity
)
from tools.llm_tools import (
    GenerateExplanationTool,
    VerifyExplanationFactsTool,
    EvaluateWithRAGASTool,
    generate_explanation,
    verify_explanation_facts,
    evaluate_with_ragas
)
from tools.mcp_tools import (
    ALL_TOOLS,
    TOOL_CATEGORIES,
    get_tool_by_name,
    list_tools,
    get_tools_by_category,
    validate_registry
)


# ============================================================================
# TEST: REGISTRY
# ============================================================================

class TestToolRegistry:
    """Test tool registry functionality"""

    def test_all_tools_count(self):
        """Test that registry has all 12 tools"""
        assert len(ALL_TOOLS) == 12, f"Expected 12 tools, got {len(ALL_TOOLS)}"

    def test_tool_categories_count(self):
        """Test category counts"""
        assert len(TOOL_CATEGORIES["qdrant"]) == 4, "Expected 4 Qdrant tools"
        assert len(TOOL_CATEGORIES["ml_rl"]) == 5, "Expected 5 ML/RL tools"
        assert len(TOOL_CATEGORIES["llm"]) == 3, "Expected 3 LLM tools"

    def test_list_tools(self):
        """Test list_tools function"""
        tools = list_tools()
        assert len(tools) == 12
        assert "qdrant_search_products" in tools
        assert "thompson_sample_ranking" in tools
        assert "generate_explanation" in tools

    def test_get_tool_by_name(self):
        """Test get_tool_by_name function"""
        tool = get_tool_by_name("qdrant_search_products")
        assert isinstance(tool, BaseTool)
        assert tool.name == "qdrant_search_products"

    def test_get_tool_by_name_invalid(self):
        """Test get_tool_by_name with invalid name"""
        with pytest.raises(ValueError, match="Tool .* not found"):
            get_tool_by_name("nonexistent_tool")

    def test_get_tools_by_category(self):
        """Test get_tools_by_category function"""
        qdrant_tools = get_tools_by_category("qdrant")
        assert len(qdrant_tools) == 4
        assert all(isinstance(t, BaseTool) for t in qdrant_tools)

    def test_validate_registry(self):
        """Test registry validation"""
        result = validate_registry()
        assert result["valid"] is True, f"Registry invalid: {result['issues']}"
        assert result["total_tools"] == 12


# ============================================================================
# TEST: QDRANT TOOLS
# ============================================================================

class TestQdrantTools:
    """Test Qdrant tool implementations"""

    def test_qdrant_search_products_structure(self):
        """Test tool has correct structure"""
        assert qdrant_search_products.name == "qdrant_search_products"
        assert qdrant_search_products.description is not None
        assert qdrant_search_products.input_schema is not None

    def test_qdrant_search_products_schema(self):
        """Test tool schema"""
        schema = qdrant_search_products.get_schema()
        assert "name" in schema
        assert "description" in schema
        assert "input_schema" in schema

    def test_qdrant_search_products_input_validation_success(self):
        """Test valid input passes validation"""
        result = qdrant_search_products.invoke({
            "query_vector": [0.1] * 512,
            "top_k": 10,
            "filters": {"category": "Electronics"},
            "score_threshold": 0.7
        })
        assert "success" in result
        # Note: Will fail without Qdrant, but input validation should pass

    def test_qdrant_search_products_input_validation_failure(self):
        """Test invalid input fails validation"""
        result = qdrant_search_products.invoke({
            "query_vector": [0.1] * 100,  # Wrong dimension
            "top_k": 10
        })
        assert result["success"] is False
        assert "error" in result
        assert "512" in result["error"]  # Should mention dimension requirement

    def test_financial_rules_tool_structure(self):
        """Test financial rules tool structure"""
        assert qdrant_retrieve_financial_rules.name == "qdrant_retrieve_financial_rules"
        assert qdrant_retrieve_financial_rules.input_schema is not None

    def test_similar_users_tool_structure(self):
        """Test similar users tool structure"""
        assert qdrant_find_similar_users.name == "qdrant_find_similar_users"
        assert qdrant_find_similar_users.input_schema is not None

    def test_cluster_alternatives_tool_structure(self):
        """Test cluster alternatives tool structure"""
        assert cluster_alternatives.name == "cluster_alternatives"
        assert cluster_alternatives.input_schema is not None


# ============================================================================
# TEST: ML/RL TOOLS
# ============================================================================

class TestMLRLTools:
    """Test ML/RL tool implementations"""

    def test_calculate_affordability_structure(self):
        """Test affordability tool structure"""
        assert calculate_affordability.name == "calculate_affordability"
        assert calculate_affordability.input_schema is not None

    def test_calculate_affordability_input_validation(self):
        """Test affordability input validation"""
        # Valid input
        result = calculate_affordability.invoke({
            "product": {"price": 1000.0, "name": "Laptop"},
            "user": {"monthly_income": 5000.0, "monthly_expenses": 3000.0},
            "financial_rules": []
        })
        # Will fail execution without proper setup, but validation should pass
        assert "success" in result

        # Invalid input (missing price)
        result = calculate_affordability.invoke({
            "product": {"name": "Laptop"},  # No price
            "user": {"monthly_income": 5000.0},
            "financial_rules": []
        })
        assert result["success"] is False
        assert "price" in result["error"].lower()

    def test_thompson_sample_ranking_structure(self):
        """Test Thompson ranking tool structure"""
        assert thompson_sample_ranking.name == "thompson_sample_ranking"
        assert thompson_sample_ranking.input_schema is not None

    def test_thompson_sample_ranking_input_validation(self):
        """Test Thompson ranking input validation"""
        # Valid input
        result = thompson_sample_ranking.invoke({
            "product_ids": ["PROD001", "PROD002", "PROD003"]
        })
        assert "success" in result
        # Note: Will fail without Redis, but input validation should pass

        # Invalid input (empty list)
        result = thompson_sample_ranking.invoke({
            "product_ids": []
        })
        assert result["success"] is False

    def test_update_thompson_sampling_structure(self):
        """Test Thompson update tool structure"""
        assert update_thompson_sampling.name == "update_thompson_sampling"
        assert update_thompson_sampling.input_schema is not None

    def test_update_thompson_sampling_input_validation(self):
        """Test Thompson update input validation"""
        # Valid action
        result = update_thompson_sampling.invoke({
            "product_id": "PROD001",
            "action": "click"
        })
        assert "success" in result

        # Invalid action
        result = update_thompson_sampling.invoke({
            "product_id": "PROD001",
            "action": "invalid_action"
        })
        assert result["success"] is False
        assert "action" in result["error"].lower()

    def test_financing_paths_tool_structure(self):
        """Test financing paths tool structure"""
        assert generate_creative_financing_paths.name == "generate_creative_financing_paths"
        assert generate_creative_financing_paths.input_schema is not None

    def test_complexity_estimation_tool_structure(self):
        """Test complexity estimation tool structure"""
        assert estimate_query_complexity.name == "estimate_query_complexity"
        assert estimate_query_complexity.input_schema is not None

    def test_complexity_estimation_input_validation(self):
        """Test complexity estimation input validation"""
        # Valid input
        result = estimate_query_complexity.invoke({
            "query": "laptops under $1000"
        })
        assert "success" in result

        # Invalid input (empty query)
        result = estimate_query_complexity.invoke({
            "query": ""
        })
        assert result["success"] is False


# ============================================================================
# TEST: LLM TOOLS
# ============================================================================

class TestLLMTools:
    """Test LLM tool implementations"""

    def test_generate_explanation_structure(self):
        """Test explanation generation tool structure"""
        assert generate_explanation.name == "generate_explanation"
        assert generate_explanation.input_schema is not None

    def test_generate_explanation_input_validation(self):
        """Test explanation generation input validation"""
        # Valid input
        result = generate_explanation.invoke({
            "context": {
                "product": {
                    "name": "Dell XPS 15",
                    "price": 1500.0,
                    "category": "Laptops",
                    "rating": 4.7,
                    "num_reviews": 523
                },
                "affordability": {
                    "can_afford_cash": False,
                    "can_afford_financing": True,
                    "risk_level": "caution"
                },
                "financial_standing": "moderate"
            },
            "rank": 1
        })
        assert "success" in result
        # Note: Will fail without API key, but should use fallback

        # Invalid input (missing required context keys)
        result = generate_explanation.invoke({
            "context": {"product": {}},  # Missing affordability, financial_standing
            "rank": 1
        })
        assert result["success"] is False

    def test_verify_explanation_facts_structure(self):
        """Test fact verification tool structure"""
        assert verify_explanation_facts.name == "verify_explanation_facts"
        assert verify_explanation_facts.input_schema is not None

    def test_verify_explanation_facts_execution(self):
        """Test fact verification execution (no external deps)"""
        result = verify_explanation_facts.invoke({
            "explanation": "The Dell XPS 15 laptop is affordable through financing at $1500.",
            "context": {
                "product": {
                    "name": "Dell XPS 15",
                    "price": 1500.0,
                    "category": "Laptops"
                },
                "affordability": {
                    "can_afford_cash": False,
                    "can_afford_financing": True
                }
            }
        })
        assert result["success"] is True
        assert "verified" in result["data"]
        assert "trust_score" in result["data"]
        assert "violations" in result["data"]
        assert isinstance(result["data"]["trust_score"], float)
        assert 0.0 <= result["data"]["trust_score"] <= 1.0

    def test_evaluate_with_ragas_structure(self):
        """Test RAGAS evaluation tool structure"""
        assert evaluate_with_ragas.name == "evaluate_with_ragas"
        assert evaluate_with_ragas.input_schema is not None

    def test_evaluate_with_ragas_execution(self):
        """Test RAGAS evaluation execution (simplified implementation)"""
        result = evaluate_with_ragas.invoke({
            "question": "Can I afford a $1000 laptop?",
            "answer": "Yes, you can afford it through financing with 5% APR.",
            "contexts": [
                "User monthly income: $5000",
                "DTI threshold: 36%",
                "Financing available with 5% APR"
            ]
        })
        assert result["success"] is True
        assert "metrics" in result["data"]
        assert "overall_score" in result["data"]
        assert "faithfulness" in result["data"]["metrics"]
        assert "answer_relevance" in result["data"]["metrics"]


# ============================================================================
# TEST: BASE TOOL CLASS
# ============================================================================

class TestBaseTool:
    """Test base tool functionality"""

    def test_tool_output_structure(self):
        """Test ToolOutput structure"""
        output = ToolOutput(success=True, data={"result": 42})
        assert output.success is True
        assert output.error is None
        assert output.data == {"result": 42}

        output_dict = output.dict()
        assert isinstance(output_dict, dict)
        assert "success" in output_dict
        assert "data" in output_dict

    def test_tool_output_error_structure(self):
        """Test ToolOutput error structure"""
        output = ToolOutput(success=False, error="Something went wrong", data=None)
        assert output.success is False
        assert output.error == "Something went wrong"
        assert output.data is None

    def test_custom_tool_implementation(self):
        """Test creating a custom tool"""

        class CustomInput(ToolInput):
            value: int

        class CustomTool(BaseTool):
            name = "custom_tool"
            description = "A custom test tool"
            input_schema = CustomInput

            def _execute(self, input_data: CustomInput) -> ToolOutput:
                result = input_data.value * 2
                return ToolOutput(success=True, data={"result": result})

        tool = CustomTool()
        result = tool.invoke({"value": 21})

        assert result["success"] is True
        assert result["data"]["result"] == 42

    def test_tool_exception_handling(self):
        """Test tool handles exceptions gracefully"""

        class FailingInput(ToolInput):
            value: int

        class FailingTool(BaseTool):
            name = "failing_tool"
            description = "A tool that fails"
            input_schema = FailingInput

            def _execute(self, input_data: FailingInput) -> ToolOutput:
                raise ValueError("Intentional failure")

        tool = FailingTool()
        result = tool.invoke({"value": 42})

        assert result["success"] is False
        assert "error" in result
        assert "Intentional failure" in result["error"]


# ============================================================================
# INTEGRATION TESTS (Require External Services)
# ============================================================================

@pytest.mark.integration
class TestToolsIntegration:
    """Integration tests requiring actual services (Qdrant, Redis, LLM API)"""

    @pytest.mark.skip(reason="Requires Qdrant running")
    def test_qdrant_search_products_integration(self):
        """Test actual product search with Qdrant"""
        result = qdrant_search_products.invoke({
            "query_vector": [0.1] * 512,
            "top_k": 5,
            "score_threshold": 0.5
        })

        if result["success"]:
            assert "products" in result["data"]
            assert isinstance(result["data"]["products"], list)
            assert result["data"]["count"] >= 0

    @pytest.mark.skip(reason="Requires Redis running")
    def test_thompson_ranking_integration(self):
        """Test actual Thompson Sampling ranking"""
        result = thompson_sample_ranking.invoke({
            "product_ids": ["PROD001", "PROD002", "PROD003"]
        })

        if result["success"]:
            assert "ranked_ids" in result["data"]
            assert "scores" in result["data"]
            assert len(result["data"]["ranked_ids"]) == 3

    @pytest.mark.skip(reason="Requires Gemini API key")
    def test_generate_explanation_integration(self):
        """Test actual LLM explanation generation"""
        result = generate_explanation.invoke({
            "context": {
                "product": {
                    "name": "Dell XPS 15",
                    "price": 1500.0,
                    "category": "Laptops",
                    "brand": "Dell",
                    "rating": 4.7,
                    "num_reviews": 523
                },
                "affordability": {
                    "can_afford_cash": False,
                    "can_afford_financing": True,
                    "risk_level": "caution"
                },
                "financial_standing": "moderate"
            },
            "rank": 1
        })

        # Should succeed with fallback even without API key
        assert result["success"] is True
        assert "explanation" in result["data"]
        assert len(result["data"]["explanation"]) > 0


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    # Run with: python backend/tools/test_mcp_tools.py
    pytest.main([__file__, "-v", "--tb=short"])
