import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.session import Base, get_db
from main import app
from models import Order, OrderItem, Product, User

TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test_cancellation.db"

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

    # User 1 (Owner)
    user1 = User(
        id=1,
        username="buyer_one",
        email="buyer_one@example.com",
        password="hashedpassword123",
        is_admin=False,
    )
    # User 2 (Other User)
    user2 = User(
        id=2,
        username="buyer_two",
        email="buyer_two@example.com",
        password="hashedpassword123",
        is_admin=False,
    )
    # Product with initial stock of 10
    product = Product(
        id=101,
        title="Gaming Laptop",
        description="High-end laptop",
        price=75000.0,
        category="Laptops",
        stock=10,
    )
    db.add_all([user1, user2, product])
    db.commit()

    # Processing order (quantity 2)
    order_processing = Order(
        id=1,
        user_id=user1.id,
        total_price=150000.0,
        status="PROCESSING",
    )
    db.add(order_processing)
    db.commit()
    item_processing = OrderItem(
        order_id=order_processing.id,
        product_id=product.id,
        quantity=2,
    )
    db.add(item_processing)

    # Shipped order
    order_shipped = Order(
        id=2,
        user_id=user1.id,
        total_price=75000.0,
        status="SHIPPED",
    )
    db.add(order_shipped)
    db.commit()
    item_shipped = OrderItem(
        order_id=order_shipped.id,
        product_id=product.id,
        quantity=1,
    )
    db.add(item_shipped)

    # Delivered order
    order_delivered = Order(
        id=3,
        user_id=user1.id,
        total_price=75000.0,
        status="DELIVERED",
    )
    db.add(order_delivered)
    db.commit()

    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_cancellation.db"):
        try:
            os.remove("./test_cancellation.db")
        except Exception:
            pass


def get_token(email: str = "buyer_one@example.com"):
    from core.security import create_access_token
    return create_access_token(data={"sub": email})


def test_cancel_processing_order_success():
    """Processing order is cancelled immediately and stock is restored."""
    token = get_token("buyer_one@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    db = TestingSessionLocal()
    initial_stock = db.query(Product).filter(Product.id == 101).first().stock
    assert initial_stock == 10
    db.close()

    response = client.post("/orders/1/cancel", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "CANCELLED"
    assert data["order_id"] == 1
    assert "successfully" in data["message"].lower()

    # Verify DB status
    db = TestingSessionLocal()
    cancelled_order = db.query(Order).filter(Order.id == 1).first()
    assert cancelled_order.status == "CANCELLED"

    # Verify stock restored by quantity 2 (10 + 2 = 12)
    updated_stock = db.query(Product).filter(Product.id == 101).first().stock
    assert updated_stock == 12
    db.close()


def test_cancel_already_cancelled_order_rejected():
    """Attempting to cancel an already cancelled order returns 400 and does NOT restore stock twice."""
    token = get_token("buyer_one@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Cancel first time
    resp1 = client.post("/orders/1/cancel", headers=headers)
    assert resp1.status_code == 200

    db = TestingSessionLocal()
    stock_after_first = db.query(Product).filter(Product.id == 101).first().stock
    assert stock_after_first == 12
    db.close()

    # Cancel second time (repeated click)
    resp2 = client.post("/orders/1/cancel", headers=headers)
    assert resp2.status_code == 400
    assert "already cancelled" in resp2.text.lower()

    # Stock must NOT be restored a second time
    db = TestingSessionLocal()
    stock_after_second = db.query(Product).filter(Product.id == 101).first().stock
    assert stock_after_second == 12
    db.close()


def test_cancel_shipped_order_rejected():
    """Shipped orders cannot be cancelled."""
    token = get_token("buyer_one@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/orders/2/cancel", headers=headers)
    assert response.status_code == 400
    assert "shipped" in response.text.lower()

    # Verify status unchanged in DB
    db = TestingSessionLocal()
    order = db.query(Order).filter(Order.id == 2).first()
    assert order.status == "SHIPPED"
    db.close()


def test_cancel_delivered_order_rejected():
    """Delivered orders cannot be cancelled."""
    token = get_token("buyer_one@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/orders/3/cancel", headers=headers)
    assert response.status_code == 400
    assert "delivered" in response.text.lower()


def test_cancel_order_unauthorized():
    """Unauthenticated request is rejected with 401."""
    response = client.post("/orders/1/cancel")
    assert response.status_code == 401


def test_cancel_other_user_order_forbidden():
    """Users cannot cancel orders belonging to other users."""
    token_user2 = get_token("buyer_two@example.com")
    headers = {"Authorization": f"Bearer {token_user2}"}

    response = client.post("/orders/1/cancel", headers=headers)
    assert response.status_code == 403
    assert "not authorized" in response.text.lower()


def test_cancel_nonexistent_order():
    """Non-existent order returns 404."""
    token = get_token("buyer_one@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/orders/9999/cancel", headers=headers)
    assert response.status_code == 404

