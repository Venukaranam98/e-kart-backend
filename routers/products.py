from fastapi import (
    APIRouter,
    Query,
    UploadFile,
    File,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from sqlalchemy import asc, desc

from database import get_db

from schemas import (
    ProductSchema,
    ReviewSchema,
    ProductResponse
)

from models import (
    Product,
    User,
    Review
)

from routers.auth import (
    get_current_admin,
    get_current_user
)

import shutil
import uuid
import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import json

from redis_client import redis_client


router = APIRouter()


@router.post(
    "/products",
    tags=["Products"]
)

def create_product(

    product: ProductSchema,

    db: Session = Depends(get_db),

    current_admin: User = Depends(
        get_current_admin
    )

):

    new_product = Product(

        title=product.title,

        description=product.description,

        price=product.price,

        image=product.image,

        category=product.category

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

            "category": new_product.category

        }

    }


@router.get(
    "/products",
    tags=["Products"]
)
def get_products(
    page: int = 1,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    cache_key = f"products:page:{page}:limit:{limit}"

    cached_products = redis_client.get(cache_key)

    if cached_products:
        print("Cache hit")
        return json.loads(cached_products)

    print("Cache miss")

    skip = (page - 1) * limit

    products = db.query(Product).offset(
        skip
    ).limit(
        limit
    ).all()

    response = {
        "success": True,
        "message": "Products fetched successfully",
        "data": [
            ProductResponse.model_validate(product).model_dump()
            for product in products
        ]
    }

    redis_client.set(
        cache_key,
        json.dumps(response),
        ex=3600
    )

    return response

@router.get(
    "/products/filter",
    tags=["Products"]
)

def filter_products(

    category: str = None,

    min_price: float = None,

    max_price: float = None,

    sort: str = None,

    db: Session = Depends(get_db)

):

    query = db.query(Product)

    if category:

        query = query.filter(
            Product.category.ilike(category)
        )

    if min_price is not None:

        query = query.filter(
            Product.price >= min_price
        )

    if max_price is not None:

        query = query.filter(
            Product.price <= max_price
        )

    if sort == "low_to_high":

        query = query.order_by(
            asc(Product.price)
        )

    elif sort == "high_to_low":

        query = query.order_by(
            desc(Product.price)
        )

    products = query.all()

    return {

        "success": True,

        "message": "Filtered products fetched successfully",

        "data": [

            ProductResponse.model_validate(product)

            for product in products

        ]

    }


@router.get("/products/{product_id}")
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    cache_key = f"product:{product_id}"

    cached_product = redis_client.get(cache_key)

    if cached_product:
        print("Product cache hit")
        return json.loads(cached_product)

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": "Product not found"
            }
        )

    response = {
        "success": True,
        "message": "Product fetched successfully",
        "data": ProductResponse.model_validate(product).model_dump()
    }

    redis_client.set(
        cache_key,
        json.dumps(response),
        ex=3600
    )

    return response

@router.post(
    "/products/{product_id}/view",
    tags=["Products"]
)
def track_product_view(
    product_id: int,
    current_user: User = Depends(get_current_user)
):
    recent_key = f"recent:user:{current_user.id}"

    redis_client.lrem(
        recent_key,
        0,
        str(product_id)
    )

    redis_client.lpush(
        recent_key,
        str(product_id)
    )

    redis_client.ltrim(
        recent_key,
        0,
        9
    )

    redis_client.expire(
        recent_key,
        604800
    )

    return {
        "success": True,
        "message": "Product view tracked"
    }

@router.get(
    "/products/recent/viewed",
    tags=["Products"]
)
def get_recently_viewed_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    recent_key = f"recent:user:{current_user.id}"

    product_ids = redis_client.lrange(
        recent_key,
        0,
        -1
    )

    products = db.query(Product).filter(
        Product.id.in_(product_ids)
    ).all()

    product_map = {
        str(product.id): product
        for product in products
    }

    ordered_products = []

    for product_id in product_ids:
        product = product_map.get(product_id)

        if product:
            ordered_products.append(
                ProductResponse.model_validate(product)
            )

    return {
        "success": True,
        "message": "Recently viewed products fetched successfully",
        "data": ordered_products
    }

@router.get(
    "/products/search/",
    tags=["Products"]
)

def search_products(

    query: str = Query(...),

    db: Session = Depends(get_db)

):

    products = db.query(Product).filter(

        Product.title.ilike(f"%{query}%")

    ).all()

    return {

        "success": True,

        "message": "Search results fetched successfully",

        "data": [

            ProductResponse.model_validate(product)

            for product in products

        ]

    }


@router.get(
    "/products/category/{category_name}",
    tags=["Products"]
)

def get_products_by_category(

    category_name: str,

    db: Session = Depends(get_db)

):

    products = db.query(Product).filter(

        Product.category.ilike(category_name)

    ).all()

    return {

        "success": True,

        "message": "Category products fetched successfully",

        "data": [

            ProductResponse.model_validate(product)

            for product in products

        ]

    }


@router.put(
    "/products/{product_id}",
    tags=["Products"]
)

def update_product(

    product_id: int,

    updated_product: ProductSchema,

    db: Session = Depends(get_db),

    current_admin: User = Depends(
        get_current_admin
    )

):

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:

        raise HTTPException(

            status_code=404,

            detail={

                "success": False,

                "message": "Product not found"

            }

        )

    product.title = updated_product.title
    product.description = updated_product.description
    product.price = updated_product.price
    product.image = updated_product.image
    product.category = updated_product.category

    db.commit()

    db.refresh(product)
    for key in redis_client.scan_iter("product:*"):
        redis_client.delete(key)

    for key in redis_client.scan_iter("products:*"):
        redis_client.delete(key)

    return {

        "success": True,

        "message": "Product updated successfully",

        "data": ProductResponse.model_validate(product)

    }


@router.delete(
    "/products/{product_id}",
    tags=["Products"]
)

def delete_product(

    product_id: int,

    db: Session = Depends(get_db),

    current_admin: User = Depends(
        get_current_admin
    )

):

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:

        raise HTTPException(

            status_code=404,

            detail={

                "success": False,

                "message": "Product not found"

            }

        )

    db.delete(product)

    db.commit()

    for key in redis_client.scan_iter("product:*"):
        redis_client.delete(key)

    for key in redis_client.scan_iter("products:*"):
        redis_client.delete(key)

    return {

        "success": True,

        "message": "Product deleted successfully"

    }


@router.post(
    "/upload-image",
    tags=["Products"]
)
def upload_image(
    file: UploadFile = File(...),
    current_admin: User = Depends(
        get_current_admin
    )
):
    result = cloudinary.uploader.upload(
        file.file,
        folder="ekart"
    )

    return {
        "success": True,
        "message": "Image uploaded successfully",
        "data": {
            "image_url": result[
                "secure_url"
            ]
        }
    }

@router.post(
    "/products/{product_id}/review",
    tags=["Reviews"]
)

def add_review(

    product_id: int,

    review: ReviewSchema,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )

):

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:

        raise HTTPException(

            status_code=404,

            detail={

                "success": False,

                "message": "Product not found"

            }

        )

    new_review = Review(

        comment=review.comment,

        rating=review.rating,

        user_id=current_user.id,

        product_id=product.id

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

            "comment": new_review.comment

        }

    }