from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean

from database import Base

from sqlalchemy.orm import relationship

from datetime import datetime

class Product(Base):

    __tablename__ = "products"


    id = Column(Integer, primary_key=True, index=True)

    title = Column(String)

    description = Column(String)

    price = Column(Float)

    image = Column(String)

    category = Column(String)


    cart_items = relationship(
        "Cart",
        back_populates="product"
    )
    order_items = relationship(
    "OrderItem",
     back_populates="product"
    )
    reviews = relationship(
    "Review",
    back_populates="product"
    )

class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True)

    email = Column(String, unique=True)

    password = Column(String)

    cart_items = relationship(
        "Cart",
        back_populates="user"
    )

    orders = relationship(
        "Order",
        back_populates="user"
    )

    addresses = relationship(
        "Address",
        back_populates="user"
    )

    is_admin = Column(
        Boolean,
        default=False
    )

    reviews = relationship(
        "Review",
        back_populates="user"
    )


class Cart(Base):

    __tablename__ = "cart"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    quantity = Column(Integer)


    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )


    product_id = Column(
        Integer,
        ForeignKey("products.id")
    )


    user = relationship(
        "User",
        back_populates="cart_items"
    )


    product = relationship(
        "Product",
        back_populates="cart_items"
    )

    
class Order(Base):

    __tablename__ = "orders"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    total_price = Column(
        Float
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )


    user = relationship(
    "User",
    back_populates="orders"
    )


    items = relationship(
        "OrderItem",
        back_populates="order"
    )

class OrderItem(Base):

    __tablename__ = "order_items"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    quantity = Column(
        Integer
    )


    order_id = Column(
        Integer,
        ForeignKey("orders.id")
    )


    product_id = Column(
        Integer,
        ForeignKey("products.id")
    )


    order = relationship(
        "Order",
        back_populates="items"
    )


    product = relationship(
        "Product",
        back_populates="order_items"
    )
class Review(Base):

    __tablename__ = "reviews"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    comment = Column(
        String
    )


    rating = Column(
        Integer
    )


    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )


    product_id = Column(
        Integer,
        ForeignKey("products.id")
    )


    user = relationship(
        "User",
        back_populates="reviews"
    )


    product = relationship(
        "Product",
        back_populates="reviews"
    )

class Address(Base):

    __tablename__ = "addresses"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    full_name = Column(String)

    phone = Column(String)

    address_line = Column(String)

    city = Column(String)

    state = Column(String)

    pincode = Column(String)

    user = relationship(
        "User",
        back_populates="addresses"
    )