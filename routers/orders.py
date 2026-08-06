"""Order placement and history tracking router endpoints."""

import logging
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    HTTPException,
    Path,
    status,
)
from sqlalchemy.orm import Session

from constants.app_constants import LOW_STOCK_THRESHOLD
from db.session import get_db
from dependencies.auth import get_current_user
from dependencies.idempotency import get_idempotency_key
from models import Cart, Order, OrderItem, User
from redis_client import redis_client
from services.idempotency_service import IdempotencyService, generate_request_hash
from services.order_service import create_order_from_cart
from tasks.email_tasks import (
    send_low_stock_alert,
    send_order_cancelled,
    send_order_confirmation,
    send_order_delivered,
    send_order_shipped,
    send_out_for_delivery,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/checkout",
    summary="Checkout Cart & Place Order",
    description="Convert items in authenticated user's cart into a new order record, decrement product stock, clear cart, and queue order confirmation email.",
    response_description="Created order payload summary",
    tags=["Orders"],
    responses={
        200: {"description": "Order placed successfully."},
        400: {"description": "Cart is empty or Idempotency-Key header is missing/invalid."},
        401: {"description": "Unauthorized."},
        409: {"description": "Concurrent request with this Idempotency-Key in progress."},
    },
)
def checkout(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    idempotency_key: str = Depends(get_idempotency_key),
) -> dict[str, Any]:
    """Process order checkout from user's current shopping cart with idempotency protection."""
    # Generate stable request hash for user checkout
    req_hash = generate_request_hash({"user_id": current_user.id, "endpoint": "/checkout"})

    # Check Idempotency Key first
    cached_response, _ = IdempotencyService.check_idempotency(
        db=db,
        idempotency_key=idempotency_key,
        endpoint="/checkout",
        request_hash=req_hash,
        user_id=current_user.id,
    )
    if cached_response:
        return cached_response

    try:
        result_payload = create_order_from_cart(
            db=db, current_user=current_user, background_tasks=background_tasks
        )

        # Save Idempotency response
        IdempotencyService.save_idempotency_response(
            db=db,
            idempotency_key=idempotency_key,
            status_code=200,
            response_body=result_payload,
            request_hash=req_hash,
        )

        return result_payload

    except Exception:
        IdempotencyService.mark_failed(db=db, idempotency_key=idempotency_key)
        raise



@router.get(
    "/orders",
    summary="Get Order History",
    description="Retrieve order placement history for current authenticated user (or all platform orders if user is Admin).",
    response_description="Array of order records with nested item details",
    tags=["Orders"],
    responses={
        200: {"description": "Order history retrieved successfully."},
        401: {"description": "Unauthorized."},
    },
)
@router.get("/all-orders", tags=["Orders"], include_in_schema=False)
def get_user_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Fetch order history for current user (or all orders if admin)."""
    if current_user.is_admin:
        orders = db.query(Order).order_by(Order.created_at.desc()).all()
    else:
        orders = (
            db.query(Order)
            .filter(Order.user_id == current_user.id)
            .order_by(Order.created_at.desc())
            .all()
        )

    order_response = []

    for order in orders:
        items = []
        for item in order.items:
            current_prod = item.product
            items.append(
                {
                    "product_id": item.product_id,
                    "product_title": current_prod.title if current_prod else "Product",
                    "price": current_prod.price if current_prod else 0,
                    "image": current_prod.image if current_prod else None,
                    "quantity": item.quantity,
                }
            )

        user_obj = order.user
        order_response.append(
            {
                "id": order.id,
                "order_id": order.id,
                "user_id": order.user_id,
                "username": user_obj.username if user_obj else "User",
                "user_email": user_obj.email if user_obj else "N/A",
                "total_price": order.total_price,
                "status": getattr(order, "status", "PROCESSING") or "PROCESSING",
                "created_at": order.created_at,
                "products": items,
                "items": items,
            }
        )

    return order_response


@router.put(
    "/orders/{order_id}/status",
    summary="Update Order Status",
    description="Update status of an existing order (PROCESSING, SHIPPED, OUT_FOR_DELIVERY, DELIVERED, CANCELLED) and queue status update email notification.",
    response_description="Updated order status object",
    tags=["Orders"],
    responses={
        200: {"description": "Order status updated."},
        404: {"description": "Order not found."},
    },
)
def update_order_status(
    order_id: int = Path(
        ..., title="Order ID", description="Target order ID", example=101
    ),
    background_tasks: BackgroundTasks = ...,
    status_str: str = Body(
        ...,
        embed=True,
        alias="status",
        description="New status string",
        example="SHIPPED",
    ),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Update order status and trigger customer email notifications."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Order not found"},
        )

    upper_status = status_str.upper().strip()
    order.status = upper_status
    db.commit()

    try:
        if upper_status == "SHIPPED":
            background_tasks.add_task(send_order_shipped, order.id)
        elif upper_status == "OUT_FOR_DELIVERY":
            background_tasks.add_task(send_out_for_delivery, order.id)
        elif upper_status == "DELIVERED":
            background_tasks.add_task(send_order_delivered, order.id)
        elif upper_status == "CANCELLED":
            background_tasks.add_task(send_order_cancelled, order.id)
    except Exception as e:
        logger.warning(f"[Order Status Email Queue Warning]: {e}")

    return {
        "success": True,
        "message": f"Order #{order_id} status updated to {upper_status}",
        "order_id": order.id,
        "status": upper_status,
    }
