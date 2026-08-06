"""Health check router endpoint for service verification."""

import os
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.session import get_db

router = APIRouter(tags=["Health"])

START_TIME = time.time()


@router.api_route(
    "/health",
    methods=["GET", "HEAD"],
    summary="Service Health Check",
    description="Production health check endpoint verifying PostgreSQL database connectivity, service environment, timestamp, and system uptime.",
    response_description="Service health status payload",
    tags=["Health"],
    response_model=None,
    responses={
        200: {
            "description": "System is operational and healthy.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "E-Kart Backend",
                        "version": "1.0.0",
                        "environment": "production",
                        "timestamp": "2026-08-04T09:57:00.000Z",
                        "uptime": "123.45 seconds",
                    }
                }
            },
        },
        503: {
            "description": "Service unhealthy or database unreachable.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "database": "disconnected",
                        "error": "Could not connect to database server",
                    }
                }
            },
        },
    },
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


@router.get(
    "/health/redis",
    summary="Redis Cache Health Check",
    description="Verify Redis server connection, ping status, and caching mode.",
    response_description="Redis health status JSON payload",
    tags=["Health"],
    responses={
        200: {
            "description": "Redis operational status.",
            "content": {
                "application/json": {
                    "example": {
                        "redis_connected": True,
                        "ping": "PONG",
                        "cache": "working",
                    }
                }
            },
        }
    },
)
@router.get("/redis/health", tags=["Health"], include_in_schema=False)
def redis_health_check() -> dict[str, Any]:
    """Check Redis connectivity and operational status."""
    from redis_client import redis_client

    pong, connected = redis_client.ping()
    if connected:
        return {
            "redis_connected": True,
            "ping": "PONG",
            "cache": "working",
        }
    return {
        "redis_connected": False,
        "ping": None,
        "cache": "fallback_db",
        "details": pong,
    }

