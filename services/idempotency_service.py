"""Production-grade Idempotency Service module for E-Kart backend."""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from constants.app_constants import IDEMPOTENCY_EXPIRE_HOURS
from models import IdempotencyRecord
from redis_client import redis_client

logger = logging.getLogger(__name__)


def generate_request_hash(data: Any) -> str:
    """Generate SHA256 hash string for request payload data."""
    if data is None:
        raw_str = ""
    elif isinstance(data, str):
        raw_str = data
    elif isinstance(data, dict | list):
        raw_str = json.dumps(data, sort_keys=True)
    else:
        raw_str = str(data)
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


class IdempotencyService:
    """Service class managing Redis + DB idempotency workflow and concurrency locks."""

    @staticmethod
    def get_redis_key(key: str) -> str:
        return f"idempotency:{key}"

    @staticmethod
    def get_lock_key(key: str) -> str:
        return f"idempotency:lock:{key}"

    @classmethod
    def check_idempotency(
        cls,
        db: Session,
        idempotency_key: str,
        endpoint: str,
        request_hash: str,
        user_id: int | None = None,
    ) -> tuple[JSONResponse | None, IdempotencyRecord | None]:
        """Check if request was already processed via Redis/DB cache.

        Returns (JSONResponse, None) if cached completed response exists.
        Returns (None, IdempotencyRecord) if key is new and lock successfully acquired.
        Raises 409 Conflict if request with same key is currently processing.
        Raises 400 Bad Request if key exists with different payload hash.
        """
        redis_cache_key = cls.get_redis_key(idempotency_key)

        # Step 1: Redis Fast Cache Lookup
        cached_raw = redis_client.get(redis_cache_key)
        if cached_raw:
            try:
                cached_data = json.loads(cached_raw)
                if cached_data.get("request_hash") != request_hash:
                    logger.warning(
                        f"[Idempotency] Payload mismatch in Redis for key {idempotency_key}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "success": False,
                            "message": "Idempotency-Key payload mismatch. This key was previously used with a different payload.",
                        },
                    )

                if cached_data.get("status") == "COMPLETED":
                    logger.info(
                        f"[Idempotency] Cache HIT (Redis) for key: {idempotency_key}"
                    )
                    return (
                        JSONResponse(
                            status_code=cached_data.get("response_status", 200),
                            content=cached_data.get("response_body"),
                        ),
                        None,
                    )
                elif cached_data.get("status") == "PROCESSING":
                    logger.warning(
                        f"[Idempotency] Concurrent request detected (Redis) for key: {idempotency_key}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "success": False,
                            "message": "Concurrent request with this Idempotency-Key is currently in progress. Please wait.",
                        },
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"[Idempotency] Error parsing Redis payload: {e}")

        # Step 2: Database Fallback Query
        existing_record = (
            db.query(IdempotencyRecord)
            .filter(IdempotencyRecord.idempotency_key == idempotency_key)
            .first()
        )

        if existing_record:
            # Check expiration
            if existing_record.expires_at < datetime.utcnow():
                logger.info(
                    f"[Idempotency] Key expired in DB: {idempotency_key}. Cleaning up."
                )
                db.delete(existing_record)
                db.commit()
                existing_record = None
            else:
                if existing_record.request_hash != request_hash:
                    logger.warning(
                        f"[Idempotency] Payload mismatch in DB for key: {idempotency_key}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "success": False,
                            "message": "Idempotency-Key payload mismatch. This key was previously used with a different payload.",
                        },
                    )

                if existing_record.status == "COMPLETED":
                    logger.info(
                        f"[Idempotency] Database HIT for key: {idempotency_key}. Re-populating Redis."
                    )
                    body_json = {}
                    if existing_record.response_body:
                        try:
                            body_json = json.loads(existing_record.response_body)
                        except Exception:
                            body_json = {"detail": existing_record.response_body}

                    # Populate Redis for future requests
                    ttl_seconds = int(IDEMPOTENCY_EXPIRE_HOURS * 3600)
                    redis_client.set(
                        redis_cache_key,
                        json.dumps(
                            {
                                "status": "COMPLETED",
                                "response_status": existing_record.response_status,
                                "response_body": body_json,
                                "request_hash": request_hash,
                            }
                        ),
                        ex=ttl_seconds,
                    )

                    return (
                        JSONResponse(
                            status_code=existing_record.response_status or 200,
                            content=body_json,
                        ),
                        None,
                    )

                elif existing_record.status == "PROCESSING":
                    logger.warning(
                        f"[Idempotency] Duplicate concurrent request detected in DB for key: {idempotency_key}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "success": False,
                            "message": "Concurrent request with this Idempotency-Key is currently in progress. Please wait.",
                        },
                    )

        # Step 3: Key is new -> Register request lock in DB & Redis
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=IDEMPOTENCY_EXPIRE_HOURS)

        new_record = IdempotencyRecord(
            idempotency_key=idempotency_key,
            user_id=user_id,
            endpoint=endpoint,
            request_hash=request_hash,
            status="PROCESSING",
            created_at=now,
            expires_at=expires_at,
        )

        try:
            db.add(new_record)
            db.commit()
            db.refresh(new_record)
        except IntegrityError:
            db.rollback()
            logger.warning(
                f"[Idempotency] DB IntegrityError (Concurrency race) for key: {idempotency_key}"
            )
            # Another concurrent request inserted the key simultaneously
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "Concurrent request with this Idempotency-Key is currently in progress. Please wait.",
                },
            )

        # Save processing state to Redis
        redis_client.set(
            redis_cache_key,
            json.dumps({"status": "PROCESSING", "request_hash": request_hash}),
            ex=300,  # 5 min lock TTL while processing
        )
        logger.info(
            f"[Idempotency] Key received and registered for execution: {idempotency_key}"
        )

        return None, new_record

    @classmethod
    def save_idempotency_response(
        cls,
        db: Session,
        idempotency_key: str,
        status_code: int,
        response_body: dict[str, Any] | list[Any],
        request_hash: str,
    ) -> None:
        """Store final response in DB & Redis after successful execution."""
        record = (
            db.query(IdempotencyRecord)
            .filter(IdempotencyRecord.idempotency_key == idempotency_key)
            .first()
        )

        serialized_body = json.dumps(response_body)

        if record:
            record.status = "COMPLETED"
            record.response_status = status_code
            record.response_body = serialized_body
            db.commit()

        # Update Redis with 24-hour expiration
        redis_cache_key = cls.get_redis_key(idempotency_key)
        ttl_seconds = int(IDEMPOTENCY_EXPIRE_HOURS * 3600)
        redis_client.set(
            redis_cache_key,
            json.dumps(
                {
                    "status": "COMPLETED",
                    "response_status": status_code,
                    "response_body": response_body,
                    "request_hash": request_hash,
                }
            ),
            ex=ttl_seconds,
        )

        logger.info(
            f"[Idempotency] Request completed and stored for key: {idempotency_key}"
        )

    @classmethod
    def mark_failed(
        cls,
        db: Session,
        idempotency_key: str,
    ) -> None:
        """Clear/remove key on unhandled execution error so client can retry."""
        try:
            record = (
                db.query(IdempotencyRecord)
                .filter(IdempotencyRecord.idempotency_key == idempotency_key)
                .first()
            )
            if record and record.status == "PROCESSING":
                db.delete(record)
                db.commit()
            redis_client.delete(cls.get_redis_key(idempotency_key))
            logger.info(
                f"[Idempotency] Cleared failed idempotency key: {idempotency_key}"
            )
        except Exception as e:
            logger.warning(
                f"[Idempotency] Error marking key as failed: {idempotency_key}: {e}"
            )
