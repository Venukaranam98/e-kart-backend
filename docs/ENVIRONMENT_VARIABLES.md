# Environment Variables Reference

Complete documentation for all environment variables used by the E-Kart backend.

---

## Environment Matrix

| Variable Name | Type | Required | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `DATABASE_URL` | String | Yes | PostgreSQL connection URI | `postgresql://user:pass@localhost:5432/ekart_db` |
| `SECRET_KEY` | String | Yes | Cryptographic secret for signing JWTs | `a9f8b7c6d5e4f3a21...` |
| `ALGORITHM` | String | No | JWT signing algorithm (default `HS256`) | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Integer | No | Token lifetime (default `60`) | `60` |
| `REDIS_URL` | String | Yes | Redis connection string for caching | `redis://localhost:6379/0` |
| `REDIS_HOST` | String | Optional | Redis host name | `localhost` |
| `REDIS_PORT` | Integer | Optional | Redis port number | `6379` |
| `CACHE_EXPIRE` | Integer | No | Redis cache expiration in seconds (default `3600`) | `3600` |
| `RAZORPAY_KEY_ID` | String | Yes | Razorpay API Key ID | `rzp_test_SeuwTZHoUlo6gg` |
| `RAZORPAY_KEY_SECRET` | String | Yes | Razorpay API Key Secret | `your_razorpay_secret` |
| `CLOUDINARY_CLOUD_NAME` | String | Yes | Cloudinary Cloud Name | `dwdvdags5` |
| `CLOUDINARY_API_KEY` | String | Yes | Cloudinary API Key | `123456789012345` |
| `CLOUDINARY_API_SECRET` | String | Yes | Cloudinary API Secret | `your_cloudinary_secret` |
| `SMTP_HOST` | String | Yes | Brevo SMTP relay host | `smtp-relay.brevo.com` |
| `SMTP_PORT` | Integer | No | SMTP port (default `587`) | `587` |
| `SMTP_USERNAME` | String | Yes | Brevo SMTP login username | `7fb21c001@smtp-brevo.com` |
| `SMTP_PASSWORD` | String | Yes | Brevo SMTP login password | `your_smtp_password` |
| `EMAIL_FROM` | String | Yes | Sender email address | `noreply@ekarthub.com` |
| `SMTP_FROM_NAME` | String | No | Sender displayed name | `EKARTHUB` |
