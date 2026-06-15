# E-Kart Backend

A FastAPI-powered backend for the E-Kart e-commerce platform, providing secure APIs for authentication, product management, cart operations, orders, addresses, reviews, image uploads, and high-performance caching with Redis.

## Live API

Backend: https://e-kart-backend-qyf8.onrender.com

---

## Features

### Authentication

* User Registration
* User Login
* JWT Token Authentication
* Role-Based Authorization
* Admin Access Control
* Login Rate Limiting with Redis
* Brute-Force Attack Protection

### Product Management

* Create Products
* Update Products
* Delete Products
* Product Search
* Category Filtering
* Product Details
* Product Pagination
* Product Caching with Redis

### Cart Management

* Add to Cart
* Update Quantity
* Remove Items
* View Cart
* User-Specific Cart Caching

### Recently Viewed Products

* Track Recently Viewed Products
* Store User Activity with Redis Lists
* Maintain View History Order
* Automatically Remove Duplicates
* Limit History Size with Redis

### Address Management

* Add Address
* Update Address
* Retrieve User Addresses

### Orders

* Create Orders
* Order History
* Order Item Management

### Reviews

* Add Product Reviews
* Product Rating Support

### Image Uploads

* Cloudinary Integration
* Secure Image Storage
* Cloud Image URLs

---

## Redis Features

* Product List Caching
* Individual Product Caching
* Cart Caching per User
* Recently Viewed Products
* Login Rate Limiting
* Automatic Cache Invalidation
* Cache-Aside Pattern Implementation
* Redis TTL for Temporary Data

---

## Tech Stack

* FastAPI
* SQLAlchemy (ORM)
* PostgreSQL
* Redis
* Pydantic
* JWT Authentication
* Cloudinary
* Docker (Redis Container)
* Uvicorn

---

## Database Models

* User
* Product
* Cart
* Order
* OrderItem
* Address
* Review

---

## API Endpoints

### Authentication

* Register User
* Login User
* Get User Profile
* Get Admin Profile

### Products

* Create Product
* Get Products
* Get Product by ID
* Search Products
* Filter Products
* Get Products by Category
* Get Recently Viewed Products
* Update Product
* Delete Product
* Upload Product Image

### Cart

* Add to Cart
* Get Cart
* Update Cart Quantity
* Remove From Cart

### Orders

* Create Order
* Get Orders

### Address

* Create Address
* Update Address
* Get Addresses

### Reviews

* Add Review

---

## Installation

### 1. Clone the Repository

```bash
git clone <backend-repository-url>

cd backend
```

### 2. Create and Activate Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file inside the `backend` directory:

```env
DATABASE_URL=your_database_url

SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### 5. Start Redis

```bash
docker run -d --name ekart-redis -p 6379:6379 redis
```

### 6. Run the Application

```bash
uvicorn main:app --reload
```

---

## Project Structure

```text
backend/
├── routers/
│   ├── __init__.py
│   ├── address.py
│   ├── admin.py
│   ├── auth.py
│   ├── cart.py
│   ├── orders.py
│   ├── payments.py
│   └── products.py
├── .venv/
├── .env
├── .gitignore
├── database.py
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

## Performance & Security Enhancements

* Redis Cache-Aside Pattern
* Automatic Cache Invalidation on CRUD Operations
* User-Specific Redis Keys
* Login Rate Limiting with TTL
* Optimized Product Retrieval
* Reduced Database Load
* JWT-Based Authentication
* Role-Based Access Control
`