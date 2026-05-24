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
    ReviewSchema
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

    skip = (page - 1) * limit

    products = db.query(Product).offset(

        skip

    ).limit(

        limit

    ).all()

    return {

        "success": True,

        "message": "Products fetched successfully",

        "data": products

    }



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

        "data": products

    }



@router.get(
    "/products/{product_id}",
    tags=["Products"]
)

def get_product(

    product_id: int,

    db: Session = Depends(get_db)

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

    return {

        "success": True,

        "message": "Product fetched successfully",

        "data": product

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

        "data": products

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

        "data": products

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

    return {

        "success": True,

        "message": "Product updated successfully",

        "data": product

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

    file_path = f"uploads/{file.filename}"

    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    return {

        "success": True,

        "message": "Image uploaded successfully",

        "data": {

            "image_url": f"/uploads/{file.filename}"

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