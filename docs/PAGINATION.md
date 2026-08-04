# Pagination & High-Speed Caching Guide

To ensure high performance across expansive product catalogs, the E-Kart backend implements standard page-based pagination paired with a Redis Cache-Aside pattern.

---

## Query Parameters

| Parameter | Type | Default | Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| `page` | Integer | `1` | `ge=1` | The 1-based page index to retrieve. |
| `limit` | Integer | `5` | `1..100` | Number of product items returned per page. |

---

## Endpoint Signature

```http
GET /products?page=2&limit=10 HTTP/1.1
Host: e-kart-backend-qyf8.onrender.com
```

---

## Redis Caching Mechanics

- **Cache Key Format**: `products:page:{page}:limit:{limit}`
- **Expiration TTL**: 3600 seconds (1 Hour)
- **Cache Invalidation**: Automatically flushed whenever an Admin creates (`POST /products`), updates (`PUT /products/{id}`), or deletes (`DELETE /products/{id}`) a product record.

### Cache Sequence

```text
Request (GET /products?page=1&limit=5)
   │
   ├─► Check Redis Key "products:page:1:limit:5"
   │    ├─► HIT: Return JSON payload immediately (0ms DB load)
   │    └─► MISS: Query PostgreSQL DB with offset = (page-1)*limit
   │              Store result in Redis with 1h TTL
   │              Return JSON payload to client
```
