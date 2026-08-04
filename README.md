# E-Kart Production REST API

A high-performance FastAPI backend for the E-Kart e-commerce platform, providing secure RESTful APIs for user authentication, product management, cart and wishlist operations, order fulfillment, Razorpay payments, transactional emails, and Redis caching.

---

## Interactive API Documentation Links

- **Swagger UI**: [https://e-kart-backend-qyf8.onrender.com/docs](https://e-kart-backend-qyf8.onrender.com/docs)
- **ReDoc Technical Manual**: [https://e-kart-backend-qyf8.onrender.com/redoc](https://e-kart-backend-qyf8.onrender.com/redoc)
- **OpenAPI Schema (JSON)**: [https://e-kart-backend-qyf8.onrender.com/openapi.json](https://e-kart-backend-qyf8.onrender.com/openapi.json)
- **Documentation Hub**: [docs/README.md](./docs/README.md)
- **Postman Collection**: [postman/E-Kart.postman_collection.json](./postman/E-Kart.postman_collection.json)

---

## Features

### Authentication & Security
- User Registration & Login
- Password Reset Workflow (15-min expiration link via Brevo SMTP API)
- Stateless JWT Bearer Token Authentication & Bcrypt Password Hashing
- Redis-backed Login Rate Limiting (5 max attempts per 15 mins)
- Interactive **Authorize 🔓** Button support in Swagger UI

### Products & Catalog Management
- Product CRUD Management (Admin restricted creation/updates)
- Keyword Search & Multi-Param Filtering (Category, Min/Max Price, Sorting)
- Cloudinary CDN Image File Uploads (`multipart/form-data`)
- Redis Cache-Aside Pattern (1 Hour Expiration)
- User Recently Viewed Products Tracking via Redis Lists

### Shopping Cart & Wishlist
- User-specific Global Cart Operations (Add, Update Quantity, Remove, Clear)
- User Wishlist Operations (Add, List, Delete by ID / Product ID)
- Real-Time Cart Calculation & Stock Reservation

### Orders & Payment Fulfillment
- Order Placement with Real-Time Total Calculation
- Order Status Tracking (`PROCESSING`, `SHIPPED`, `OUT_FOR_DELIVERY`, `DELIVERED`, `CANCELLED`)
- Automated Email Status Notifications queued via `BackgroundTasks`
- Razorpay Payment Order Creation & HMAC SHA256 Digital Signature Verification

### Administration & Metrics
- System Overview Metrics (`GET /admin/dashboard`)
- Customer Orders Directory with formatted delivery addresses
- Registered Users Directory

---

## Project Directory Layout

```text
backend/
├── constants/
│   ├── app_constants.py
│   └── __init__.py
├── core/
│   ├── security.py
│   └── __init__.py
├── db/
│   ├── session.py
│   └── __init__.py
├── dependencies/
│   ├── auth.py
│   └── __init__.py
├── docs/
│   ├── README.md
│   ├── API_REFERENCE.md
│   ├── AUTHENTICATION.md
│   ├── ENDPOINTS.md
│   ├── ERROR_CODES.md
│   ├── REQUEST_EXAMPLES.md
│   ├── RESPONSE_EXAMPLES.md
│   ├── PAGINATION.md
│   ├── SEARCH.md
│   ├── FILE_UPLOADS.md
│   ├── ADMIN_APIS.md
│   ├── SETUP.md
│   ├── DEPLOYMENT.md
│   ├── ENVIRONMENT_VARIABLES.md
│   ├── ARCHITECTURE.md
│   └── CHANGELOG.md
├── postman/
│   ├── E-Kart.postman_collection.json
│   └── E-Kart.postman_environment.json
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

## Local Quickstart Guide

### 1. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/vk-09857/e-kart-backend.git
cd e-kart-backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Activate virtual environment (macOS/Linux)
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Development Server
```bash
uvicorn main:app --reload --port 8000
```
Swagger UI will be available at `http://localhost:8000/docs`.

---

## Environment Variables Summary

Create a `.env` file in the `backend/` directory:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/ekart_db
SECRET_KEY=your_super_secret_jwt_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret

REDIS_URL=redis://localhost:6379/0
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USERNAME=your_brevo_smtp_username
SMTP_PASSWORD=your_brevo_smtp_password
EMAIL_FROM=noreply@ekarthub.com
```

For complete technical specifications, consult [docs/README.md](./docs/README.md).