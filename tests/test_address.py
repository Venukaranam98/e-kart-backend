"""Pytest suite verifying Pydantic v2 serialization for Address endpoints."""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models
from db.session import Base, get_db
from main import app
from models import User

TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test_address.db"

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
    """Create fresh test database tables."""
    app.dependency_overrides[get_db] = override_get_db
    models.Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    test_user = User(
        username="addr_user",
        email="addr_user@example.com",
        password="hashedpassword123",
        is_admin=False,
    )
    db.add(test_user)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_address.db"):
        try:
            os.remove("./test_address.db")
        except Exception:
            pass


def get_auth_token():
    from core.security import create_access_token
    return create_access_token(data={"sub": "addr_user@example.com"})


def test_address_crud_serialization():
    """Test full CRUD cycle for /address to ensure no PydanticSerializationError is raised."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    address_payload = {
        "full_name": "Jane Doe",
        "phone": "9876543210",
        "address_line": "123 Innovation Drive",
        "city": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560001",
    }

    # 1. POST /address
    create_resp = client.post("/address", json=address_payload, headers=headers)
    assert create_resp.status_code == 200, create_resp.text
    create_data = create_resp.json()
    assert create_data["message"] == "Address saved"
    assert "address" in create_data
    address_id = create_data["address"]["id"]
    assert create_data["address"]["full_name"] == "Jane Doe"

    # 2. GET /address
    get_resp = client.get("/address", headers=headers)
    assert get_resp.status_code == 200, get_resp.text
    addresses_data = get_resp.json()
    assert isinstance(addresses_data, list)
    assert len(addresses_data) == 1
    assert addresses_data[0]["id"] == address_id

    # 3. PUT /address/{address_id}
    update_payload = {**address_payload, "full_name": "Jane Smith"}
    update_resp = client.put(f"/address/{address_id}", json=update_payload, headers=headers)
    assert update_resp.status_code == 200, update_resp.text
    update_data = update_resp.json()
    assert update_data["message"] == "Address updated"
    assert update_data["address"]["full_name"] == "Jane Smith"

    # 4. DELETE /address/{address_id}
    delete_resp = client.delete(f"/address/{address_id}", headers=headers)
    assert delete_resp.status_code == 200, delete_resp.text
    delete_data = delete_resp.json()
    assert delete_data["message"] == "Address deleted"
