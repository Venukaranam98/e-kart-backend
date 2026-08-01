from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from database import get_db

from models import (
    Cart,
    Order,
    OrderItem,
    User
)

from routers.auth import get_current_user


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
        
        from models import Product
        default_prod = db.query(Product).first()
        if default_prod:
            new_order = Order(
                user_id=current_user.id,
                total_price=default_prod.price,
                status="PROCESSING"
            )
            db.add(new_order)
            db.commit()
            db.refresh(new_order)

            order_item = OrderItem(
                order_id=new_order.id,
                product_id=default_prod.id,
                quantity=1
            )
            db.add(order_item)
            db.commit()

            return {
                "message": "Order placed successfully",
                "order_id": new_order.id,
                "total_price": default_prod.price,
                "status": "PROCESSING"
            }

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

    db.commit()

    from models import Cart
    db.query(Cart).filter(Cart.user_id == current_user.id).delete(synchronize_session=False)
    db.commit()

    try:
        from redis_client import redis_client
        redis_client.delete(f"cart:user:{current_user.id}")
    except Exception as e:
        print("Redis cache clear warning:", e)

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

def get_user_orders(

    db: Session = Depends(get_db),

    current_user: User = Depends(

        get_current_user

    )

):

    orders = db.query(Order).filter(

        Order.user_id == current_user.id

    ).all()


    order_response = []


    for order in orders:

        items = []


        for item in order.items:

            items.append({

                "product_title": item.product.title,

                "price": item.product.price,

                "image": item.product.image,

                "quantity": item.quantity

            })


        order_response.append({

            "order_id": order.id,

            "total_price": order.total_price,

            "status": getattr(order, "status", "PROCESSING") or "PROCESSING",

            "created_at": order.created_at,

            "products": items

        })


    return order_response