# E-Kart API Documentation Hub

Welcome to the official technical documentation repository for the **E-Kart Backend RESTful API**.

## Live API Interactive Links

- **Swagger UI**: [https://e-kart-backend-qyf8.onrender.com/docs](https://e-kart-backend-qyf8.onrender.com/docs)
- **ReDoc Documentation**: [https://e-kart-backend-qyf8.onrender.com/redoc](https://e-kart-backend-qyf8.onrender.com/redoc)
- **OpenAPI Schema Specification**: [https://e-kart-backend-qyf8.onrender.com/openapi.json](https://e-kart-backend-qyf8.onrender.com/openapi.json)

---

## Documentation Index

| Documentation Guide | Description |
| :--- | :--- |
| [API Reference](./API_REFERENCE.md) | Overview of base URLs, request/response formats, and endpoint matrix. |
| [Authentication Guide](./AUTHENTICATION.md) | Complete JWT Bearer workflow, registration, login, logout, and password recovery. |
| [Endpoints Matrix](./ENDPOINTS.md) | Comprehensive specification for all 25+ API endpoints. |
| [Error Codes](./ERROR_CODES.md) | HTTP status codes, error payload schemas, rate limits, and troubleshooting. |
| [Request Examples](./REQUEST_EXAMPLES.md) | Code snippets in cURL, JavaScript (Axios/Fetch), and Python. |
| [Response Examples](./RESPONSE_EXAMPLES.md) | Sample JSON responses for success, validation, and error states. |
| [Pagination Guide](./PAGINATION.md) | Page and limit query parameters, Redis caching behavior, and pagination schemas. |
| [Search & Filtering](./SEARCH.md) | Product search keywords, price range filtering, category filtering, and sorting modes. |
| [File Uploads](./FILE_UPLOADS.md) | Cloudinary CDN image uploads, supported MIME types, size limits, and security. |
| [Admin APIs](./ADMIN_APIS.md) | Restricted administrative endpoints, role-based access control, metrics, and user management. |
| [Local Setup Guide](./SETUP.md) | Step-by-step guide for local development, virtual environment, and database migrations. |
| [Deployment Guide](./DEPLOYMENT.md) | Containerization with Docker, Render deployment, environment configurations, and production checklist. |
| [Environment Variables](./ENVIRONMENT_VARIABLES.md) | Complete configuration matrix for PostgreSQL, Redis, Brevo SMTP, Cloudinary, and Razorpay. |
| [Architecture Overview](./ARCHITECTURE.md) | Technical architecture diagram, database schema, Cache-Aside pattern, and Celery async workers. |
| [Changelog](./CHANGELOG.md) | API version release history and stability notes. |

---

## Architecture & Technology Summary

- **Framework**: FastAPI (Python 3.11+)
- **Database & ORM**: PostgreSQL with SQLAlchemy 2 ORM & Pydantic v2 validation
- **Caching & Rate Limiting**: Redis & Upstash Redis Cache-Aside pattern
- **Asynchronous Tasks**: Celery & FastAPI BackgroundTasks
- **Media CDN**: Cloudinary Python SDK
- **Payment Gateway**: Razorpay Python SDK & digital signature verification
- **Transactional Email**: Brevo (Sendinblue) SMTP API
