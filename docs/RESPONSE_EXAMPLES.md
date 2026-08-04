# Sample JSON Responses Directory

Representative JSON payloads returned by E-Kart backend endpoints.

---

## 1. Authentication & Profile Responses

### `POST /register`
```json
{
  "success": true,
  "message": "Registration Successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huQGV4YW1wbGUuY29tIn0...",
    "token_type": "bearer"
  }
}
```

### `GET /profile`
```json
{
  "success": true,
  "message": "Profile fetched successfully",
  "data": {
    "id": 42,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

---

## 2. Product Catalog Responses

### `GET /products?page=1&limit=2`
```json
{
  "success": true,
  "message": "Products fetched successfully",
  "data": [
    {
      "id": 1,
      "title": "ONEPLUS 15R",
      "description": "Experience ultra-fast performance with flagship Snapdragon processor.",
      "price": 59999.0,
      "image": "https://res.cloudinary.com/dwdvdags5/image/upload/v1780316665/ekart/thgozxpt6vxonsdaz8ba.webp",
      "category": "Mobiles"
    },
    {
      "id": 2,
      "title": "IPHONE 15 PRO",
      "description": "Titanium design with A17 Pro chip and customizable Action button.",
      "price": 134900.0,
      "image": "https://res.cloudinary.com/dwdvdags5/image/upload/v1780317112/ekart/cd29pm8b7nslyespb6wi.webp",
      "category": "Mobiles"
    }
  ]
}
```

---

## 3. Cart & Order Responses

### `GET /cart`
```json
{
  "success": true,
  "message": "Cart fetched successfully",
  "data": [
    {
      "cart_id": 10,
      "product_title": "ONEPLUS 15R",
      "price": 59999.0,
      "image": "https://res.cloudinary.com/dwdvdags5/image/upload/v1780316665/ekart/thgozxpt6vxonsdaz8ba.webp",
      "category": "Mobiles",
      "quantity": 2
    }
  ]
}
```

### `POST /checkout`
```json
{
  "message": "Order placed successfully",
  "order_id": 101,
  "total_price": 119998.0,
  "status": "PROCESSING"
}
```

---

## 4. Admin Dashboard Metrics

### `GET /admin/dashboard`
```json
{
  "total_users": 150,
  "total_products": 45,
  "total_orders": 320,
  "total_revenue": 4589000.0
}
```
