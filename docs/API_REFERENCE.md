# E-Kart API Technical Reference

## Base URLs

- **Production API**: `https://e-kart-backend-qyf8.onrender.com`
- **Development API**: `http://localhost:8000`

---

## Global Headers

| Header Name | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `Content-Type` | String | Must be set to `application/json` (except for `multipart/form-data` uploads). | Yes (POST/PUT) |
| `Authorization` | String | Bearer token format: `Bearer <JWT_TOKEN>`. | Yes (Protected routes) |
| `Accept` | String | Should be `application/json`. | Optional |

---

## Endpoint Categorization Matrix

### 1. Authentication (`/register`, `/login`, `/auth/...`)
- `POST /register`: Register a new user account.
- `POST /login`: Authenticate user and issue JWT access token.
- `POST /auth/forgot-password`: Request email password reset link.
- `POST /auth/reset-password`: Complete password reset using token.
- `POST /auth/logout`: Terminate session.
- `GET /profile`: Retrieve current user profile details.
- `GET /admin/profile`: Retrieve current admin profile details.

### 2. Products Catalog (`/products...`)
- `GET /products`: List products with pagination.
- `GET /products/filter`: Filter by category, price, and sorting.
- `GET /products/{id}`: Get detailed product info.
- `GET /products/search/`: Keyword search.
- `GET /products/category/{category_name}`: Filter by category name.
- `POST /products`: Create product (Admin only).
- `PUT /products/{id}`: Update product (Admin only).
- `DELETE /products/{id}`: Delete product (Admin only).
- `POST /products/{id}/view`: Record user product view history.
- `GET /products/recent/viewed`: Fetch user recently viewed products.
- `POST /products/{id}/review`: Add product rating & review.
- `POST /upload-image`: Upload image file to Cloudinary CDN (Admin only).

### 3. Shopping Cart (`/cart...`)
- `GET /cart`: Fetch authenticated user's cart items.
- `POST /cart`: Add product item or increment quantity in cart.
- `PUT /cart/{cart_id}`: Update cart item quantity count.
- `DELETE /cart/{cart_id}`: Remove single item from cart.
- `DELETE /cart/clear`: Remove all items from user cart.

### 4. Orders & Checkout (`/checkout`, `/orders...`)
- `POST /checkout`: Convert cart items to a new placed order.
- `GET /orders`: Retrieve order placement history.
- `PUT /orders/{id}/status`: Update order fulfillment status (SHIPPED, DELIVERED, CANCELLED).

### 5. Delivery Address (`/address...`)
- `GET /address`: Fetch user's saved shipping addresses.
- `POST /address`: Save new delivery address.
- `PUT /address/{id}`: Update existing delivery address.
- `DELETE /address/{id}`: Delete delivery address.

### 6. Wishlist (`/wishlist...`)
- `GET /wishlist`: Fetch user's saved wishlist products.
- `POST /wishlist`: Save product to wishlist.
- `DELETE /wishlist/{wishlist_id}`: Remove item by wishlist ID.
- `DELETE /wishlist/product/{product_id}`: Remove item by product ID.
- `DELETE /wishlist`: Clear all wishlist items.

### 7. Payments (`/create-payment-order`, `/verify-payment`)
- `POST /create-payment-order`: Initialize Razorpay payment order.
- `POST /verify-payment`: Verify HMAC SHA256 payment signature.

### 8. Admin Management (`/admin/...`)
- `GET /admin/dashboard`: Platform statistics & revenue metrics.
- `GET /admin/orders`: View all platform orders with customer details.
- `PUT /admin/orders/{id}/status`: Update order status & send email.
- `GET /admin/users`: View all registered users list.

### 9. System Health (`/health`)
- `GET /health`: Verify system health & PostgreSQL database status.
