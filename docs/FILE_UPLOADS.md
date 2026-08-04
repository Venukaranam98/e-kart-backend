# Cloudinary File Uploads Specification

The E-Kart backend integrates Cloudinary Python SDK for image media uploads.

---

## Upload Endpoint Overview

- **Endpoint**: `POST /upload-image`
- **Access Control**: Admin Only (`is_admin=True`)
- **Content-Type**: `multipart/form-data`
- **Form Field**: `file`

---

## Supported Specifications

- **Allowed Formats**: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`
- **Recommended File Size**: `< 5 MB`
- **Cloudinary Storage Folder**: `ekart/`

---

## cURL Example

```bash
curl -X POST "https://e-kart-backend-qyf8.onrender.com/upload-image" \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>" \
  -F "file=@/path/to/product-photo.png"
```

---

## Response Output

```json
{
  "success": true,
  "message": "Image uploaded successfully",
  "data": {
    "image_url": "https://res.cloudinary.com/dwdvdags5/image/upload/v1780316665/ekart/sample_photo.webp"
  }
}
```
