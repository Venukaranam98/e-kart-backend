"""Main FastAPI application entry point for E-Kart backend."""

import logging
import os
from typing import Any

import razorpay
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
from db.session import engine, get_db
from models import User
from routers import (
    address,
    admin,
    auth,
    cart,
    health,
    orders,
    payments,
    products,
    wishlist,
)
from schemas import OrderRequest

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Razorpay Client
razorpay_key_id = os.getenv("RAZORPAY_KEY_ID", "")
razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))

# Initialize FastAPI App
app = FastAPI(title="E-Kart API", version="1.0.0")

# Configure CORS Middleware
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://e-kart-one.vercel.app",
    "https://ekart-admin-panel.pages.dev",
    "https://e-kart-frontend.pages.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health.router)
app.include_router(products.router)
app.include_router(auth.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(address.router)
app.include_router(admin.router)
app.include_router(wishlist.router)

# Database Startup Metadata Creation
try:
    models.Base.metadata.create_all(bind=engine)
    logger.info("[Database] Tables created/verified successfully.")
except Exception as e:
    logger.warning(
        f"[Database Warning] Table creation skipped or failed on startup: {e}"
    )


@app.get("/")
def home() -> dict[str, str]:
    """Root health check endpoint."""
    return {"message": "E-KART Backend Running"}


@app.post("/create-order")
def create_order(data: OrderRequest) -> dict[str, Any]:
    """Legacy endpoint for creating Razorpay payment orders."""
    order = client.order.create(
        {
            "amount": data.amount * 100,
            "currency": "INR",
            "payment_capture": 1,
        }
    )
    return order


@app.get("/users")
def get_users(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Legacy public endpoint returning registered user list."""
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
        }
        for user in users
    ]
