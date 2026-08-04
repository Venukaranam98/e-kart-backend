"""Wishlist router endpoints for managing saved products."""

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from dependencies.auth import get_current_user
from models import Product, User, Wishlist
from redis_client import redis_client
from schemas import WishlistSchema

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/wishlist", tags=["Wishlist"])
def add_to_wishlist(
    wishlist: WishlistSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Add a product to current user's wishlist."""
    product_exists = db.query(Product).filter(Product.id == wishlist.product_id).first()
    if not product_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Product not found"},
        )

    existing_wishlist_item = (
        db.query(Wishlist)
        .filter(
            Wishlist.user_id == current_user.id,
            Wishlist.product_id == wishlist.product_id,
        )
        .first()
    )

    if existing_wishlist_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Product already in wishlist"},
        )

    new_wishlist_item = Wishlist(
        user_id=current_user.id, product_id=wishlist.product_id
    )
    db.add(new_wishlist_item)
    db.commit()
    db.refresh(new_wishlist_item)

    redis_client.delete(f"wishlist:user:{current_user.id}")

    return {
        "success": True,
        "message": "Product added to wishlist",
        "data": {
            "wishlist_id": new_wishlist_item.id,
            "product_id": new_wishlist_item.product_id,
        },
    }


@router.get("/wishlist", tags=["Wishlist"])
def get_user_wishlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Fetch all wishlist items for current user with Redis caching."""
    cache_key = f"wishlist:user:{current_user.id}"
    cached_wishlist = redis_client.get(cache_key)

    if cached_wishlist:
        logger.info("Wishlist cache hit")
        return json.loads(cached_wishlist)

    logger.info("Wishlist cache miss")
    wishlist_items = (
        db.query(Wishlist).filter(Wishlist.user_id == current_user.id).all()
    )

    wishlist_response = []
    for item in wishlist_items:
        wishlist_response.append(
            {
                "wishlist_id": item.id,
                "product_id": item.product.id,
                "product_title": item.product.title,
                "price": item.product.price,
                "image": item.product.image,
                "category": item.product.category,
            }
        )

    response = {
        "success": True,
        "message": "Wishlist fetched successfully",
        "data": wishlist_response,
    }

    redis_client.set(cache_key, json.dumps(response), ex=3600)
    return response


@router.delete("/wishlist/{wishlist_id}", tags=["Wishlist"])
def remove_from_wishlist(
    wishlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Remove item from wishlist by wishlist ID."""
    wishlist_item = (
        db.query(Wishlist)
        .filter(
            Wishlist.id == wishlist_id,
            Wishlist.user_id == current_user.id,
        )
        .first()
    )

    if not wishlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Wishlist item not found"},
        )

    db.delete(wishlist_item)
    db.commit()

    cache_key = f"wishlist:user:{current_user.id}"
    redis_client.delete(cache_key)

    return {"success": True, "message": "Product removed from wishlist"}


@router.delete("/wishlist", tags=["Wishlist"])
def clear_user_wishlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Clear all items from current user's wishlist."""
    db.query(Wishlist).filter(Wishlist.user_id == current_user.id).delete(
        synchronize_session=False
    )
    db.commit()

    cache_key = f"wishlist:user:{current_user.id}"
    redis_client.delete(cache_key)

    return {"success": True, "message": "Wishlist cleared successfully"}


@router.delete("/wishlist/product/{product_id}", tags=["Wishlist"])
def remove_from_wishlist_by_product_id(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Remove item from wishlist by product ID."""
    wishlist_item = (
        db.query(Wishlist)
        .filter(
            Wishlist.product_id == product_id,
            Wishlist.user_id == current_user.id,
        )
        .first()
    )

    if not wishlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Wishlist item not found"},
        )

    db.delete(wishlist_item)
    db.commit()

    cache_key = f"wishlist:user:{current_user.id}"
    redis_client.delete(cache_key)

    return {"success": True, "message": "Product removed from wishlist"}
