# Administrative APIs Specification

Endpoints restricted exclusively to users possessing administrative privileges (`is_admin=True`).

---

## Security & Authorization

All Admin endpoints require a valid JWT Bearer token issued to an admin account. If a regular non-admin user accesses an admin endpoint, the API returns:

```json
{
  "detail": {
    "success": false,
    "message": "Admin privileges required to access this resource"
  }
}
```
**Status Code**: `403 Forbidden`

---

## Admin Endpoints Summary

### 1. `GET /admin/dashboard`
- **Description**: Returns total system metrics: registered users count, total catalog products, total orders placed, and gross revenue.

### 2. `GET /admin/orders`
- **Description**: Retrieve all customer orders platform-wide, including formatted shipping addresses and user contact information.

### 3. `PUT /admin/orders/{order_id}/status`
- **Description**: Update order fulfillment status and dispatch transactional email notifications.
- **Request Body**: `{"status": "SHIPPED"}` (Options: `PROCESSING`, `SHIPPED`, `OUT_FOR_DELIVERY`, `DELIVERED`, `CANCELLED`).

### 4. `GET /admin/users`
- **Description**: List all registered accounts with registration dates and admin status flags.

### 5. `POST /products`, `PUT /products/{id}`, `DELETE /products/{id}`
- **Description**: Manage store product catalog inventory.
