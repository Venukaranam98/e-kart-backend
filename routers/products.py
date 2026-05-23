from fastapi import APIRouter,Query,UploadFile, File

from sqlalchemy.orm import Session

from fastapi import Depends

from database import get_db

from schemas import ProductSchema,ReviewSchema

from models import Product,User,Review

from routers.auth import get_current_admin

import shutil

from sqlalchemy import asc, desc

from routers.auth import (
    get_current_admin,
    get_current_user
)


router = APIRouter()


@router.post("/products")

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


    return new_product


@router.get("/products")

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


    return products


@router.get("/products/filter")

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


    return products



@router.get("/products/{product_id}")

def get_product(

    product_id: int,

    db: Session = Depends(get_db)

):

    product = db.query(Product).filter(

        Product.id == product_id

    ).first()


    return product


@router.get("/products/search/")

def search_products(

    query: str = Query(...),

    db: Session = Depends(get_db)

):

    products = db.query(Product).filter(

        Product.title.ilike(f"%{query}%")

    ).all()


    return products


@router.get("/products/category/{category_name}")

def get_products_by_category(

    category_name: str,

    db: Session = Depends(get_db)

):

    products = db.query(Product).filter(

        Product.category.ilike(category_name)

    ).all()


    return products


@router.put("/products/{product_id}")

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


    product.title = updated_product.title

    product.description = updated_product.description

    product.price = updated_product.price

    product.image = updated_product.image

    product.category = updated_product.category


    db.commit()

    db.refresh(product)


    return product


@router.delete("/products/{product_id}")

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


    db.delete(product)

    db.commit()


    return {

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

        "image_url": f"/uploads/{file.filename}"

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

        return {

            "message": "Product not found"

        }


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

        "message": "Review added successfully"

    }