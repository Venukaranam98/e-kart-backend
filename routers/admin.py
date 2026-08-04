"""Administrative management and store dashboard router endpoints."""

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

from db.session import get_db
from dependencies.auth import get_current_admin
from models import Address, Order, Product, User
from tasks.email_tasks import (
    send_order_cancelled,
    send_order_delivered,
    send_order_shipped,
    send_out_for_delivery,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/dashboard",
    summary="Get Admin Dashboard Metrics (Admin Only)",
    description="Retrieve system overview statistics: total registered users, catalog products count, total order volume, and total platform revenue. Requires Admin JWT authorization.",
    response_description="Dashboard metrics object",
    tags=["Admin"],
    responses={
        200: {"description": "Dashboard overview statistics."},
        401: {"description": "Unauthorized."},
        403: {"description": "Forbidden: Requires Admin privileges."},
    },
)
def admin_dashboard(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> dict[str, Any]:
    """Return high-level administration overview metrics."""
    total_users = db.query(User).count()
    total_products = db.query(Product).count()
    total_orders = db.query(Order).count()
    total_revenue = sum((order.total_price or 0) for order in db.query(Order).all())

    return {
        "total_users": total_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
    }


def _build_orders_list(db: Session) -> list[dict[str, Any]]:
    """Helper method to format all customer orders for admin views."""
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    orders_list = []
    for order in orders:
        items = []
        for item in order.items:
            prod = item.product
            items.append(
                {
                    "product_id": item.product_id,
                    "product_title": prod.title if prod else "Product",
                    "price": prod.price if prod else 0,
                    "image": prod.image if prod else None,
                    "quantity": item.quantity,
                }
            )

        user_obj = order.user
        addr_obj = db.query(Address).filter(Address.user_id == order.user_id).first()
        address_str = (
            f"{addr_obj.full_name}, {addr_obj.address_line}, {addr_obj.city}, {addr_obj.state} - {addr_obj.pincode}"
            if addr_obj
            else "No shipping address provided"
        )

        orders_list.append(
            {
                "id": order.id,
                "order_id": order.id,
                "user_id": order.user_id,
                "user_name": user_obj.username if user_obj else "Unknown User",
                "user_email": user_obj.email if user_obj else "N/A",
                "total_price": order.total_price,
                "status": getattr(order, "status", "PROCESSING") or "PROCESSING",
                "shipping_address": address_str,
                "created_at": order.created_at,
                "products": items,
                "items": items,
            }
        )
    return orders_list


@router.get(
    "/orders",
    summary="List All Orders (Admin Only)",
    description="Retrieve all customer orders across the platform with shipping address and user details. Requires Admin authorization.",
    response_description="Array of all platform orders",
    tags=["Admin"],
    responses={
        200: {"description": "List of all customer orders."},
        401: {"description": "Unauthorized."},
        403: {"description": "Forbidden: Requires Admin privileges."},
    },
)
@router.get("/all-orders", tags=["Admin"], include_in_schema=False)
def get_all_orders(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> list[dict[str, Any]]:
    """Fetch all customer orders for store administrator."""
    return _build_orders_list(db)


@router.put(
    "/orders/{order_id}/status",
    summary="Update Customer Order Status (Admin Only)",
    description="Update fulfillment status of any customer order (PROCESSING, SHIPPED, OUT_FOR_DELIVERY, DELIVERED, CANCELLED) and trigger automated email notification.",
    response_description="Status update confirmation",
    tags=["Admin"],
    responses={
        200: {"description": "Order status updated."},
        401: {"description": "Unauthorized."},
        403: {"description": "Forbidden: Requires Admin privileges."},
        404: {"description": "Order not found."},
    },
)
def update_admin_order_status(
    order_id: int = Path(
        ..., title="Order ID", description="Target order ID", example=101
    ),
    background_tasks: BackgroundTasks = ...,
    status_str: str = Body(
        ...,
        embed=True,
        alias="status",
        description="Target status string",
        example="SHIPPED",
    ),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> dict[str, Any]:
    """Update order fulfillment status and queue customer status notification email."""
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
        logger.warning(f"[Admin Order Status Email Warning]: {e}")

    return {
        "success": True,
        "message": f"Order #{order_id} status updated to {upper_status}",
        "order_id": order.id,
        "status": upper_status,
    }


@router.get(
    "/users",
    summary="List All Users (Admin Only)",
    description="Retrieve all registered user accounts with administrative status and registration timestamp. Requires Admin privileges.",
    response_description="Array of user objects",
    tags=["Admin"],
    responses={
        200: {"description": "List of user accounts."},
        401: {"description": "Unauthorized."},
        403: {"description": "Forbidden: Requires Admin privileges."},
    },
)
def get_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> list[dict[str, Any]]:
    """Fetch all registered user accounts for store administrator."""
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "created_at": user.created_at,
        }
        for user in users
    ]
