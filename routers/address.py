"""User address management router endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from db.session import get_db
from dependencies.auth import get_current_user
from models import Address, User
from schemas import AddressSchema

router = APIRouter(tags=["Addresses"])


@router.post(
    "/address",
    summary="Save Shipping Address",
    description="Save a new delivery address for the authenticated user.",
    response_description="Created address object",
    tags=["Addresses"],
    responses={
        200: {"description": "Address saved successfully."},
        401: {"description": "Unauthorized."},
    },
)
def save_address(
    address: AddressSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Save a new shipping address for current user."""
    new_address = Address(
        user_id=current_user.id,
        full_name=address.full_name,
        phone=address.phone,
        address_line=address.address_line,
        city=address.city,
        state=address.state,
        pincode=address.pincode,
    )
    db.add(new_address)
    db.commit()
    db.refresh(new_address)

    return {"message": "Address saved", "address": new_address}


@router.get(
    "/address",
    summary="Get User Addresses",
    description="Retrieve all saved delivery addresses for the authenticated user.",
    response_description="Array of user address objects",
    tags=["Addresses"],
    responses={
        200: {"description": "List of user addresses."},
        401: {"description": "Unauthorized."},
    },
)
def get_addresses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Any]:
    """Fetch all shipping addresses for current user."""
    addresses = db.query(Address).filter(Address.user_id == current_user.id).all()
    return addresses


@router.put(
    "/address/{address_id}",
    summary="Update Address",
    description="Modify an existing delivery address by ID.",
    response_description="Updated address object",
    tags=["Addresses"],
    responses={
        200: {"description": "Address updated successfully."},
        401: {"description": "Unauthorized."},
        404: {"description": "Address not found."},
    },
)
def update_address(
    address_id: int = Path(
        ..., title="Address ID", description="Target address ID to edit", example=1
    ),
    address: AddressSchema = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Update an existing shipping address."""
    existing_address = (
        db.query(Address)
        .filter(Address.id == address_id, Address.user_id == current_user.id)
        .first()
    )

    if not existing_address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Address not found"
        )

    existing_address.full_name = address.full_name
    existing_address.phone = address.phone
    existing_address.address_line = address.address_line
    existing_address.city = address.city
    existing_address.state = address.state
    existing_address.pincode = address.pincode

    db.commit()
    db.refresh(existing_address)

    return {"message": "Address updated", "address": existing_address}


@router.delete(
    "/address/{address_id}",
    summary="Delete Address",
    description="Remove a delivery address record by ID.",
    response_description="Deletion status message",
    tags=["Addresses"],
    responses={
        200: {"description": "Address deleted."},
        401: {"description": "Unauthorized."},
        404: {"description": "Address not found."},
    },
)
def delete_address(
    address_id: int = Path(
        ..., title="Address ID", description="Target address ID to delete", example=1
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Delete a shipping address by ID."""
    existing_address = (
        db.query(Address)
        .filter(Address.id == address_id, Address.user_id == current_user.id)
        .first()
    )

    if not existing_address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Address not found"
        )

    db.delete(existing_address)
    db.commit()

    return {"message": "Address deleted"}
