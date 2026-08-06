"""SQLAlchemy database models for E-Kart application."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from db.session import Base


class Product(Base):
    """Product domain model representing inventory items."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    price = Column(Float)
    image = Column(String)
    category = Column(String)
    stock = Column(Integer, default=10)

    cart_items = relationship("Cart", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    reviews = relationship("Review", back_populates="product")
    wishlist_items = relationship("Wishlist", back_populates="product")


class User(Base):
    """User account model for customer and admin authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)

    cart_items = relationship("Cart", back_populates="user")
    orders = relationship("Order", back_populates="user")
    addresses = relationship("Address", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    wishlist_items = relationship("Wishlist", back_populates="user")
    reset_tokens = relationship("PasswordResetToken", back_populates="user")


class PasswordResetToken(Base):
    """Security token model for password reset requests."""

    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reset_tokens")


class Cart(Base):
    """Shopping cart line items for users."""

    __tablename__ = "cart"

    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")


class Order(Base):
    """Customer order details and fulfillment tracking."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    total_price = Column(Float)
    status = Column(String, default="PROCESSING")
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    """Individual product line items within a placed order."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Review(Base):
    """Product ratings and review comments submitted by users."""

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    comment = Column(String)
    rating = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")


class Address(Base):
    """User shipping and billing address records."""

    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    full_name = Column(String)
    phone = Column(String)
    address_line = Column(String)
    city = Column(String)
    state = Column(String)
    pincode = Column(String)

    user = relationship("User", back_populates="addresses")


class Wishlist(Base):
    """Saved wishlist items associated with user accounts."""

    __tablename__ = "wishlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="wishlist_items")
    product = relationship("Product", back_populates="wishlist_items")


class IdempotencyRecord(Base):
    """Database entity storing processed request/response payloads for idempotency key validation."""

    __tablename__ = "idempotency_records"

    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    endpoint = Column(String(255), nullable=False)
    request_hash = Column(String(64), nullable=False)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    status = Column(String(20), default="PROCESSING", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)

    user = relationship("User")
