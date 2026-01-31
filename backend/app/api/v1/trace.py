"""
Trace Routes
Agent trace retrieval for observability and debugging
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.middleware import require_auth
from app.schemas.auth import AuthenticatedUser
from app.schemas.trace import AgentTrace, TraceListResponse
from app.schemas.errors import ErrorCode, ErrorResponse
from app.agents.orchestrator import orchestrator

router = APIRouter(prefix="/trace", tags=["Observability"])


@router.get(
    "/{trace_id}",
    response_model=AgentTrace,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Trace not found"}
    }
)
async def get_trace(
    trace_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(require_auth)]
):
    """
    Retrieve agent trace by ID.
    
    Returns the complete execution trace showing how each agent
    processed the request and made decisions.
    
    Users can only access their own traces (unless admin).
    """
    trace = orchestrator.get_trace(trace_id)
    
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code=ErrorCode.TRACE_NOT_FOUND,
                message="Trace not found",
                details={"trace_id": trace_id}
            ).model_dump()
        )
    
    # Check authorization (users can only see their own traces)
    if trace.user_id != current_user.user_id and current_user.role.value != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                error_code=ErrorCode.FORBIDDEN,
                message="You don't have access to this trace"
            ).model_dump()
        )
    
    return trace


@router.get(
    "",
    response_model=TraceListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"}
    }
)
async def list_traces(
    current_user: Annotated[AuthenticatedUser, Depends(require_auth)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10
):
    """
    List agent traces for the current user.
    
    Returns paginated list of traces ordered by most recent first.
    """
    traces = orchestrator.get_user_traces(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size
    )
    
    # Get total count
    all_traces = orchestrator.get_user_traces(current_user.user_id, page=1, page_size=1000)
    
    return TraceListResponse(
        traces=traces,
        total=len(all_traces),
        page=page,
        page_size=page_size
    )
