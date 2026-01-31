"""
Health and Metrics Routes
System observability endpoints
"""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.middleware import require_admin
from app.schemas.auth import AuthenticatedUser

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns service status and version information.
    No authentication required.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness probe for Kubernetes/container orchestration.
    
    Checks if all dependencies are available.
    """
    # In production: check Redis, Qdrant, database connections
    checks = {
        "database": True,  # TODO: actual check
        "redis": True,     # TODO: actual check
        "qdrant": True     # TODO: actual check
    }
    
    all_ready = all(checks.values())
    
    return {
        "ready": all_ready,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/health/live")
async def liveness_check():
    """
    Liveness probe for Kubernetes/container orchestration.
    
    Simple check that the service is running.
    """
    return {
        "alive": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get(
    "/metrics",
    responses={
        403: {"description": "Admin access required"}
    }
)
async def get_metrics(
    current_user: Annotated[AuthenticatedUser, Depends(require_admin)]
):
    """
    Get system metrics.
    
    Requires admin authentication.
    """
    # In production: collect actual metrics from Prometheus/StatsD
    return {
        "requests": {
            "total": 0,
            "success": 0,
            "error": 0
        },
        "latency": {
            "p50_ms": 0,
            "p95_ms": 0,
            "p99_ms": 0
        },
        "agents": {
            "discovery": {"calls": 0, "avg_ms": 0},
            "financial": {"calls": 0, "avg_ms": 0},
            "pathfinder": {"calls": 0, "avg_ms": 0},
            "ranking": {"calls": 0, "avg_ms": 0},
            "explainer": {"calls": 0, "avg_ms": 0}
        },
        "cache": {
            "hits": 0,
            "misses": 0,
            "hit_rate": 0
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
