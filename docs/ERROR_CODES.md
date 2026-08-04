# Standard HTTP Error Codes & Troubleshooting

The E-Kart API returns consistent JSON error structures when a request fails or validation errors occur.

---

## Error Response Payload Formats

### 1. Standard Error Format
```json
{
  "detail": {
    "success": false,
    "message": "Human-readable error explanation text."
  }
}
```

### 2. Validation Error Format (Status `422 Unprocessable Entity`)
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Status Code Reference

| Status Code | Code Name | Description | Recommended Resolution |
| :--- | :--- | :--- | :--- |
| **`200 OK`** | Success | Request succeeded cleanly. | N/A |
| **`201 Created`** | Created | Resource successfully created (e.g. registration). | N/A |
| **`400 Bad Request`** | Client Error | Malformed request, duplicate email, or empty cart checkout. | Verify request payload parameters. |
| **`401 Unauthorized`** | Authentication Required | Invalid password, missing Bearer token, or token expired. | Login to obtain a fresh JWT token. |
| **`403 Forbidden`** | Permission Denied | Authenticated user lacks `is_admin=True` role. | Contact admin for access elevation. |
| **`404 Not Found`** | Resource Missing | Product ID, order ID, or user account does not exist. | Verify target resource identifier. |
| **`422 Unprocessable Entity`** | Validation Failed | Pydantic data validation constraint failed. | Check input type, missing required fields. |
| **`429 Too Many Requests`** | Rate Limit Exceeded | More than 5 failed login attempts within 15 minutes. | Wait 15 minutes before retrying login. |
| **`500 Internal Server Error`** | Server Fault | Unexpected backend error or unhandled exception. | Check backend application error logs. |
| **`503 Service Unavailable`** | Service Disconnected | Database connectivity lost or Redis offline. | Inspect PostgreSQL / Redis instance health. |

---

## Example Error Responses

### `401 Unauthorized` (Invalid Credentials)
```json
{
  "detail": {
    "success": false,
    "message": "Invalid password. 4 attempts remaining."
  }
}
```

### `429 Too Many Requests` (Lockout)
```json
{
  "detail": {
    "success": false,
    "message": "Too many failed login attempts. Try again in 15 minutes."
  }
}
```

### `403 Forbidden` (Non-Admin User)
```json
{
  "detail": {
    "success": false,
    "message": "Admin privileges required to access this resource"
  }
}
```
