# E-Kart Backend

A high-performance FastAPI backend for the E-Kart e-commerce platform, providing secure RESTful APIs for user authentication, product management, cart and wishlist operations, order fulfillment, Razorpay payments, transactional emails, and Redis caching.

## Live Demo

Backend API: https://e-kart-backend-qyf8.onrender.com  
API Documentation (Swagger UI): https://e-kart-backend-qyf8.onrender.com/docs

---

## Features

### Authentication & Authorization

* User Registration & Login
* Forgot Password & Reset Password Email Workflow
* Protected Routes with JWT Bearer Authentication
* Role-Based Access Control (User & Admin Roles)
* Secure Password Hashing with Bcrypt
* Login Rate Limiting & Brute-Force Attack Protection via Redis

### Products & Catalog

* Product CRUD Management
* Category Filtering, Search & Sorting
* Pagination & Price Filtering
* Cloudinary Image CDN Integration for Product Media
* Redis Caching for Product List & Product Details (Cache-Aside Pattern)
* User Recently Viewed Products Tracking via Redis Lists

### Shopping Cart

* User-Specific Global Cart Operations (Add, Update Quantity, Delete)
* Real-Time Total & Item Count Calculation
* Redis Caching for High-Speed Cart Access

### Wishlist

* Save Favorite Products
* View Saved Wishlist Items
* Seamless Item Transfer to Cart

### Address Management

* Multiple Saved Delivery Addresses per User
* Add, Edit, and Retrieve User Delivery Addresses
* Address Selection during Order Placement

### Orders & Payment Integration

* Order Placement with Real-Time Total Calculation
* Order Status Tracking (PROCESSING, SHIPPED, DELIVERED, CANCELLED)
* Razorpay Payment Gateway Integration (Order Creation & Signature Verification)
* Support for Cash on Delivery (COD) & Online Payments

### Email Notifications & Async Tasks

* Asynchronous Transactional Email Delivery via Brevo (Sendinblue) API
* Password Reset Email Link Delivery with Expiration Tokens
* Non-Blocking Execution with FastAPI BackgroundTasks & Celery Worker Support

### System Health & Administration

* Admin Endpoints for User, Order, and Product Administration
* System Health Check Endpoint (`/health`) for Database & Redis Status Verification

---

## Tech Stack

* Python 3.11+
* FastAPI
* SQLAlchemy 2 (ORM)
* PostgreSQL / SQLite
* Redis & Upstash Redis
* Pydantic v2
* PyJWT & Passlib (Bcrypt)
* Brevo (Sendinblue) SMTP API
* Razorpay Python SDK
* Cloudinary Python SDK
* Celery & FastAPI BackgroundTasks
* Uvicorn & Docker

---

## Installation

### 1. Clone the Repository

```bash
git clone <backend-repository-url>

cd backend
```

### 2. Create and Activate Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
uvicorn main:app --reload
```

---

## Environment Variables

Create a `.env` file in the `backend` root directory:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/ekart_db

# Security & Authentication
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Razorpay Payment Gateway
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

# Cloudinary Image Storage
CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret

# Redis Cache Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
CACHE_EXPIRE=3600
REDIS_URL=your_redis_connection_url

# Celery Configuration (Optional)
CELERY_BROKER_URL=your_redis_url
CELERY_RESULT_BACKEND=your_redis_url

# Email Service (Brevo SMTP API)
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USERNAME=your_brevo_smtp_username
SMTP_PASSWORD=your_brevo_smtp_password
EMAIL_FROM=your_verified_sender_email@domain.com
SMTP_FROM_NAME=EKARTHUB
```

---

## Folder Structure

```text
backend/
├── routers/
│   ├── address.py
│   ├── admin.py
│   ├── auth.py
│   ├── cart.py
│   ├── health.py
│   ├── orders.py
│   ├── payments.py
│   ├── products.py
│   └── wishlist.py
├── services/
│   └── email_service.py
├── tasks/
│   └── email_tasks.py
├── utils/
│   └── token.py
├── celery_app.py
├── database.py
├── Dockerfile
├── hashing.py
├── jwt_handler.py
├── main.py
├── models.py
├── redis_client.py
├── requirements.txt
├── runtime.txt
├── schemas.py
└── README.md
```

---

## Project Architecture

The backend follows a domain-driven, modular RESTful API architecture:
* **Routers (`routers/`)**: Expressive, feature-focused API endpoints (auth, products, cart, wishlist, orders, payments, address, admin, health).
* **Database Models & ORM (`models.py`, `database.py`, `schemas.py`)**: Declarative SQLAlchemy models with Pydantic request/response schemas for data validation and sanitization.
* **Caching & Rate Limiting (`redis_client.py`)**: Cache-Aside pattern for high-frequency queries (products, cart) and Redis-backed rate limiting for login security.
* **Service & Task Layer (`services/`, `tasks/`)**: Modular email service leveraging Brevo SMTP API integrated with FastAPI `BackgroundTasks` for non-blocking asynchronous email delivery.
* **Security & Auth (`jwt_handler.py`, `hashing.py`)**: Stateless JWT authorization headers with salted Bcrypt password hashing.