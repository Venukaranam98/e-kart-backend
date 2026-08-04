"""Pydantic v2 schemas for request validation and response serialization."""

from pydantic import BaseModel, ConfigDict


class ProductSchema(BaseModel):
    """Schema for creating or updating product details."""

    title: str
    description: str
    price: float
    image: str
    category: str


class ProductResponse(BaseModel):
    """Schema for returning product data."""

    id: int
    title: str
    description: str
    price: float
    image: str
    category: str

    model_config = ConfigDict(from_attributes=True)


class UserSchema(BaseModel):
    """Schema for user registration requests."""

    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    """Schema for returning public user information."""

    id: int
    username: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class LoginSchema(BaseModel):
    """Schema for user authentication requests."""

    email: str
    password: str


class CartSchema(BaseModel):
    """Schema for adding an item to the shopping cart."""

    product_id: int
    quantity: int


class UpdateCartSchema(BaseModel):
    """Schema for updating cart item quantity."""

    quantity: int


class CartItemSchema(BaseModel):
    """Cart item schema for bulk or inline operations."""

    product_id: int
    quantity: int


class CartResponse(BaseModel):
    """Response schema for formatted cart item display."""

    cart_id: int
    product_title: str
    price: float
    image: str
    category: str
    quantity: int


class ReviewSchema(BaseModel):
    """Schema for submitting a product review."""

    comment: str
    rating: int


class ReviewResponse(BaseModel):
    """Response schema for serialized product review."""

    id: int
    comment: str
    rating: int

    model_config = ConfigDict(from_attributes=True)


class AddressSchema(BaseModel):
    """Schema for creating or updating user shipping addresses."""

    full_name: str
    phone: str
    address_line: str
    city: str
    state: str
    pincode: str


class AdminDashboardResponse(BaseModel):
    """Response schema for administrative metrics overview."""

    total_users: int
    total_products: int
    total_orders: int


class WishlistSchema(BaseModel):
    """Schema for adding a product to wishlist."""

    product_id: int


class WishlistResponse(BaseModel):
    """Response schema for serialized wishlist item."""

    wishlist_id: int
    product_title: str
    price: float
    image: str
    category: str


class ForgotPasswordRequest(BaseModel):
    """Schema for requesting a password reset email."""

    email: str


class ResetPasswordRequest(BaseModel):
    """Schema for completing a password reset via token."""

    token: str
    new_password: str


class OrderRequest(BaseModel):
    """Schema for initiating a payment order."""

    amount: int
