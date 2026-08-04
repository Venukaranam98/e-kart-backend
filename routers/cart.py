"""Shopping cart router endpoints for managing cart items."""

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from dependencies.auth import get_current_user
from models import Cart, Product, User
from redis_client import redis_client
from schemas import CartSchema, UpdateCartSchema

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/cart", tags=["Cart"])
def add_to_cart(
    cart: CartSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Add a product to current user's shopping cart."""
    product_exists = db.query(Product).filter(Product.id == cart.product_id).first()
    if not product_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Product not found"},
        )

    existing_cart_item = (
        db.query(Cart)
        .filter(
            Cart.user_id == current_user.id,
            Cart.product_id == cart.product_id,
        )
        .first()
    )

    if existing_cart_item:
        existing_cart_item.quantity += cart.quantity
        db.commit()
        db.refresh(existing_cart_item)
        redis_client.delete(f"cart:user:{current_user.id}")

        return {
            "success": True,
            "message": "Cart quantity updated successfully",
            "data": {
                "cart_id": existing_cart_item.id,
                "product_id": existing_cart_item.product_id,
                "quantity": existing_cart_item.quantity,
            },
        }

    new_cart_item = Cart(
        quantity=cart.quantity,
        user_id=current_user.id,
        product_id=cart.product_id,
    )
    db.add(new_cart_item)
    db.commit()
    db.refresh(new_cart_item)
    redis_client.delete(f"cart:user:{current_user.id}")

    return {
        "success": True,
        "message": "Product added to cart",
        "data": {
            "cart_id": new_cart_item.id,
            "product_id": new_cart_item.product_id,
            "quantity": new_cart_item.quantity,
        },
    }


@router.get("/cart", tags=["Cart"])
def get_user_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Fetch all cart items for current authenticated user with Redis caching."""
    cache_key = f"cart:user:{current_user.id}"
    cached_cart = redis_client.get(cache_key)

    if cached_cart:
        logger.info("Cart cache hit")
        return json.loads(cached_cart)

    logger.info("Cart cache miss")
    cart_items = db.query(Cart).filter(Cart.user_id == current_user.id).all()

    cart_response = []
    for item in cart_items:
        cart_response.append(
            {
                "cart_id": item.id,
                "product_title": item.product.title,
                "price": item.product.price,
                "image": item.product.image,
                "category": item.product.category,
                "quantity": item.quantity,
            }
        )

    response = {
        "success": True,
        "message": "Cart fetched successfully",
        "data": cart_response,
    }

    redis_client.set(cache_key, json.dumps(response), ex=3600)
    return response


@router.delete("/cart/clear", tags=["Cart"])
def clear_user_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Remove all items from current user's shopping cart."""
    db.query(Cart).filter(Cart.user_id == current_user.id).delete(
        synchronize_session=False
    )
    db.commit()

    try:
        redis_client.delete(f"cart:user:{current_user.id}")
    except Exception as e:
        logger.warning(f"Redis cache delete error: {e}")

    return {
        "success": True,
        "message": "Cart cleared successfully",
        "data": [],
    }


@router.delete("/cart/{cart_id}", tags=["Cart"])
def remove_from_cart(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Remove a specific item from cart by cart ID."""
    cart_item = (
        db.query(Cart)
        .filter(Cart.id == cart_id, Cart.user_id == current_user.id)
        .first()
    )

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Cart item not found"},
        )

    db.delete(cart_item)
    db.commit()
    redis_client.delete(f"cart:user:{current_user.id}")

    return {"success": True, "message": "Item removed from cart"}


@router.put("/cart/{cart_id}", tags=["Cart"])
def update_cart_quantity(
    cart_id: int,
    updated_cart: UpdateCartSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Update quantity of a specific cart item."""
    cart_item = (
        db.query(Cart)
        .filter(Cart.id == cart_id, Cart.user_id == current_user.id)
        .first()
    )

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Cart item not found"},
        )

    cart_item.quantity = updated_cart.quantity
    db.commit()
    db.refresh(cart_item)
    redis_client.delete(f"cart:user:{current_user.id}")

    return {
        "success": True,
        "message": "Cart quantity updated successfully",
        "data": {"cart_id": cart_item.id, "quantity": cart_item.quantity},
    }
