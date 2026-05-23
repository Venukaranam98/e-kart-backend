from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from database import get_db

from models import Cart, User

from schemas import (CartSchema,UpdateCartSchema)

from routers.auth import get_current_user

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)


router = APIRouter()


@router.post(

    "/cart",

    tags=["Cart"]

)

def add_to_cart(

    cart: CartSchema,

    db: Session = Depends(get_db),

    current_user: User = Depends(

        get_current_user

    )

):

    new_cart_item = Cart(

        quantity=cart.quantity,

        user_id=current_user.id,

        product_id=cart.product_id

    )


    db.add(new_cart_item)

    db.commit()

    db.refresh(new_cart_item)


    return {

        "message": "Product added to cart"

    }


@router.get(

    "/cart",

    tags=["Cart"]

)

def get_user_cart(

    db: Session = Depends(get_db),

    current_user: User = Depends(

        get_current_user

    )

):

    cart_items = db.query(Cart).filter(

        Cart.user_id == current_user.id

    ).all()


    cart_response = []


    for item in cart_items:

        cart_response.append({

            "cart_id": item.id,

            "product_title": item.product.title,

            "price": item.product.price,

            "image": item.product.image,

            "category": item.product.category,

            "quantity": item.quantity

        })


    return cart_response


@router.delete(

    "/cart/{cart_id}",

    tags=["Cart"]

)

def remove_from_cart(

    cart_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(

        get_current_user

    )

):

    cart_item = db.query(Cart).filter(

        Cart.id == cart_id,

        Cart.user_id == current_user.id

    ).first()


    if not cart_item:

        raise HTTPException(

            status_code=404,

            detail="Cart item not found"

        )


    db.delete(cart_item)

    db.commit()


    return {

        "message": "Item removed from cart"

    }


@router.put(

    "/cart/{cart_id}",

    tags=["Cart"]

)

def update_cart_quantity(

    cart_id: int,

    updated_cart: UpdateCartSchema,

    db: Session = Depends(get_db),

    current_user: User = Depends(

        get_current_user

    )

):

    cart_item = db.query(Cart).filter(

        Cart.id == cart_id,

        Cart.user_id == current_user.id

    ).first()


    if not cart_item:

        raise HTTPException(

            status_code=404,

            detail="Cart item not found"

        )


    cart_item.quantity = updated_cart.quantity


    db.commit()

    db.refresh(cart_item)


    return {

        "message": "Cart quantity updated",

        "quantity": cart_item.quantity

    }
