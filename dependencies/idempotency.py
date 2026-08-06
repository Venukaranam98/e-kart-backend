"""FastAPI dependency for extracting and validating the Idempotency-Key header."""

from fastapi import Header, HTTPException, status


def get_idempotency_key(
    idempotency_key: str | None = Header(
        None,
        alias="Idempotency-Key",
        description="Unique UUID or token to guarantee idempotent request execution.",
        example="a2b8d91d-7c4f-4d32-9a10-2e8749b5c001",
    ),
) -> str:
    """Validate presence of Idempotency-Key header and return 400 Bad Request if missing."""
    if not idempotency_key or not idempotency_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Idempotency-Key header is required for this operation.",
            },
        )
    return idempotency_key.strip()


def get_optional_idempotency_key(
    idempotency_key: str | None = Header(
        None,
        alias="Idempotency-Key",
        description="Optional Idempotency-Key header.",
    ),
) -> str | None:
    """Return stripped Idempotency-Key if present, or None."""
    if idempotency_key and idempotency_key.strip():
        return idempotency_key.strip()
    return None
