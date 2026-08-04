"""Main FastAPI application entry point for E-Kart backend."""

import logging
import os
from typing import Any

import razorpay
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
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

tags_metadata = [
    {
        "name": "Authentication",
        "description": "User registration, authentication, JWT token management, profile retrieval, and password reset workflows.",
    },
    {
        "name": "Products",
        "description": "Product catalog browsing, search, filtering, category exploration, reviews, and image uploads.",
    },
    {
        "name": "Cart",
        "description": "User-specific shopping cart operations including adding items, updating quantities, and clearing cart items.",
    },
    {
        "name": "Orders",
        "description": "Order creation, checkout processing, order history retrieval, status tracking, and order cancellation.",
    },
    {
        "name": "Addresses",
        "description": "Managing user delivery addresses (creation, retrieval, updates, and deletion).",
    },
    {
        "name": "Wishlist",
        "description": "Managing saved favorite products, wishlist viewing, item removal, and quick transfers.",
    },
    {
        "name": "Payments",
        "description": "Razorpay payment order creation, digital signature verification, and transaction processing.",
    },
    {
        "name": "Admin",
        "description": "Administrative endpoints for platform metrics, user management, product curation, and order status updates.",
    },
    {
        "name": "Health",
        "description": "System health check endpoint verifying database connectivity, Redis state, and service availability.",
    },
    {
        "name": "Legacy",
        "description": "Legacy compatibility endpoints for order placement and public user lists.",
    },
]

servers = [
    {
        "url": "https://e-kart-backend-qyf8.onrender.com",
        "description": "Production Server (Render Cloud)",
    },
    {
        "url": "http://localhost:8000",
        "description": "Local Development Environment",
    },
]

# Initialize FastAPI App
app = FastAPI(
    title="E-Kart API",
    description="""
# E-Kart Production REST API

Welcome to the **E-Kart API Documentation**. E-Kart is a full-stack, enterprise-grade e-commerce platform powering modern gadget retail.

## Key Technical Features
* **Authentication**: Stateless JWT Bearer tokens with Bcrypt password hashing.
* **Product Catalog**: High-performance product search, filtering, pagination, and Cloudinary CDN image integration.
* **Caching & Speed**: Redis Cache-Aside pattern for instantaneous cart and product payload delivery.
* **Payments & Orders**: Razorpay payment gateway integration with payment signature verification and order tracking.
* **Asynchronous Notifications**: Transactional emails powered by Brevo SMTP API and Celery workers.

## Authentication Guide
To access protected endpoints:
1. Register a new user at `POST /register` or login at `POST /login`.
2. Copy the `access_token` string from the JSON response.
3. Click the **Authorize 🔓** button above.
4. Enter `Bearer <your_access_token>` in the value field (or use `OAuth2PasswordBearer`) and click **Authorize**.
""",
    version="1.0.0",
    terms_of_service="https://ekarthub.com/terms/",
    contact={
        "name": "E-Kart Engineering Team",
        "url": "https://ekarthub.com/support",
        "email": "support@ekarthub.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=tags_metadata,
    servers=servers,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


def custom_openapi() -> dict[str, Any]:
    """Custom OpenAPI schema generator preserving OAuth2PasswordBearer & HTTPBearer security schemes."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=tags_metadata,
        servers=servers,
    )

    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    sec_schemes = openapi_schema["components"].get("securitySchemes", {})
    sec_schemes["HTTPBearer"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Enter your JWT token directly to authorize requests.",
    }
    if "OAuth2PasswordBearer" in sec_schemes:
        sec_schemes["OAuth2PasswordBearer"]["flows"]["password"]["tokenUrl"] = "/login"

    openapi_schema["components"]["securitySchemes"] = sec_schemes

    # Map protected endpoints to support both OAuth2PasswordBearer and HTTPBearer in Swagger UI
    for path in openapi_schema.get("paths", {}).values():
        for method in path.values():
            if isinstance(method, dict) and "security" in method:
                method["security"] = [
                    {"OAuth2PasswordBearer": []},
                    {"HTTPBearer": []},
                ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]

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


@app.get(
    "/",
    summary="Root Service Status",
    description="Returns the operational status message for the E-Kart backend API.",
    response_description="Operational status JSON message",
    tags=["Health"],
)
def home() -> dict[str, str]:
    """Root health check endpoint."""
    return {"message": "E-KART Backend Running"}


@app.post(
    "/create-order",
    summary="Create Razorpay Payment Order (Legacy)",
    description="Legacy endpoint for initializing a Razorpay payment order for checkout.",
    response_description="Razorpay order dictionary containing order ID and amount in paise",
    tags=["Legacy"],
)
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


@app.get(
    "/users",
    summary="List Registered Users (Legacy)",
    description="Legacy endpoint returning the list of registered users in the database.",
    response_description="List of registered user records",
    tags=["Legacy"],
)
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
