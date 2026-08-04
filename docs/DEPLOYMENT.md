# Production Deployment Guide

Guide for deploying the E-Kart backend to cloud providers (Render, Docker, Railway).

---

## 1. Docker Deployment

A production-ready `Dockerfile` is included in the project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build & Run Container

```bash
docker build -t ekart-backend .
docker run -d -p 8000:8000 --env-file .env ekart-backend
```

---

## 2. Render Cloud Deployment

1. Connect your GitHub repository `e-kart-backend` to Render.
2. Select **Web Service**.
3. Set **Runtime** to `Python 3`.
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add Environment Variables under **Environment**:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `REDIS_URL`
   - `RAZORPAY_KEY_ID`
   - `RAZORPAY_KEY_SECRET`
   - `CLOUDINARY_CLOUD_NAME`
   - `CLOUDINARY_API_KEY`
   - `CLOUDINARY_API_SECRET`
   - `SMTP_HOST`
   - `SMTP_USERNAME`
   - `SMTP_PASSWORD`
