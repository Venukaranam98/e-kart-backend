import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.session import Base, get_db
from main import app
from models import Cart, Product, User
from redis_client import redis_client
from services.idempotency_service import IdempotencyService, generate_request_hash

TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test_idempotency.db"

engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create fresh database tables for each test run and teardown after."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    test_user = User(
        username="testuser_idem",
        email="testuser_idem@example.com",
        password="hashedpassword123",
        is_admin=False,
    )
    test_product = Product(
        title="Test Gadget",
        description="High tech gadget",
        price=100.0,
        category="Tech",
        stock=10,
    )
    db.add(test_user)
    db.add(test_product)
    db.commit()
    db.refresh(test_user)
    db.refresh(test_product)

    cart_item = Cart(
        user_id=test_user.id,
        product_id=test_product.id,
        quantity=2,
    )
    db.add(cart_item)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_idempotency.db"):
        try:
            os.remove("./test_idempotency.db")
        except Exception:
            pass


def get_auth_token():
    """Helper to mock current user JWT dependency."""
    from core.security import create_access_token
    return create_access_token(data={"sub": "testuser_idem@example.com"})


def test_missing_idempotency_header_returns_400():
    """Verify that requests missing the Idempotency-Key header return 400 Bad Request."""
    token = get_auth_token()
    response = client.post(
        "/checkout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "Idempotency-Key header is required" in str(response.json())


def test_checkout_single_and_duplicate_request():
    """Verify single request succeeds and repeated request with same key returns cached response."""
    token = get_auth_token()
    idem_key = str(uuid.uuid4())
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": idem_key,
    }

    # First request
    resp1 = client.post("/checkout", headers=headers)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["message"] == "Order placed successfully"
    order_id = data1["order_id"]

    # Second request with SAME Idempotency-Key
    resp2 = client.post("/checkout", headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.json()

    # Must return exact same response and order_id without creating a new order
    assert data2["order_id"] == order_id
    assert data2["total_price"] == data1["total_price"]


def test_payment_order_idempotency():
    """Verify Razorpay payment order creation idempotency."""
    idem_key = str(uuid.uuid4())
    headers = {"Idempotency-Key": idem_key}
    payload = {"amount": 500}

    # First call
    resp1 = client.post("/create-payment-order", json=payload, headers=headers)
    assert resp1.status_code == 200
    order1 = resp1.json()

    # Second call with same key
    resp2 = client.post("/create-payment-order", json=payload, headers=headers)
    assert resp2.status_code == 200
    order2 = resp2.json()

    # Must return exact same payload
    assert order1 == order2


def test_razorpay_webhook_idempotency():
    """Verify Razorpay webhook duplicate event processing is ignored."""
    webhook_payload = {
        "event_id": "evt_test_12345",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_999",
                    "amount": 2000,
                    "status": "captured",
                }
            }
        },
    }

    # First Webhook Delivery
    resp1 = client.post("/webhooks/razorpay", json=webhook_payload)
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "success"

    # Second Webhook Delivery (Duplicate retry from Razorpay)
    resp2 = client.post("/webhooks/razorpay", json=webhook_payload)
    assert resp2.status_code == 200
    assert resp2.json()["event_id"] == "evt_test_12345"


def test_redis_failure_fallback(monkeypatch):
    """Verify that system operates correctly via Postgres DB when Redis is unavailable."""
    # Simulate Redis failure by patching redis_client.get and set to raise/return None
    monkeypatch.setattr(redis_client, "get", lambda name: None)
    monkeypatch.setattr(redis_client, "set", lambda name, val, ex=None: False)

    idem_key = str(uuid.uuid4())
    headers = {"Idempotency-Key": idem_key}
    payload = {"amount": 750}

    # First request works via DB
    resp1 = client.post("/create-payment-order", json=payload, headers=headers)
    assert resp1.status_code == 200
    data1 = resp1.json()

    # Second request works via DB fallback
    resp2 = client.post("/create-payment-order", json=payload, headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data1 == data2
