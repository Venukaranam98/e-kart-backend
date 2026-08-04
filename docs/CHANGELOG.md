# API Version Changelog

History of API releases, architectural updates, and documentation enhancements.

---

## [1.0.0] - 2026-08-04

### Added
- **Production-Grade OpenAPI & Swagger Metadata**:
  - Enriched OpenAPI specification with detailed route summaries, descriptions, parameter annotations, and status code response examples.
  - Injected `HTTPBearer` security scheme enabling interactive **Authorize 🔓** button in Swagger UI.
  - Organized all 25+ endpoints into explicit tags: `Authentication`, `Products`, `Cart`, `Orders`, `Addresses`, `Wishlist`, `Payments`, `Admin`, `Health`, `Legacy`.
- **Pydantic v2 Schema Enhancements**:
  - Annotated schema fields with `Field` metadata, descriptions, and realistic `json_schema_extra` request/response payload examples.
- **Documentation Suite**:
  - Created 16 dedicated markdown technical manuals in `docs/`.
  - Created Postman Collection and Environment in `postman/`.
- **Modular Codebase Architecture**:
  - Refactored backend into domain packages (`core/`, `db/`, `dependencies/`, `constants/`).
  - Added backward-compatibility re-export shims for legacy module imports.

### Security & Performance
- Rate limiting on `/login` via Redis (5 max attempts per 15 mins).
- Redis Cache-Aside pattern for `/products` and `/cart`.
- Transactional email queueing via FastAPI `BackgroundTasks`.
