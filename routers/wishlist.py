from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from database import get_db

from models import (
    Wishlist,
    Product,
    User
)

from schemas import WishlistSchema

from routers.auth import get_current_user
import json

from redis_client import redis_client

router = APIRouter()

@router.post(
    "/wishlist",
    tags=["Wishlist"]
)
def add_to_wishlist(

    wishlist: WishlistSchema,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )

):

    product_exists = db.query(Product).filter(

        Product.id == wishlist.product_id

    ).first()

    if not product_exists:

        raise HTTPException(

            status_code=404,

            detail={

                "success": False,

                "message": "Product not found"

            }

        )


    existing_wishlist_item = db.query(Wishlist).filter(

        Wishlist.user_id == current_user.id,

        Wishlist.product_id == wishlist.product_id

    ).first()

    if existing_wishlist_item:

        raise HTTPException(

            status_code=400,

            detail={

                "success": False,

                "message": "Product already in wishlist"

            }

        )

    new_wishlist_item = Wishlist(

        user_id=current_user.id,

        product_id=wishlist.product_id

    )

    db.add(new_wishlist_item)
    db.commit()
    db.refresh(new_wishlist_item)

    redis_client.delete(
    f"wishlist:user:{current_user.id}"
    )

    return {

        "success": True,

        "message": "Product added to wishlist",

        "data": {

            "wishlist_id": new_wishlist_item.id,

            "product_id": new_wishlist_item.product_id

        }

    }

@router.get(
    "/wishlist",
    tags=["Wishlist"]
)
def get_user_wishlist(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )

):
    cache_key = f"wishlist:user:{current_user.id}"
    cached_wishlist = redis_client.get(cache_key)
    if cached_wishlist:

        print("Wishlist cache hit")

        return json.loads(cached_wishlist)

    print("Wishlist cache miss")

    wishlist_items = db.query(Wishlist).filter(

        Wishlist.user_id == current_user.id

    ).all()


    wishlist_response = []

    for item in wishlist_items:

        wishlist_response.append({

        "wishlist_id": item.id,

        "product_id": item.product.id,

        "product_title": item.product.title,

        "price": item.product.price,

        "image": item.product.image,

        "category": item.product.category

    })

    response = {

        "success": True,

        "message": "Wishlist fetched successfully",

        "data": wishlist_response

    }


    redis_client.set(
    cache_key,
    json.dumps(response),
    ex=3600
    )
    return response

@router.delete(
    "/wishlist/{wishlist_id}",
    tags=["Wishlist"]
)
def remove_from_wishlist(

    wishlist_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    )

):

    wishlist_item = db.query(Wishlist).filter(

        Wishlist.id == wishlist_id,

        Wishlist.user_id == current_user.id

    ).first()

    if not wishlist_item:

        raise HTTPException(

            status_code=404,

            detail={

                "success": False,

                "message": "Wishlist item not found"

            }

        )

    db.delete(wishlist_item)
    db.commit()

    cache_key = f"wishlist:user:{current_user.id}"

    redis_client.delete(cache_key)

    return {

        "success": True,

        "message": "Product removed from wishlist"

    }
    