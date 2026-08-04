"""Pydantic v2 schemas for request validation and response serialization."""

from pydantic import BaseModel, ConfigDict, Field


class ProductSchema(BaseModel):
    """Schema for creating or updating product details."""

    title: str = Field(
        ...,
        description="Title or name of the product",
        example="ONEPLUS 15R",
    )
    description: str = Field(
        ...,
        description="Detailed specification and features of the product",
        example="Experience ultra-fast performance with Snapdragon 8 Gen processor.",
    )
    price: float = Field(
        ...,
        description="Product retail price in INR (₹)",
        example=59999.0,
    )
    image: str = Field(
        ...,
        description="Cloudinary or HTTP image URL for the product",
        example="https://res.cloudinary.com/demo/image/upload/sample.jpg",
    )
    category: str = Field(
        ...,
        description="Product category classification",
        example="Mobiles",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "ONEPLUS 15R",
                "description": "Flagship smartphone with 120Hz Fluid AMOLED display.",
                "price": 59999.0,
                "image": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
                "category": "Mobiles",
            }
        }
    )


class ProductResponse(BaseModel):
    """Schema for returning product data."""

    id: int = Field(..., description="Unique product ID", example=1)
    title: str = Field(..., description="Product title", example="ONEPLUS 15R")
    description: str = Field(
        ..., description="Product description", example="Flagship phone"
    )
    price: float = Field(..., description="Product price in INR", example=59999.0)
    image: str = Field(
        ...,
        description="Image URL",
        example="https://res.cloudinary.com/demo/sample.jpg",
    )
    category: str = Field(..., description="Category name", example="Mobiles")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "ONEPLUS 15R",
                "description": "Flagship smartphone with 120Hz display.",
                "price": 59999.0,
                "image": "https://res.cloudinary.com/demo/sample.jpg",
                "category": "Mobiles",
            }
        },
    )


class UserSchema(BaseModel):
    """Schema for user registration requests."""

    username: str = Field(
        ...,
        description="Desired unique username",
        example="john_doe",
    )
    email: str = Field(
        ...,
        description="User email address",
        example="john@example.com",
    )
    password: str = Field(
        ...,
        description="User password (min 6 characters)",
        example="StrongPassword123",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "StrongPassword123",
            }
        }
    )


class UserResponse(BaseModel):
    """Schema for returning public user information."""

    id: int = Field(..., description="Unique user ID", example=42)
    username: str = Field(..., description="User's handle", example="john_doe")
    email: str = Field(
        ..., description="User's email address", example="john@example.com"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 42,
                "username": "john_doe",
                "email": "john@example.com",
            }
        },
    )


class LoginSchema(BaseModel):
    """Schema for user authentication requests."""

    email: str = Field(
        ...,
        description="Registered account email address",
        example="john@example.com",
    )
    password: str = Field(
        ...,
        description="Account password",
        example="StrongPassword123",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john@example.com",
                "password": "StrongPassword123",
            }
        }
    )


class CartSchema(BaseModel):
    """Schema for adding an item to the shopping cart."""

    product_id: int = Field(
        ...,
        description="ID of the target product to add to cart",
        example=1,
    )
    quantity: int = Field(
        1,
        description="Quantity of product items to add (min 1)",
        example=2,
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": 1,
                "quantity": 2,
            }
        }
    )


class UpdateCartSchema(BaseModel):
    """Schema for updating cart item quantity."""

    quantity: int = Field(
        ...,
        description="New quantity for cart item",
        example=3,
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "quantity": 3,
            }
        }
    )


class CartItemSchema(BaseModel):
    """Cart item schema for bulk or inline operations."""

    product_id: int = Field(..., description="Product ID", example=1)
    quantity: int = Field(..., description="Item quantity", example=1)


class CartResponse(BaseModel):
    """Response schema for formatted cart item display."""

    cart_id: int = Field(..., description="Unique cart item ID", example=10)
    product_title: str = Field(..., description="Product title", example="ONEPLUS 15R")
    price: float = Field(..., description="Item price", example=59999.0)
    image: str = Field(
        ...,
        description="Product image URL",
        example="https://res.cloudinary.com/demo/sample.jpg",
    )
    category: str = Field(..., description="Product category", example="Mobiles")
    quantity: int = Field(..., description="Quantity ordered", example=2)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cart_id": 10,
                "product_title": "ONEPLUS 15R",
                "price": 59999.0,
                "image": "https://res.cloudinary.com/demo/sample.jpg",
                "category": "Mobiles",
                "quantity": 2,
            }
        }
    )


class ReviewSchema(BaseModel):
    """Schema for submitting a product review."""

    comment: str = Field(
        ...,
        description="Review commentary text",
        example="Outstanding build quality and battery life!",
    )
    rating: int = Field(
        ...,
        description="Star rating from 1 to 5",
        example=5,
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "comment": "Outstanding build quality and battery life!",
                "rating": 5,
            }
        }
    )


class ReviewResponse(BaseModel):
    """Response schema for serialized product review."""

    id: int = Field(..., description="Review ID", example=1)
    comment: str = Field(..., description="Review text", example="Great phone!")
    rating: int = Field(..., description="Rating out of 5", example=5)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "comment": "Great phone!",
                "rating": 5,
            }
        },
    )


class AddressSchema(BaseModel):
    """Schema for creating or updating user shipping addresses."""

    full_name: str = Field(..., description="Recipient's full name", example="John Doe")
    phone: str = Field(
        ..., description="Recipient's phone number", example="9876543210"
    )
    address_line: str = Field(
        ..., description="House No., Building, Street", example="42 Tech Park Avenue"
    )
    city: str = Field(..., description="City name", example="Bengaluru")
    state: str = Field(..., description="State name", example="Karnataka")
    pincode: str = Field(..., description="6-digit PIN code", example="560001")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "John Doe",
                "phone": "9876543210",
                "address_line": "42 Tech Park Avenue",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560001",
            }
        }
    )


class AdminDashboardResponse(BaseModel):
    """Response schema for administrative metrics overview."""

    total_users: int = Field(
        ..., description="Total registered users count", example=150
    )
    total_products: int = Field(
        ..., description="Total active catalog products", example=45
    )
    total_orders: int = Field(..., description="Total order volume count", example=320)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_users": 150,
                "total_products": 45,
                "total_orders": 320,
            }
        }
    )


class WishlistSchema(BaseModel):
    """Schema for adding a product to wishlist."""

    product_id: int = Field(
        ...,
        description="Target product ID to add to wishlist",
        example=1,
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": 1,
            }
        }
    )


class WishlistResponse(BaseModel):
    """Response schema for serialized wishlist item."""

    wishlist_id: int = Field(..., description="Wishlist item ID", example=5)
    product_title: str = Field(..., description="Product name", example="ONEPLUS 15R")
    price: float = Field(..., description="Price in INR", example=59999.0)
    image: str = Field(
        ...,
        description="Image URL",
        example="https://res.cloudinary.com/demo/sample.jpg",
    )
    category: str = Field(..., description="Category", example="Mobiles")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "wishlist_id": 5,
                "product_title": "ONEPLUS 15R",
                "price": 59999.0,
                "image": "https://res.cloudinary.com/demo/sample.jpg",
                "category": "Mobiles",
            }
        }
    )


class ForgotPasswordRequest(BaseModel):
    """Schema for requesting a password reset email."""

    email: str = Field(
        ...,
        description="User email address for password recovery",
        example="john@example.com",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john@example.com",
            }
        }
    )


class ResetPasswordRequest(BaseModel):
    """Schema for completing a password reset via token."""

    token: str = Field(
        ...,
        description="Password reset token received via email link",
        example="d9a1f2b3c4e5f6a7b8c9d0e1f2a3b4c5",
    )
    new_password: str = Field(
        ...,
        description="New password (min 6 characters)",
        example="NewSuperPassword2026!",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "d9a1f2b3c4e5f6a7b8c9d0e1f2a3b4c5",
                "new_password": "NewSuperPassword2026!",
            }
        }
    )


class OrderRequest(BaseModel):
    """Schema for initiating a payment order."""

    amount: int = Field(
        ...,
        description="Order total amount in INR (₹)",
        example=59999,
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 59999,
            }
        }
    )
