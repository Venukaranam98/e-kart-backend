# Local Setup & Installation Guide

Complete instructions for installing and running the E-Kart backend locally.

---

## Prerequisites

- **Python**: Version `3.11` or higher
- **PostgreSQL**: Local or cloud instance (PostgreSQL 14+)
- **Redis**: Local server or Upstash Redis URL

---

## Installation Steps

### 1. Clone Project
```bash
git clone https://github.com/vk-09857/e-kart-backend.git
cd e-kart-backend
```

### 2. Set Up Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Create Local `.env` Configuration
Copy environment variables template:
```bash
cp .env.example .env
```
Fill in database and secret key values.

### 5. Run Database Migrations
```bash
alembic upgrade head
```

### 6. Start Development Server
```bash
uvicorn main:app --reload --port 8000
```

Access Swagger UI documentation at: `http://localhost:8000/docs`
