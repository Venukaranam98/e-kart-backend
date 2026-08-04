# Code Request Snippets & Examples

Code snippets for integrating with the E-Kart REST API across popular languages and environments.

---

## 1. User Login

### cURL
```bash
curl -X POST "https://e-kart-backend-qyf8.onrender.com/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john%40example.com&password=StrongPassword123"
```

### JavaScript (Axios)
```javascript
import axios from 'axios';

const loginUser = async (email, password) => {
  const params = new URLSearchParams();
  params.append('username', email);
  params.append('password', password);

  const response = await axios.post('https://e-kart-backend-qyf8.onrender.com/login', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });

  const { access_token } = response.data;
  localStorage.setItem('access_token', access_token);
  return access_token;
};
```

### Python (Requests)
```python
import requests

url = "https://e-kart-backend-qyf8.onrender.com/login"
payload = {
    "username": "john@example.com",
    "password": "StrongPassword123"
}

response = requests.post(url, data=payload)
data = response.json()
print("Access Token:", data["access_token"])
```

---

## 2. Fetch User Shopping Cart

### cURL
```bash
curl -X GET "https://e-kart-backend-qyf8.onrender.com/cart" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

### JavaScript (Fetch API)
```javascript
const getCart = async (token) => {
  const response = await fetch('https://e-kart-backend-qyf8.onrender.com/cart', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return await response.json();
};
```

---

## 3. Product Filtering & Search

### cURL
```bash
curl -X GET "https://e-kart-backend-qyf8.onrender.com/products/filter?category=Mobiles&min_price=10000&max_price=80000&sort=low_to_high"
```

### Python (Requests)
```python
import requests

url = "https://e-kart-backend-qyf8.onrender.com/products/filter"
params = {
    "category": "Mobiles",
    "min_price": 10000,
    "max_price": 80000,
    "sort": "low_to_high"
}

response = requests.get(url, params=params)
print(response.json())
```

---

## 4. Checkout Order

### cURL
```bash
curl -X POST "https://e-kart-backend-qyf8.onrender.com/checkout" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

### JavaScript (Axios)
```javascript
const checkout = async (token) => {
  const response = await axios.post('https://e-kart-backend-qyf8.onrender.com/checkout', {}, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  console.log('Order Placed:', response.data);
};
```
