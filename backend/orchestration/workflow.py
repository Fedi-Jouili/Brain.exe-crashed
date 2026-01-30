"""
LangGraph Workflow Orchestration for PriceSense
Connects all 5 agents into cohesive recommendation pipeline
"""
import logging
import time
from typing import Dict, Any, Optional, Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Import models and agents
from models.state import AgentState
from models.schemas import UserProfile
from agents.agent1_discovery import product_discovery_agent
from agents.agent2_financial import financial_analyzer_agent
from agents.agent2_5_pathfinder import budget_pathfinder_agent
from agents.agent3_recommender import smart_recommender_agent
from agents.agent4_explainer import explainer_agent

logger = logging.getLogger(__name__)


# ============================================================================
# AGENT WRAPPER FUNCTIONS
# ============================================================================

def run_discovery(state: AgentState) -> AgentState:
    """
    Execute Agent 1: Discovery

    Input: query, user_profile
    Output: candidate_products
    """
    logger.info("=== EXECUTING AGENT 1: DISCOVERY ===")
    try:
        result = product_discovery_agent.execute(state)
        logger.info(f"Agent 1 complete: {len(result.get('candidate_products', []))} candidates found")
        return result
    except Exception as e:
        logger.error(f"Agent 1 error: {e}", exc_info=True)
        state['candidate_products'] = []
        if 'errors' not in state:
            state['errors'] = []
        state['errors'].append(f"Discovery: {str(e)}")
        return state


def run_financial(state: AgentState) -> AgentState:
    """
    Execute Agent 2: Financial Analysis

    Input: candidate_products, user_profile
    Output: affordable_products, all_unaffordable
    """
    logger.info("=== EXECUTING AGENT 2: FINANCIAL ANALYSIS ===")
    try:
        result = financial_analyzer_agent.execute(state)
        logger.info(
            f"Agent 2 complete: {len(result.get('affordable_products', []))} affordable, "
            f"all_unaffordable={result.get('all_unaffordable', False)}"
        )
        return result
    except Exception as e:
        logger.error(f"Agent 2 error: {e}", exc_info=True)
        state['affordable_products'] = []
        state['all_unaffordable'] = False
        if 'errors' not in state:
            state['errors'] = []
        state['errors'].append(f"Financial: {str(e)}")
        return state


def run_pathfinder(state: AgentState) -> AgentState:
    """
    Execute Agent 2.5: Budget PathFinder (CONDITIONAL)

    Only runs if state['all_unaffordable'] = True

    Input: candidate_products, user_profile
    Output: alternative_paths, affordable_products (updated)
    """
    logger.info("=== EXECUTING AGENT 2.5: BUDGET PATHFINDER ===")
    try:
        result = budget_pathfinder_agent.execute(state)
        logger.info(
            f"Agent 2.5 complete: {len(result.get('alternative_paths', []))} paths generated"
        )
        return result
    except Exception as e:
        logger.error(f"Agent 2.5 error: {e}", exc_info=True)
        state['alternative_paths'] = []
        if 'errors' not in state:
            state['errors'] = []
        state['errors'].append(f"PathFinder: {str(e)}")
        return state


def run_recommender(state: AgentState) -> AgentState:
    """
    Execute Agent 3: Smart Recommender

    Input: affordable_products
    Output: final_recommendations (top 10, ranked)
    """
    logger.info("=== EXECUTING AGENT 3: SMART RECOMMENDER ===")
    try:
        result = smart_recommender_agent.execute(state)
        logger.info(
            f"Agent 3 complete: {len(result.get('final_recommendations', []))} recommendations"
        )
        return result
    except Exception as e:
        logger.error(f"Agent 3 error: {e}", exc_info=True)
        state['final_recommendations'] = []
        if 'errors' not in state:
            state['errors'] = []
        state['errors'].append(f"Recommender: {str(e)}")
        return state


def run_explainer(state: AgentState) -> AgentState:
    """
    Execute Agent 4: Explainer

    Input: final_recommendations
    Output: recommendations with explanation objects
    """
    logger.info("=== EXECUTING AGENT 4: EXPLAINER ===")
    try:
        result = explainer_agent.execute(state)
        logger.info("Agent 4 complete: Explanations generated")
        return result
    except Exception as e:
        logger.error(f"Agent 4 error: {e}", exc_info=True)
        if 'errors' not in state:
            state['errors'] = []
        state['errors'].append(f"Explainer: {str(e)}")
        return state


# ============================================================================
# CONDITIONAL ROUTING
# ============================================================================

def should_run_pathfinder(state: AgentState) -> Literal["pathfinder", "recommender"]:
    """
    Decide if Agent 2.5 (PathFinder) should run

    Logic:
    - IF all_unaffordable = True → run pathfinder
    - ELSE → skip to recommender

    Returns:
        "pathfinder" | "recommender"
    """
    all_unaffordable = state.get('all_unaffordable', False)

    if all_unaffordable:
        logger.info("ROUTING: All products unaffordable → Agent 2.5 (PathFinder)")
        return "pathfinder"
    else:
        logger.info("ROUTING: Products affordable → Agent 3 (Recommender)")
        return "recommender"


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def create_recommendation_graph() -> StateGraph:
    """
    Create LangGraph workflow for PriceSense

    Graph structure:
    START → Agent1 → Agent2 → [conditional] → Agent3 → Agent4 → END
                              ↓
                         all_unaffordable?
                         ↓YES        ↓NO
                      Agent2.5       skip
                         ↓____________↓
                         Agent3

    Returns:
        Compiled StateGraph
    """
    # Create graph with AgentState
    workflow = StateGraph(AgentState)

    # Add agent nodes
    workflow.add_node("discovery", run_discovery)
    workflow.add_node("financial", run_financial)
    workflow.add_node("pathfinder", run_pathfinder)
    workflow.add_node("recommender", run_recommender)
    workflow.add_node("explainer", run_explainer)

    # Define edges
    workflow.set_entry_point("discovery")

    # Agent 1 → Agent 2 (always)
    workflow.add_edge("discovery", "financial")

    # Agent 2 → conditional routing
    workflow.add_conditional_edges(
        "financial",
        should_run_pathfinder,
        {
            "pathfinder": "pathfinder",
            "recommender": "recommender"
        }
    )

    # Agent 2.5 → Agent 3 (if pathfinder ran)
    workflow.add_edge("pathfinder", "recommender")

    # Agent 3 → Agent 4 (always)
    workflow.add_edge("recommender", "explainer")

    # Agent 4 → END (always)
    workflow.add_edge("explainer", END)

    # Compile graph with memory saver (for state persistence)
    memory = MemorySaver()
    compiled_graph = workflow.compile(checkpointer=memory)

    logger.info("LangGraph workflow compiled successfully")

    return compiled_graph


# ============================================================================
# PUBLIC API
# ============================================================================

# Global graph instance (compiled once)
_recommendation_graph = None


def get_recommendation_graph() -> StateGraph:
    """
    Get or create the compiled recommendation graph

    Returns:
        Compiled StateGraph (singleton)
    """
    global _recommendation_graph
    if _recommendation_graph is None:
        _recommendation_graph = create_recommendation_graph()
    return _recommendation_graph


def run_recommendation_pipeline(
    query: str,
    user_profile: Dict[str, Any],
    config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Execute the complete recommendation pipeline

    This is the main entry point for running recommendations.

    Args:
        query: User's search query
        user_profile: User's financial profile dict
        config: Optional LangGraph config (for checkpointing)

    Returns:
        Final state dict with recommendations and explanations

    Example:
        >>> result = run_recommendation_pipeline(
        ...     query="laptop for programming",
        ...     user_profile={
        ...         "monthly_income": 5000,
        ...         "credit_score": 720,
        ...         ...
        ...     }
        ... )
        >>> recommendations = result['final_recommendations']
    """
    start_time = time.time()

    logger.info("=" * 80)
    logger.info("STARTING RECOMMENDATION PIPELINE")
    logger.info(f"Query: {query}")
    logger.info("=" * 80)

    # Create initial state
    initial_state = {
        'query': query,
        'user_profile': UserProfile(**user_profile),
        'candidate_products': [],
        'affordable_products': [],
        'final_recommendations': [],
        'errors': []
    }

    # Get graph
    graph = get_recommendation_graph()

    # Execute graph
    try:
        # Run the graph
        final_state = graph.invoke(
            initial_state,
            config=config or {"configurable": {"thread_id": "default"}}
        )

        # Calculate total execution time
        total_time = int((time.time() - start_time) * 1000)
        final_state['total_execution_time_ms'] = total_time

        # Log summary
        logger.info("=" * 80)
        logger.info("PIPELINE COMPLETE")
        logger.info(f"Total time: {total_time}ms")
        logger.info(f"Candidates: {len(final_state.get('candidate_products', []))}")
        logger.info(f"Affordable: {len(final_state.get('affordable_products', []))}")
        logger.info(f"Final recommendations: {len(final_state.get('final_recommendations', []))}")
        logger.info(f"Errors: {len(final_state.get('errors', []))}")

        if final_state.get('errors'):
            for error in final_state['errors']:
                logger.warning(f"  - {error}")

        logger.info("=" * 80)

        return final_state

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)

        # Return error state
        return {
            'query': query,
            'final_recommendations': [],
            'errors': [f"Pipeline failed: {str(e)}"],
            'total_execution_time_ms': int((time.time() - start_time) * 1000)
        }


# ============================================================================
# VISUALIZATION (Optional)
# ============================================================================

def visualize_graph(output_path: str = "recommendation_graph.png"):
    """
    Generate visual representation of the graph

    Args:
        output_path: Where to save the image
    """
    try:
        from IPython.display import Image, display

        graph = get_recommendation_graph()

        # Generate graph visualization
        graph_image = graph.get_graph().draw_mermaid_png()

        # Save to file
        with open(output_path, 'wb') as f:
            f.write(graph_image)

        logger.info(f"Graph visualization saved to {output_path}")

        # Display if in notebook
        try:
            display(Image(graph_image))
        except:
            pass

    except ImportError:
        logger.warning("IPython not installed, cannot visualize graph")
    except Exception as e:
        logger.error(f"Error visualizing graph: {e}")
