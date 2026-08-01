from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from database import get_db
from models import (
    User,
    Product,
    Order,
    Address
)
from routers.auth import get_current_admin
from tasks.email_tasks import (
    send_order_shipped,
    send_out_for_delivery,
    send_order_delivered,
    send_order_cancelled,
    dispatch_email_task
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

@router.get("/dashboard")
def admin_dashboard(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    total_users = db.query(User).count()
    total_products = db.query(Product).count()
    total_orders = db.query(Order).count()
    total_revenue = sum(
        (order.total_price or 0)
        for order in db.query(Order).all()
    )

    return {
        "total_users": total_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": total_revenue
    }

def _build_orders_list(db: Session):
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    orders_list = []
    for order in orders:
        items = []
        for item in order.items:
            prod = item.product
            items.append({
                "product_id": item.product_id,
                "product_title": prod.title if prod else "Product",
                "price": prod.price if prod else 0,
                "image": prod.image if prod else None,
                "quantity": item.quantity
            })

        user_obj = order.user
        addr_obj = db.query(Address).filter(Address.user_id == order.user_id).first()
        address_str = f"{addr_obj.full_name}, {addr_obj.address_line}, {addr_obj.city}, {addr_obj.state} - {addr_obj.pincode}" if addr_obj else "No shipping address provided"

        orders_list.append({
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
            "items": items
        })
    return orders_list

@router.get("/orders")
@router.get("/all-orders")
def get_all_orders(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    return _build_orders_list(db)

@router.put("/orders/{order_id}/status")
def update_admin_order_status(
    order_id: int,
    status: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "message": "Order not found"}
        )

    upper_status = status.upper().strip()
    order.status = upper_status
    db.commit()

    # Trigger corresponding status email tasks
    try:
        if upper_status == "SHIPPED":
            dispatch_email_task(send_order_shipped, order.id)
        elif upper_status == "OUT_FOR_DELIVERY":
            dispatch_email_task(send_out_for_delivery, order.id)
        elif upper_status == "DELIVERED":
            dispatch_email_task(send_order_delivered, order.id)
        elif upper_status == "CANCELLED":
            dispatch_email_task(send_order_cancelled, order.id)
    except Exception as e:
        print("[Admin Order Status Email Warning]:", e)

    return {
        "success": True,
        "message": f"Order #{order_id} status updated to {upper_status}",
        "order_id": order.id,
        "status": upper_status
    }

@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "created_at": user.created_at
        }
        for user in users
    ]