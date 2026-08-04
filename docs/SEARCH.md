# Product Search & Filtering Guide

The E-Kart backend supports full case-insensitive keyword searching, category taxonomy browsing, price range constraints, and price sorting strategies.

---

## 1. Full-Text Title Search

- **Endpoint**: `GET /products/search/?query={keyword}`
- **Example Request**: `GET /products/search/?query=oneplus`
- **Matching Behavior**: Case-insensitive substring matching using SQL `ILIKE '%query%'`.

---

## 2. Advanced Multi-Param Filter

- **Endpoint**: `GET /products/filter`
- **Supported Parameters**:

| Query Parameter | Type | Example | Description |
| :--- | :--- | :--- | :--- |
| `category` | String | `Mobiles` | Case-insensitive category match (`ILIKE`). |
| `min_price` | Float | `10000` | Minimum item price threshold. |
| `max_price` | Float | `80000` | Maximum item price threshold. |
| `sort` | String | `low_to_high` | Sort strategy: `low_to_high` or `high_to_low`. |

---

## 3. Example Combined Filter Request

```http
GET /products/filter?category=Mobiles&min_price=20000&max_price=90000&sort=low_to_high HTTP/1.1
Host: e-kart-backend-qyf8.onrender.com
```

### Response (`200 OK`)
```json
{
  "success": true,
  "message": "Filtered products fetched successfully",
  "data": [
    {
      "id": 1,
      "title": "ONEPLUS 15R",
      "price": 59999.0,
      "category": "Mobiles",
      "image": "https://res.cloudinary.com/demo/sample.jpg"
    }
  ]
}
```
