"""Product catalog, search, filtering, and review management router endpoints."""

import json
import logging
from typing import Any

import cloudinary
import cloudinary.uploader
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Path,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from db.session import get_db
from dependencies.auth import get_current_admin, get_current_user
from models import Product, Review, User
from redis_client import redis_client
from schemas import ProductResponse, ProductSchema, ReviewSchema

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/products",
    status_code=status.HTTP_200_OK,
    summary="Create Product (Admin Only)",
    description="Create a new product record in the catalog and invalidate Redis product caches. Requires Admin JWT Bearer authentication.",
    response_description="Created product metadata",
    tags=["Products"],
    responses={
        200: {"description": "Product created successfully."},
        401: {"description": "Unauthorized."},
        403: {"description": "Forbidden: Requires Admin privileges."},
    },
)
def create_product(
    product: ProductSchema,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> dict[str, Any]:
    """Create a new product in the store inventory (Admin only)."""
    new_product = Product(
        title=product.title,
        description=product.description,
        price=product.price,
        image=product.image,
        category=product.category,
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    for key in redis_client.scan_iter("product:*"):
        redis_client.delete(key)

    for key in redis_client.scan_iter("products:*"):
        redis_client.delete(key)

    return {
        "success": True,
        "message": "Product created successfully",
        "data": {
            "id": new_product.id,
            "title": new_product.title,
            "price": new_product.price,
            "category": new_product.category,
        },
    }


@router.get(
    "/products",
    summary="List Products (Paginated)",
    description="Retrieve catalog products using page and limit parameters. Uses Redis Cache-Aside pattern (1 hour expiration).",
    response_description="Paginated array of product objects",
    tags=["Products"],
    responses={200: {"description": "List of product objects returned successfully."}},
)
def get_products(
    page: int = Query(1, description="Page index (1-based)", example=1, ge=1),
    limit: int = Query(
        5, description="Number of products per page", example=5, ge=1, le=100
    ),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Fetch paginated products list with Redis caching."""
    cache_key = f"products:page:{page}:limit:{limit}"
    cached_products = redis_client.get(cache_key)

    if cached_products:
        logger.info("Products cache hit")
        return json.loads(cached_products)

    logger.info("Products cache miss")
    skip = (page - 1) * limit
    products = (
        db.query(Product).order_by(asc(Product.id)).offset(skip).limit(limit).all()
    )

    response = {
        "success": True,
        "message": "Products fetched successfully",
        "data": [
            ProductResponse.model_validate(product).model_dump() for product in products
        ],
    }

    redis_client.set(cache_key, json.dumps(response), ex=3600)
    return response


@router.get(
    "/products/filter",
    summary="Filter & Sort Products",
    description="Filter catalog products by category, price range, and sort order (low_to_high or high_to_low).",
    response_description="Filtered product items array",
    tags=["Products"],
    responses={200: {"description": "Filtered products array retrieved."}},
)
def filter_products(
    category: str | None = Query(
        None, description="Category name (e.g. Mobiles, Laptops)", example="Mobiles"
    ),
    min_price: float | None = Query(
        None, description="Minimum price filter (INR)", example=10000.0
    ),
    max_price: float | None = Query(
        None, description="Maximum price filter (INR)", example=80000.0
    ),
    sort: str | None = Query(
        None,
        description="Price sorting strategy: 'low_to_high' or 'high_to_low'",
        example="low_to_high",
    ),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Filter and sort product catalog by category, price range, and order."""
    query = db.query(Product)

    if category:
        query = query.filter(Product.category.ilike(category))

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if sort == "low_to_high":
        query = query.order_by(asc(Product.price), asc(Product.id))
    elif sort == "high_to_low":
        query = query.order_by(desc(Product.price), asc(Product.id))
    else:
        query = query.order_by(asc(Product.id))

    products = query.all()

    return {
        "success": True,
        "message": "Filtered products fetched successfully",
        "data": [ProductResponse.model_validate(product) for product in products],
    }


@router.get(
    "/products/{product_id}",
    summary="Get Product Details by ID",
    description="Retrieve complete specifications for a single product by ID. Utilizes Redis caching.",
    response_description="Single product details object",
    tags=["Products"],
    responses={
        200: {"description": "Product details returned."},
        404: {"description": "Product not found."},
    },
)
def get_product(
    product_id: int = Path(
        ..., title="Product ID", description="Unique identifier of product", example=1
    ),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Fetch product details by ID with Redis caching."""
    cache_key = f"product:{product_id}"
    cached_product = redis_client.get(cache_key)

    if cached_product:
        logger.info("Product cache hit")
        return json.loads(cached_product)

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Product not found"},
        )

    response = {
        "success": True,
        "message": "Product fetched successfully",
        "data": ProductResponse.model_validate(product).model_dump(),
    }

    redis_client.set(cache_key, json.dumps(response), ex=3600)
    return response


@router.post(
    "/products/{product_id}/view",
    summary="Track Recently Viewed Product",
    description="Push a product ID to the user's recently viewed list stored in Redis.",
    response_description="Tracking confirmation",
    tags=["Products"],
    responses={
        200: {"description": "View logged in user's Redis tracking history."},
        401: {"description": "Unauthorized."},
    },
)
def track_product_view(
    product_id: int = Path(
        ..., title="Product ID", description="Product ID to record", example=1
    ),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Track recently viewed product for current user."""
    recent_key = f"recent:user:{current_user.id}"

    redis_client.lrem(recent_key, 0, str(product_id))
    redis_client.lpush(recent_key, str(product_id))
    redis_client.ltrim(recent_key, 0, 9)
    redis_client.expire(recent_key, 604800)

    return {"success": True, "message": "Product view tracked"}


@router.get(
    "/products/recent/viewed",
    summary="Get Recently Viewed Products",
    description="Retrieve up to 10 recently viewed products for the authenticated user from Redis history.",
    response_description="List of recently viewed products",
    tags=["Products"],
    responses={
        200: {"description": "Recently viewed items array."},
        401: {"description": "Unauthorized."},
    },
)
def get_recently_viewed_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Fetch list of recently viewed products for current user."""
    recent_key = f"recent:user:{current_user.id}"
    product_ids = redis_client.lrange(recent_key, 0, -1)

    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    product_map = {str(product.id): product for product in products}

    ordered_products = []
    for pid in product_ids:
        product = product_map.get(pid)
        if product:
            ordered_products.append(ProductResponse.model_validate(product))

    return {
        "success": True,
        "message": "Recently viewed products fetched successfully",
        "data": ordered_products,
    }


@router.get(
    "/products/search/",
    summary="Search Products by Keyword",
    description="Perform case-insensitive title search on products catalog.",
    response_description="Array of matching products",
    tags=["Products"],
    responses={200: {"description": "Search results returned."}},
)
def search_products(
    query: str = Query(..., description="Search keyword query", example="oneplus"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Search products by title keyword."""
    products = (
        db.query(Product)
        .filter(Product.title.ilike(f"%{query}%"))
        .order_by(asc(Product.id))
        .all()
    )

    return {
        "success": True,
        "message": "Search results fetched successfully",
        "data": [ProductResponse.model_validate(product) for product in products],
    }


@router.get(
    "/products/category/{category_name}",
    summary="Get Products by Category",
    description="Retrieve all products belonging to a specified category name.",
    response_description="Array of category products",
    tags=["Products"],
    responses={200: {"description": "Category products returned."}},
)
def get_products_by_category(
    category_name: str = Path(
        ..., title="Category Name", description="Target category", example="Mobiles"
    ),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Fetch products matching a specific category name."""
    products = (
        db.query(Product)
        .filter(Product.category.ilike(category_name))
        .order_by(asc(Product.id))
        .all()
    )

    return {
        "success": True,
        "message": "Category products fetched successfully",
        "data": [ProductResponse.model_validate(product) for product in products],
    }


@router.put(
    "/products/{product_id}",
    summary="Update Product (Admin Only)",
    description="Update existing product attributes (title, price, image, category) and invalidate Redis cache.",
    response_description="Updated product object",
    tags=["Products"],
    responses={
        200: {"description": "Product updated successfully."},
        401: {"description": "Unauthorized."},
        403: {"description": "Forbidden: Requires Admin privileges."},
        404: {"description": "Product not found."},
    },
)
def update_product(
    product_id: int = Path(
        ..., title="Product ID", description="Product ID to modify", example=1
    ),
    updated_product: ProductSchema = ...,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> dict[str, Any]:
    """Update product information (Admin only)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Product not found"},
        )

    product.title = updated_product.title
    product.description = updated_product.description
    product.price = updated_product.price
    product.image = updated_product.image
    product.category = updated_product.category

    db.commit()
    db.refresh(product)

    try:
        for key in redis_client.scan_iter("product:*"):
            redis_client.delete(key)
        for key in redis_client.scan_iter("products:*"):
            redis_client.delete(key)
    except Exception as e:
        logger.warning(f"Redis cache clear warning: {e}")

    return {
        "success": True,
        "message": "Product updated successfully",
        "data": ProductResponse.model_validate(product),
    }


@router.delete(
    "/products/{product_id}",
    summary="Delete Product (Admin Only)",
    description="Permanently remove product from inventory and clear cache.",
    response_description="Deletion confirmation message",
    tags=["Products"],
    responses={
        200: {"description": "Product deleted successfully."},
        401: {"description": "Unauthorized."},
        403: {"description": "Forbidden: Admin required."},
        404: {"description": "Product not found."},
    },
)
def delete_product(
    product_id: int = Path(
        ..., title="Product ID", description="Product ID to delete", example=1
    ),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> dict[str, Any]:
    """Delete a product from the inventory (Admin only)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Product not found"},
        )

    db.delete(product)
    db.commit()

    for key in redis_client.scan_iter("product:*"):
        redis_client.delete(key)
    for key in redis_client.scan_iter("products:*"):
        redis_client.delete(key)

    return {"success": True, "message": "Product deleted successfully"}


@router.post(
    "/upload-image",
    summary="Upload Image to Cloudinary CDN (Admin Only)",
    description="Upload multipart/form-data image file to Cloudinary CDN storage and return secure image URL.",
    response_description="Cloudinary secure image URL object",
    tags=["Products"],
    responses={
        200: {"description": "Image uploaded successfully."},
        401: {"description": "Unauthorized."},
        403: {"description": "Forbidden: Requires Admin privileges."},
    },
)
def upload_image(
    file: UploadFile = File(..., description="Multipart image file (JPEG, PNG, WebP)"),
    current_admin: User = Depends(get_current_admin),
) -> dict[str, Any]:
    """Upload product image file to Cloudinary."""
    result = cloudinary.uploader.upload(file.file, folder="ekart")
    return {
        "success": True,
        "message": "Image uploaded successfully",
        "data": {"image_url": result["secure_url"]},
    }


@router.post(
    "/products/{product_id}/review",
    summary="Add Product Review",
    description="Submit a 1-5 star review and comment for a product. Requires user authentication.",
    response_description="Created review object",
    tags=["Products"],
    responses={
        200: {"description": "Review added successfully."},
        401: {"description": "Unauthorized."},
        404: {"description": "Product not found."},
    },
)
def add_review(
    product_id: int = Path(
        ..., title="Product ID", description="Target product ID for review", example=1
    ),
    review: ReviewSchema = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Submit a rating review for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Product not found"},
        )

    new_review = Review(
        comment=review.comment,
        rating=review.rating,
        user_id=current_user.id,
        product_id=product.id,
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return {
        "success": True,
        "message": "Review added successfully",
        "data": {
            "review_id": new_review.id,
            "rating": new_review.rating,
            "comment": new_review.comment,
        },
    }
