"""
LangGraph Orchestrator
Connects all 5 agents into a coherent workflow
"""
import logging
from typing import Literal
from langgraph.graph import StateGraph, END

from models.state import AgentState
from agents.agent1_discovery import product_discovery_agent
from agents.agent2_financial import financial_analyzer_agent
from agents.agent2_5_pathfinder import budget_pathfinder_agent
from agents.agent3_recommender import smart_recommender_agent
from agents.agent4_explainer import explainer_agent

logger = logging.getLogger(__name__)


def build_recommendation_graph() -> StateGraph:
    """
    Build the multi-agent recommendation workflow
    
    Flow:
    1. Discovery → Find candidate products
    2. Financial → Analyze affordability
    3a. If all unaffordable → Pathfinder → Find alternatives
    3b. If some affordable → Skip pathfinder
    4. Recommender → Rank and score products
    5. Explainer → Generate detailed explanations
    
    Returns:
        Compiled StateGraph ready for execution
    """
    
    # Create workflow
    workflow = StateGraph(AgentState)
    
    # Add agent nodes
    workflow.add_node("discovery", product_discovery_agent.execute)
    workflow.add_node("financial", financial_analyzer_agent.execute)
    workflow.add_node("pathfinder", budget_pathfinder_agent.execute)
    workflow.add_node("recommender", smart_recommender_agent.execute)
    workflow.add_node("explainer", explainer_agent.execute)
    
    # Set entry point
    workflow.set_entry_point("discovery")
    
    # Linear flow: discovery → financial
    workflow.add_edge("discovery", "financial")
    
    # Conditional routing after financial analysis
    def route_after_financial(state: AgentState) -> Literal["pathfinder", "recommender"]:
        """
        Route to pathfinder if all products unaffordable, otherwise to recommender
        """
        if state.get('all_unaffordable', False):
            logger.info("Routing to pathfinder (all products unaffordable)")
            return "pathfinder"
        else:
            logger.info("Routing to recommender (affordable products found)")
            return "recommender"
    
    workflow.add_conditional_edges(
        "financial",
        route_after_financial,
        {
            "pathfinder": "pathfinder",
            "recommender": "recommender"
        }
    )
    
    # Pathfinder → Recommender (if pathfinder was triggered)
    workflow.add_edge("pathfinder", "recommender")
    
    # Recommender → Explainer
    workflow.add_edge("recommender", "explainer")
    
    # Explainer → END
    workflow.add_edge("explainer", END)
    
    # Compile the graph
    app = workflow.compile()
    
    logger.info("LangGraph workflow compiled successfully")
    
    return app


def build_fast_path_graph() -> StateGraph:
    """
    Build a FAST path workflow (cache-only, no agents)
    
    This is used when:
    - Query complexity is very low
    - Cache hit is available
    - User wants quick results
    
    Returns:
        Compiled StateGraph for fast path
    """
    workflow = StateGraph(AgentState)
    
    def return_cached(state: AgentState) -> AgentState:
        """Return cached results directly"""
        logger.info("Fast path: Returning cached results")
        return state
    
    workflow.add_node("cache", return_cached)
    workflow.set_entry_point("cache")
    workflow.add_edge("cache", END)
    
    app = workflow.compile()
    logger.info("Fast path workflow compiled")
    
    return app


def build_smart_path_graph() -> StateGraph:
    """
    Build a SMART path workflow (Agent 1 + Agent 3 only)
    
    This is used when:
    - Query complexity is medium
    - Financial analysis not needed (no user profile)
    - Just need good product recommendations
    
    Flow:
    1. Discovery → Find products
    2. Recommender → Rank by Thompson + RAGAS (no financial)
    3. Explainer → Brief explanations
    
    Returns:
        Compiled StateGraph for smart path
    """
    workflow = StateGraph(AgentState)
    
    # Adapter node to convert candidate_products to affordable_products format
    def prepare_for_recommender(state: AgentState) -> AgentState:
        """
        Convert candidate_products to affordable_products format for Agent 3
        Since we skip Agent 2, assume all products are affordable
        """
        candidate_products = state.get('candidate_products', [])
        
        # Convert to affordable format (simulate 100% affordability)
        affordable_products = []
        for product in candidate_products:
            affordable_products.append({
                'product': product,
                'affordability': {
                    'is_affordable': True,
                    'affordability_score': 100.0,
                    'cash_score': 100.0,
                    'credit_score': 100.0,
                    'payment_plan_score': 100.0
                },
                'financial_score': 100.0
            })
        
        state['affordable_products'] = affordable_products
        state['all_unaffordable'] = False
        logger.info(f"SMART path: Prepared {len(affordable_products)} products for ranking")
        return state
    
    workflow.add_node("discovery", product_discovery_agent.execute)
    workflow.add_node("prepare", prepare_for_recommender)
    workflow.add_node("recommender", smart_recommender_agent.execute)
    workflow.add_node("explainer", explainer_agent.execute)
    
    workflow.set_entry_point("discovery")
    workflow.add_edge("discovery", "prepare")
    workflow.add_edge("prepare", "recommender")
    workflow.add_edge("recommender", "explainer")
    workflow.add_edge("explainer", END)
    
    app = workflow.compile()
    logger.info("Smart path workflow compiled")
    
    return app


# Global compiled graphs (singleton pattern for performance)
_deep_graph = None
_smart_graph = None
_fast_graph = None


def get_deep_graph() -> StateGraph:
    """Get or create the DEEP path graph (all 5 agents)"""
    global _deep_graph
    if _deep_graph is None:
        _deep_graph = build_recommendation_graph()
    return _deep_graph


def get_smart_graph() -> StateGraph:
    """Get or create the SMART path graph (Agents 1, 3, 4)"""
    global _smart_graph
    if _smart_graph is None:
        _smart_graph = build_smart_path_graph()
    return _smart_graph


def get_fast_graph() -> StateGraph:
    """Get or create the FAST path graph (cache only)"""
    global _fast_graph
    if _fast_graph is None:
        _fast_graph = build_fast_path_graph()
    return _fast_graph


def execute_workflow(state: AgentState, path: str = "DEEP") -> AgentState:
    """
    Execute the appropriate workflow based on path
    
    Args:
        state: Initial agent state
        path: Workflow path - "FAST", "SMART", or "DEEP"
        
    Returns:
        Final state after workflow execution
    """
    logger.info(f"Executing {path} path workflow")
    
    # Select graph
    if path == "FAST":
        graph = get_fast_graph()
    elif path == "SMART":
        graph = get_smart_graph()
    else:  # DEEP
        graph = get_deep_graph()
    
    # Execute workflow
    try:
        result = graph.invoke(state)
        logger.info(f"{path} path completed successfully")
        return result
    except Exception as e:
        logger.error(f"{path} path failed: {e}")
        # Add error to state
        if 'errors' not in state:
            state['errors'] = []
        state['errors'].append(str(e))
        return state
