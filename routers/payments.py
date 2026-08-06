"""Razorpay payment gateway integration router endpoints with idempotency support."""

import json
import logging
import os
from typing import Any

import razorpay
from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, Body, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from db.session import get_db
from dependencies.auth import get_current_user
from dependencies.idempotency import get_idempotency_key, get_optional_idempotency_key
from models import User
from schemas import OrderRequest, PaymentVerifyRequest
from services.idempotency_service import IdempotencyService, generate_request_hash
from services.order_service import create_order_from_cart

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter()

client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID", ""), os.getenv("RAZORPAY_KEY_SECRET", ""))
)
webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "default_webhook_secret")


@router.post(
    "/create-payment-order",
    summary="Create Razorpay Payment Order",
    description="Initialize a Razorpay payment order for online checkout and return the Razorpay order object (amount in paise). Idempotency-Key header is required.",
    response_description="Razorpay order payload",
    tags=["Payments"],
    responses={
        200: {"description": "Payment order initialized successfully."},
        400: {"description": "Idempotency-Key header missing or invalid request."},
        409: {"description": "Concurrent request with this Idempotency-Key in progress."},
    },
)
def create_payment_order(
    data: OrderRequest,
    db: Session = Depends(get_db),
    idempotency_key: str = Depends(get_idempotency_key),
) -> dict[str, Any]:
    """Create a new Razorpay payment order idempotently."""
    req_hash = generate_request_hash(data.model_dump() if hasattr(data, "model_dump") else data.dict())

    # Step 1: Check Idempotency Key
    cached_response, _ = IdempotencyService.check_idempotency(
        db=db,
        idempotency_key=idempotency_key,
        endpoint="/create-payment-order",
        request_hash=req_hash,
    )
    if cached_response:
        logger.info(f"[Payments] Returning previous Razorpay order for key: {idempotency_key}")
        return cached_response

    try:
        payment_order = client.order.create(
            {
                "amount": data.amount * 100,
                "currency": "INR",
                "payment_capture": 1,
            }
        )

        key_id = os.getenv("RAZORPAY_KEY_ID", "")
        response_payload = {
            "success": True,
            "razorpay_order_id": payment_order["id"],
            "amount": payment_order["amount"],
            "currency": payment_order["currency"],
            "key_id": key_id,
            "id": payment_order["id"],
        }

        # Save idempotency record
        IdempotencyService.save_idempotency_response(
            db=db,
            idempotency_key=idempotency_key,
            status_code=200,
            response_body=response_payload,
            request_hash=req_hash,
        )

        return response_payload
    except Exception as e:
        logger.error(f"Error creating Razorpay payment order: {e}")
        IdempotencyService.mark_failed(db=db, idempotency_key=idempotency_key)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": f"Payment order creation failed: {str(e)}"},
        )


@router.post(
    "/verify-payment",
    summary="Verify Razorpay Payment Signature & Complete Order",
    description="Verify HMAC SHA256 digital signature of a completed Razorpay payment transaction. Only after successful signature verification is the order created in the database.",
    response_description="Payment verification and order creation status result",
    tags=["Payments"],
    responses={
        200: {"description": "Payment signature verified and order created successfully."},
        400: {"description": "Invalid Razorpay payment signature or missing parameters."},
    },
)
def verify_payment(
    background_tasks: BackgroundTasks,
    payload: PaymentVerifyRequest | None = Body(None),
    razorpay_order_id: str | None = Query(None),
    razorpay_payment_id: str | None = Query(None),
    razorpay_signature: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    idempotency_key: str | None = Depends(get_optional_idempotency_key),
) -> dict[str, Any]:
    """Verify signature of a completed Razorpay payment transaction and create order."""
    order_id = (payload.razorpay_order_id if payload else None) or razorpay_order_id
    payment_id = (payload.razorpay_payment_id if payload else None) or razorpay_payment_id
    signature = (payload.razorpay_signature if payload else None) or razorpay_signature

    if not order_id or not payment_id or not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Missing required Razorpay payment verification parameters.",
            },
        )

    effective_key = idempotency_key or f"verify:{order_id}:{payment_id}"
    params_dict = {
        "order_id": order_id,
        "payment_id": payment_id,
        "signature": signature,
        "user_id": current_user.id,
    }
    req_hash = generate_request_hash(params_dict)

    cached_response, _ = IdempotencyService.check_idempotency(
        db=db,
        idempotency_key=effective_key,
        endpoint="/verify-payment",
        request_hash=req_hash,
        user_id=current_user.id,
    )
    if cached_response:
        return cached_response

    # Verify Razorpay HMAC signature
    try:
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }
        )
    except Exception as e:
        logger.error(f"[Razorpay Signature Verification Failed]: {e}")
        IdempotencyService.mark_failed(db=db, idempotency_key=effective_key)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Payment verification failed. Invalid Razorpay signature.",
            },
        )

    # Signature is VALID -> Create order in DB and clear user cart
    try:
        order_res = create_order_from_cart(
            db=db, current_user=current_user, background_tasks=background_tasks
        )

        res_payload = {
            "success": True,
            "message": "Payment verified and order placed successfully",
            "order_id": order_res["order_id"],
            "total_price": order_res["total_price"],
            "status": order_res["status"],
            "razorpay_payment_id": payment_id,
            "razorpay_order_id": order_id,
        }

        IdempotencyService.save_idempotency_response(
            db=db,
            idempotency_key=effective_key,
            status_code=200,
            response_body=res_payload,
            request_hash=req_hash,
        )

        return res_payload

    except HTTPException:
        IdempotencyService.mark_failed(db=db, idempotency_key=effective_key)
        raise
    except Exception as exc:
        logger.error(f"Error completing order after payment verification: {exc}")
        IdempotencyService.mark_failed(db=db, idempotency_key=effective_key)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": f"Order placement failed: {str(exc)}"},
        )


@router.post(
    "/webhooks/razorpay",
    summary="Handle Razorpay Webhooks",
    description="Idempotent webhook endpoint for processing Razorpay event notifications.",
    tags=["Payments"],
)
async def handle_razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: str | None = Header(None, alias="X-Razorpay-Signature"),
) -> dict[str, Any]:
    """Process incoming Razorpay webhook events idempotently."""
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")

    # Optional Razorpay webhook signature verification
    if x_razorpay_signature and webhook_secret and webhook_secret != "default_webhook_secret":
        try:
            client.utility.verify_webhook_signature(
                body_str, x_razorpay_signature, webhook_secret
            )
        except Exception as e:
            logger.warning(f"[Webhook] Signature verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "Invalid webhook signature"},
            )

    try:
        payload = json.loads(body_str) if body_str else {}
    except Exception:
        payload = {}

    # Extract unique Event ID or construct key from entity ID
    event_id = payload.get("event_id") or payload.get("id")
    if not event_id:
        payment_entity = (
            payload.get("payload", {})
            .get("payment", {})
            .get("entity", {})
        )
        payment_id = payment_entity.get("id", "unknown")
        event_type = payload.get("event", "event")
        event_id = f"webhook:{event_type}:{payment_id}"

    idempotency_key = f"razorpay_webhook:{event_id}"
    req_hash = generate_request_hash(payload)

    # Check if duplicate webhook
    cached_response, _ = IdempotencyService.check_idempotency(
        db=db,
        idempotency_key=idempotency_key,
        endpoint="/webhooks/razorpay",
        request_hash=req_hash,
    )
    if cached_response:
        logger.info(f"[Webhook] Duplicate Razorpay webhook ignored for key: {idempotency_key}")
        return cached_response

    event_name = payload.get("event", "unknown")
    logger.info(f"[Webhook] Processing new Razorpay event '{event_name}' (Key: {idempotency_key})")

    res_payload = {
        "status": "success",
        "message": f"Webhook event '{event_name}' processed successfully",
        "event_id": event_id,
    }

    IdempotencyService.save_idempotency_response(
        db=db,
        idempotency_key=idempotency_key,
        status_code=200,
        response_body=res_payload,
        request_hash=req_hash,
    )

    return res_payload
