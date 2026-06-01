# E-Kart Backend

A FastAPI-powered backend for the E-Kart e-commerce platform, providing secure APIs for authentication, products, cart management, orders, addresses, reviews, and image uploads.

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

### Product Management

* Create Products
* Update Products
* Delete Products
* Product Search
* Category Filtering
* Product Details

### Cart Management

* Add to Cart
* Update Quantity
* Remove Items
* View Cart

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

## Tech Stack

* FastAPI
* SQLAlchemy
* PostgreSQL
* Pydantic
* JWT Authentication
* Cloudinary

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

### Products

* Create Product
* Get Products
* Search Products
* Filter Products
* Update Product
* Delete Product
* Upload Product Image

### Cart

* Add To Cart
* Get Cart
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

```bash
git clone <backend-repository-url>

cd backend

pip install -r requirements.txt

uvicorn main:app --reload
```

---

## Project Structure

```text
backend/
├── routers/
├── models/
├── schemas/
├── database/
├── uploads/
└── main.py
```
