"""Shopping cart router endpoints for managing cart items."""

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from db.session import get_db
from dependencies.auth import get_current_user
from models import Cart, Product, User
from redis_client import redis_client
from schemas import CartSchema, UpdateCartSchema

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/cart",
    summary="Add Product to Cart",
    description="Add a product item to the authenticated user's cart or increment quantity if already added.",
    response_description="Created or updated cart item details",
    tags=["Cart"],
    responses={
        200: {"description": "Product added to cart or quantity updated."},
        401: {"description": "Unauthorized."},
        404: {"description": "Product not found."},
    },
)
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


@router.get(
    "/cart",
    summary="Get User Cart Items",
    description="Retrieve all cart items for the authenticated user. Utilizes Redis caching.",
    response_description="Array of cart items with product metadata",
    tags=["Cart"],
    responses={
        200: {"description": "Cart items array retrieved successfully."},
        401: {"description": "Unauthorized."},
    },
)
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


@router.delete(
    "/cart/clear",
    summary="Clear Entire Cart",
    description="Remove all items from authenticated user's cart and invalidate Redis cache.",
    response_description="Empty cart array confirmation",
    tags=["Cart"],
    responses={
        200: {"description": "Cart cleared successfully."},
        401: {"description": "Unauthorized."},
    },
)
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


@router.delete(
    "/cart/{cart_id}",
    summary="Remove Single Cart Item",
    description="Delete a specific cart item by ID from user's shopping cart.",
    response_description="Removal confirmation message",
    tags=["Cart"],
    responses={
        200: {"description": "Item removed from cart."},
        401: {"description": "Unauthorized."},
        404: {"description": "Cart item not found."},
    },
)
def remove_from_cart(
    cart_id: int = Path(
        ..., title="Cart Item ID", description="Cart item ID to remove", example=10
    ),
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


@router.put(
    "/cart/{cart_id}",
    summary="Update Cart Item Quantity",
    description="Update quantity count for a specific item in user's cart.",
    response_description="Updated cart item payload",
    tags=["Cart"],
    responses={
        200: {"description": "Cart quantity updated successfully."},
        401: {"description": "Unauthorized."},
        404: {"description": "Cart item not found."},
    },
)
def update_cart_quantity(
    cart_id: int = Path(
        ..., title="Cart Item ID", description="Cart item ID to update", example=10
    ),
    updated_cart: UpdateCartSchema = ...,
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
