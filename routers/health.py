"""Health check router endpoint for service verification."""

from datetime import datetime, timezone
import os
import time
from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.session import get_db

router = APIRouter(tags=["Health Check"])

START_TIME = time.time()


@router.api_route(
    "/health",
    methods=["GET", "HEAD"],
    summary="Health Check Endpoint",
    response_model=None,
)
def health_check(
    db: Session = Depends(get_db),
) -> Any:
    """Production health check endpoint verifying database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        uptime_seconds = round(time.time() - START_TIME, 2)

        return {
            "status": "healthy",
            "service": "E-Kart Backend",
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "production"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime": f"{uptime_seconds} seconds",
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
            },
        )
