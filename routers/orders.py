"""Order placement and history tracking router endpoints."""

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from constants.app_constants import LOW_STOCK_THRESHOLD
from db.session import get_db
from dependencies.auth import get_current_user
from models import Cart, Order, OrderItem, User
from redis_client import redis_client
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


@router.post("/checkout", tags=["Orders"])
def checkout(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Process order checkout from user's current shopping cart."""
    cart_items = db.query(Cart).filter(Cart.user_id == current_user.id).all()

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Cart is empty. Please add items to your cart before checking out.",
            },
        )

    total_price = sum(item.product.price * item.quantity for item in cart_items)

    new_order = Order(
        user_id=current_user.id,
        total_price=total_price,
        status="PROCESSING",
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    for item in cart_items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
        )
        db.add(order_item)

        prod = item.product
        if prod and hasattr(prod, "stock") and prod.stock is not None:
            prod.stock = max(0, prod.stock - item.quantity)
            db.commit()
            if prod.stock < LOW_STOCK_THRESHOLD:
                try:
                    background_tasks.add_task(
                        send_low_stock_alert, prod.id, prod.title, prod.stock
                    )
                except Exception as e:
                    logger.warning(f"[Low Stock Alert Warning]: {e}")

    db.commit()

    db.query(Cart).filter(Cart.user_id == current_user.id).delete(
        synchronize_session=False
    )
    db.commit()

    try:
        redis_client.delete(f"cart:user:{current_user.id}")
    except Exception as e:
        logger.warning(f"Redis cache clear warning: {e}")

    try:
        background_tasks.add_task(send_order_confirmation, new_order.id)
    except Exception as e:
        logger.warning(f"[Order Confirmation Email Queue Warning]: {e}")

    return {
        "message": "Order placed successfully",
        "order_id": new_order.id,
        "total_price": total_price,
        "status": "PROCESSING",
    }


@router.get("/orders", tags=["Orders"])
@router.get("/all-orders", tags=["Orders"])
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


@router.put("/orders/{order_id}/status", tags=["Orders"])
def update_order_status(
    order_id: int,
    background_tasks: BackgroundTasks,
    status_str: str = Body(..., embed=True, alias="status"),
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
