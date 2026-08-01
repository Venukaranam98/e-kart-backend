from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
import os

from database import get_db
from models import (
    Cart,
    Order,
    OrderItem,
    User,
    Product
)
from routers.auth import get_current_user
from tasks.email_tasks import (
    send_order_confirmation,
    send_order_shipped,
    send_out_for_delivery,
    send_order_delivered,
    send_order_cancelled,
    send_low_stock_alert
)

LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", "5"))

router = APIRouter()

@router.post(
    "/checkout",
    tags=["Orders"]
)
def checkout(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):
    cart_items = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).all()

    if not cart_items:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "Cart is empty. Please add items to your cart before checking out."
            }
        )


    total_price = 0
    for item in cart_items:
        total_price += (item.product.price * item.quantity)

    new_order = Order(
        user_id=current_user.id,
        total_price=total_price,
        status="PROCESSING"
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    for item in cart_items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(order_item)

        # Decrement stock and check low stock threshold
        prod = item.product
        if prod and hasattr(prod, "stock") and prod.stock is not None:
            prod.stock = max(0, prod.stock - item.quantity)
            db.commit()
            if prod.stock < LOW_STOCK_THRESHOLD:
                try:
                    send_low_stock_alert.delay(prod.id, prod.title, prod.stock)
                except Exception as e:
                    print("[Low Stock Alert Warning]:", e)

    db.commit()

    db.query(Cart).filter(Cart.user_id == current_user.id).delete(synchronize_session=False)
    db.commit()

    try:
        from redis_client import redis_client
        redis_client.delete(f"cart:user:{current_user.id}")
    except Exception as e:
        print("Redis cache clear warning:", e)

    # Queue order confirmation email asynchronously
    try:
        send_order_confirmation.delay(new_order.id)
    except Exception as e:
        print("[Order Confirmation Email Queue Warning]:", e)

    return {
        "message": "Order placed successfully",
        "order_id": new_order.id,
        "total_price": total_price,
        "status": "PROCESSING"
    }

@router.get(
    "/orders",
    tags=["Orders"]
)
@router.get(
    "/all-orders",
    tags=["Orders"]
)
def get_user_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):
    if current_user.is_admin:
        orders = db.query(Order).order_by(Order.created_at.desc()).all()
    else:
        orders = db.query(Order).filter(
            Order.user_id == current_user.id
        ).order_by(Order.created_at.desc()).all()

    order_response = []

    for order in orders:
        items = []
        for item in order.items:
            current_prod = item.product
            items.append({
                "product_id": item.product_id,
                "product_title": current_prod.title if current_prod else "Product",
                "price": current_prod.price if current_prod else 0,
                "image": current_prod.image if current_prod else None,
                "quantity": item.quantity
            })

        user_obj = order.user
        order_response.append({
            "id": order.id,
            "order_id": order.id,
            "user_id": order.user_id,
            "username": user_obj.username if user_obj else "User",
            "user_email": user_obj.email if user_obj else "N/A",
            "total_price": order.total_price,
            "status": getattr(order, "status", "PROCESSING") or "PROCESSING",
            "created_at": order.created_at,
            "products": items,
            "items": items
        })

    return order_response


@router.put(
    "/orders/{order_id}/status",
    tags=["Orders"]
)
def update_order_status(
    order_id: int,
    status: str = Body(..., embed=True),
    db: Session = Depends(get_db)
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
            send_order_shipped.delay(order.id)
        elif upper_status == "OUT_FOR_DELIVERY":
            send_out_for_delivery.delay(order.id)
        elif upper_status == "DELIVERED":
            send_order_delivered.delay(order.id)
        elif upper_status == "CANCELLED":
            send_order_cancelled.delay(order.id)
    except Exception as e:
        print("[Order Status Email Queue Warning]:", e)

    return {
        "success": True,
        "message": f"Order #{order_id} status updated to {upper_status}",
        "order_id": order.id,
        "status": upper_status
    }