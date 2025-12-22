"""
Metrics API Routes
Exposes metrics endpoint for monitoring dashboard
"""

from fastapi import APIRouter
from utils.metrics_middleware import get_metrics_summary

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])


@router.get("")
@router.get("/")
async def get_metrics():
    """
    Get backend metrics for monitoring dashboard
    
    Returns metrics including:
    - Hourly request counts and response times
    - Endpoint-specific performance data
    - Error rates and types
    - Server health information
    """
    return get_metrics_summary()


@router.get("/health")
async def metrics_health():
    """Quick health check for metrics endpoint"""
    from datetime import datetime, timezone
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
