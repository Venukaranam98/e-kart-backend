# Comprehensive Endpoints Directory

This document contains explicit endpoint definitions across all 9 application modules.

---

## 1. Authentication Endpoints

### `POST /register`
- **Summary**: Register New User Account
- **Access**: Public
- **Status Code**: `201 Created`
- **Request Body**: `UserSchema` (`username`, `email`, `password`)
- **Responses**: `201 Created`, `400 Bad Request` (Email already registered), `422 Unprocessable Entity`.

### `POST /login`
- **Summary**: User Login
- **Access**: Public
- **Status Code**: `200 OK`
- **Form Data**: `username` (email), `password`
- **Responses**: `200 OK`, `401 Unauthorized`, `404 Not Found`, `429 Too Many Requests`.

### `POST /auth/forgot-password`
- **Summary**: Request Password Reset Email Link
- **Access**: Public
- **Request Body**: `ForgotPasswordRequest` (`email`)
- **Responses**: `200 OK`.

### `POST /auth/reset-password`
- **Summary**: Reset Password with Token
- **Access**: Public
- **Request Body**: `ResetPasswordRequest` (`token`, `new_password`)
- **Responses**: `200 OK`, `400 Bad Request` (Token invalid or expired).

### `GET /profile`
- **Summary**: Get Authenticated User Profile
- **Access**: User (`Bearer Token`)
- **Responses**: `200 OK`, `401 Unauthorized`.

---

## 2. Product Catalog Endpoints

### `GET /products`
- **Summary**: List Paginated Products
- **Query Params**: `page` (default `1`), `limit` (default `5`)
- **Caching**: 1 Hour in Redis (`products:page:X:limit:Y`).

### `GET /products/filter`
- **Summary**: Filter & Sort Products
- **Query Params**: `category`, `min_price`, `max_price`, `sort` (`low_to_high` | `high_to_low`)

### `GET /products/{product_id}`
- **Summary**: Get Single Product Details
- **Path Params**: `product_id` (integer)

### `GET /products/search/`
- **Summary**: Search Products by Title
- **Query Params**: `query` (string keyword)

### `GET /products/category/{category_name}`
- **Summary**: Get Products in Category
- **Path Params**: `category_name` (string)

### `POST /products` (Admin Only)
- **Summary**: Add New Product to Store Catalog
- **Access**: Admin (`is_admin=True`)

### `PUT /products/{product_id}` (Admin Only)
- **Summary**: Update Product Attributes
- **Access**: Admin (`is_admin=True`)

### `DELETE /products/{product_id}` (Admin Only)
- **Summary**: Delete Product
- **Access**: Admin (`is_admin=True`)

### `POST /upload-image` (Admin Only)
- **Summary**: Upload Image File to Cloudinary CDN
- **Access**: Admin (`is_admin=True`)
- **Body**: `multipart/form-data` file payload.

---

## 3. Shopping Cart Endpoints

### `GET /cart`
- **Summary**: Get User Shopping Cart
- **Access**: User

### `POST /cart`
- **Summary**: Add Product to Cart / Increment Quantity
- **Access**: User
- **Request Body**: `{"product_id": 1, "quantity": 2}`

### `PUT /cart/{cart_id}`
- **Summary**: Update Cart Item Quantity
- **Access**: User

### `DELETE /cart/{cart_id}`
- **Summary**: Remove Item from Cart
- **Access**: User

### `DELETE /cart/clear`
- **Summary**: Empty Shopping Cart
- **Access**: User

---

## 4. Orders Endpoints

### `POST /checkout`
- **Summary**: Checkout Cart and Place Order
- **Access**: User

### `GET /orders`
- **Summary**: Fetch Order History
- **Access**: User / Admin

### `PUT /orders/{order_id}/status`
- **Summary**: Update Order Status & Queue Email Notification
- **Access**: Admin / User

---

## 5. Address Endpoints

### `GET /address`
- **Summary**: Get User Shipping Addresses
- **Access**: User

### `POST /address`
- **Summary**: Save New Shipping Address
- **Access**: User

### `PUT /address/{address_id}`
- **Summary**: Edit Shipping Address
- **Access**: User

### `DELETE /address/{address_id}`
- **Summary**: Delete Shipping Address
- **Access**: User

---

## 6. Wishlist Endpoints

### `GET /wishlist`
- **Summary**: Get User Wishlist
- **Access**: User

### `POST /wishlist`
- **Summary**: Save Product to Wishlist
- **Access**: User

### `DELETE /wishlist/{wishlist_id}`
- **Summary**: Remove Wishlist Item by ID
- **Access**: User

---

## 7. Payments Endpoints

### `POST /create-payment-order`
- **Summary**: Create Razorpay Order ID
- **Access**: User / Public

### `POST /verify-payment`
- **Summary**: Verify Razorpay Digital Signature
- **Access**: User / Public

---

## 8. Admin Endpoints

### `GET /admin/dashboard`
- **Summary**: Platform Overview Metrics
- **Access**: Admin

### `GET /admin/orders`
- **Summary**: Fetch All Platform Orders
- **Access**: Admin

### `GET /admin/users`
- **Summary**: Fetch All User Accounts
- **Access**: Admin

---

## 9. Health Endpoint

### `GET /health`
- **Summary**: System & DB Health Status Check
- **Access**: Public
