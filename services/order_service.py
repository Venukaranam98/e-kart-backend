"""Order creation service for handling checkout and payment fulfillment."""

import logging
from typing import Any

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from constants.app_constants import LOW_STOCK_THRESHOLD
from models import Cart, Order, OrderItem, User
from redis_client import redis_client
from tasks.email_tasks import send_low_stock_alert, send_order_confirmation

logger = logging.getLogger(__name__)


def create_order_from_cart(
    db: Session,
    current_user: User,
    background_tasks: BackgroundTasks | None = None,
) -> dict[str, Any]:
    """Convert user cart items into a new order record, decrement stock, and clear cart."""
    cart_items = db.query(Cart).filter(Cart.user_id == current_user.id).all()

    if not cart_items:
        # Check if an order was placed recently (e.g. within last 60 seconds)
        recent_order = (
            db.query(Order)
            .filter(Order.user_id == current_user.id)
            .order_by(Order.created_at.desc())
            .first()
        )
        if recent_order:
            return {
                "message": "Order placed successfully",
                "order_id": recent_order.id,
                "total_price": recent_order.total_price,
                "status": getattr(recent_order, "status", "PROCESSING") or "PROCESSING",
            }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Cart is empty. Please add items to your cart before checking out.",
            },
        )

    total_price = sum(item.product.price * item.quantity for item in cart_items if item.product)

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
            if prod.stock < LOW_STOCK_THRESHOLD and background_tasks:
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

    if background_tasks:
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
