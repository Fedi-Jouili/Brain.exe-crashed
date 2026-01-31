"""
Agent Trace Schemas
Observability and explainability for multi-agent decisions
"""
from pydantic import BaseModel, Field
from typing import Any, Optional, Literal
from datetime import datetime
from enum import Enum


class AgentName(str, Enum):
    """Agent identifiers"""
    DISCOVERY = "discovery"
    FINANCIAL = "financial"
    PATHFINDER = "pathfinder"
    RANKING = "ranking"
    EXPLAINER = "explainer"


class AgentDecision(str, Enum):
    """Agent decision outcomes"""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    WARN = "WARN"
    PASS = "PASS"  # No decision, just processing


class AgentStep(BaseModel):
    """Single agent execution step"""
    agent: AgentName
    started_at: datetime
    completed_at: datetime
    duration_ms: int
    
    # Input/Output
    input: dict[str, Any]
    output: dict[str, Any]
    
    # Decision (if applicable)
    decision: Optional[AgentDecision] = None
    decision_reason: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)
    
    # Errors
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent": "financial",
                "started_at": "2024-01-15T10:30:00Z",
                "completed_at": "2024-01-15T10:30:00.042Z",
                "duration_ms": 42,
                "input": {
                    "product_price": 299.99,
                    "user_income": 5000
                },
                "output": {
                    "affordability_score": 78,
                    "dti_impact": 0.02
                },
                "decision": "APPROVE",
                "decision_reason": "Within safe spending limits",
                "confidence": 0.92
            }
        }


class DiscoveryAgentOutput(BaseModel):
    """Discovery agent specific output"""
    query_embedding: Optional[list[float]] = None
    products_found: int
    search_strategy: str
    vector_similarity_scores: list[float]


class FinancialAgentOutput(BaseModel):
    """Financial analyzer agent output"""
    decision: AgentDecision
    reason: str
    dti_before: float
    dti_after: float
    affordability_scores: dict[str, float]  # product_id -> score
    rejected_products: list[str]
    warnings: list[str]


class PathFinderAgentOutput(BaseModel):
    """PathFinder agent output"""
    alternatives_found: int
    clusters_analyzed: int
    alternative_products: list[str]  # product IDs
    savings_opportunities: dict[str, float]


class RankingAgentOutput(BaseModel):
    """Ranking agent output (Thompson Sampling)"""
    method: Literal["thompson_sampling"]
    arm_selections: dict[str, int]  # product_id -> selection count
    exploitation_vs_exploration: float  # 0-1, higher = more exploitation
    selected_order: list[str]  # Final product ordering


class ExplainerAgentOutput(BaseModel):
    """Explainer agent output"""
    summaries: dict[str, str]  # product_id -> summary
    decision_explanation: str
    key_factors: list[str]
    user_specific_insights: list[str]


class AgentTrace(BaseModel):
    """Complete agent trace for a request"""
    trace_id: str
    request_id: str
    user_id: str
    
    # Timing
    started_at: datetime
    completed_at: datetime
    total_duration_ms: int
    
    # Agent steps
    agents: list[AgentStep]
    
    # Final outcome
    final_decision: AgentDecision
    products_returned: int
    alternatives_returned: int
    
    # Request context
    original_query: str
    applied_filters: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "trace_id": "550e8400-e29b-41d4-a716-446655440000",
                "request_id": "req_abc123",
                "user_id": "user_xyz",
                "started_at": "2024-01-15T10:30:00Z",
                "completed_at": "2024-01-15T10:30:00.350Z",
                "total_duration_ms": 350,
                "agents": [],
                "final_decision": "APPROVE",
                "products_returned": 15,
                "alternatives_returned": 3,
                "original_query": "wireless headphones",
                "applied_filters": {"max_price": 300}
            }
        }


class TraceListResponse(BaseModel):
    """List of traces for a user"""
    traces: list[AgentTrace]
    total: int
    page: int
    page_size: int
