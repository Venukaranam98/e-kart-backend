from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Address, User
from routers.auth import get_current_user
from schemas import AddressSchema

router = APIRouter(tags=["Address"])


@router.post("/address")
def save_address(
    address: AddressSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    new_address = Address(
        user_id=current_user.id,
        full_name=address.full_name,
        phone=address.phone,
        address_line=address.address_line,
        city=address.city,
        state=address.state,
        pincode=address.pincode
    )
    db.add(new_address)
    db.commit()

    return {"message": "Address saved"}

@router.get("/address")
def get_addresses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    addresses = db.query(Address).filter(
        Address.user_id == current_user.id
    ).all()

    return addresses