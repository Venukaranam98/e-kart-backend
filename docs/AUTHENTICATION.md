# Authentication & Security Specification

The E-Kart API uses stateless **JWT (JSON Web Token)** Bearer Authentication and **Bcrypt** password hashing.

---

## Token Lifecycle Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as FastAPI Backend
    participant DB as PostgreSQL DB
    participant Redis as Redis Cache

    Client->>API: POST /login {email, password}
    API->>Redis: Check login_attempts:email
    alt Attempts >= 5
        API-->>Client: 429 Too Many Requests (Lockout 15 mins)
    else Attempts < 5
        API->>DB: Query User by Email
        API->>API: Verify Password Hash (Bcrypt)
        alt Invalid Credentials
            API->>Redis: Increment login_attempts
            API-->>Client: 401 Unauthorized
        else Valid Credentials
            API->>Redis: Reset login_attempts
            API->>API: Sign JWT Token (HS256)
            API-->>Client: 200 OK {access_token, token_type: "bearer"}
        end
    end
```

---

## 1. User Registration

- **Endpoint**: `POST /register`
- **Authentication**: None (Public)
- **Request Body**:
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "StrongPassword123"
}
```
- **Response** (Status `201 Created`):
```json
{
  "success": true,
  "message": "Registration Successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

---

## 2. User Login

- **Endpoint**: `POST /login` (also supported at `POST /auth/login`)
- **Content-Type**: `application/x-www-form-urlencoded`
- **Request Body**:
```text
username=john%40example.com&password=StrongPassword123
```
- **Response** (Status `200 OK`):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## 3. Password Reset Flow

1. **Request Reset Link**:
   - **Endpoint**: `POST /auth/forgot-password`
   - **Payload**: `{"email": "john@example.com"}`
   - Creates a 15-minute expiration token in `PasswordResetToken` table and dispatches an email via Brevo SMTP API.

2. **Complete Password Reset**:
   - **Endpoint**: `POST /auth/reset-password`
   - **Payload**: `{"token": "d9a1f2b3c4e5f6a7...", "new_password": "NewStrongPassword2026!"}`
   - Updates account password hash, marks token as used, and sends confirmation email.

---

## 4. Protected Request Example

In all protected API calls, include the JWT token in the `Authorization` request header:

```http
GET /profile HTTP/1.1
Host: e-kart-backend-qyf8.onrender.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
