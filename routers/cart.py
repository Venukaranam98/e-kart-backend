from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from database import get_db

from models import Cart, User, Product

from schemas import (
    CartSchema,
    UpdateCartSchema
)

from routers.auth import get_current_user


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


    product_exists = db.query(Product).filter(

        Product.id == cart.product_id

    ).first()

    if not product_exists:

        raise HTTPException(

            status_code=404,

            detail={

                "success": False,

                "message": "Product not found"

            }

        )


    existing_cart_item = db.query(Cart).filter(

        Cart.user_id == current_user.id,

        Cart.product_id == cart.product_id

    ).first()


    if existing_cart_item:

        existing_cart_item.quantity += cart.quantity

        db.commit()

        db.refresh(existing_cart_item)

        return {

            "success": True,

            "message": "Cart quantity updated successfully",

            "data": {

                "cart_id": existing_cart_item.id,

                "product_id": existing_cart_item.product_id,

                "quantity": existing_cart_item.quantity

            }

        }


    new_cart_item = Cart(

        quantity=cart.quantity,

        user_id=current_user.id,

        product_id=cart.product_id

    )

    db.add(new_cart_item)

    db.commit()

    db.refresh(new_cart_item)

    return {

        "success": True,

        "message": "Product added to cart",

        "data": {

            "cart_id": new_cart_item.id,

            "product_id": new_cart_item.product_id,

            "quantity": new_cart_item.quantity

        }

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

    return {

        "success": True,

        "message": "Cart fetched successfully",

        "data": cart_response

    }



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

            detail={

                "success": False,

                "message": "Cart item not found"

            }

        )

    db.delete(cart_item)

    db.commit()

    return {

        "success": True,

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

            detail={

                "success": False,

                "message": "Cart item not found"

            }

        )

    cart_item.quantity = updated_cart.quantity

    db.commit()

    db.refresh(cart_item)

    return {

        "success": True,

        "message": "Cart quantity updated successfully",

        "data": {

            "cart_id": cart_item.id,

            "quantity": cart_item.quantity

        }

    }