from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import base64

import os

# configure an in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# import application components
from app.database.connection import Base
from app.main import app
from app.auth import deps as auth_deps


# create tables in test database
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[auth_deps.get_db] = override_get_db

client = TestClient(app)


def basic_header(email: str, password: str) -> dict:
    token = base64.b64encode(f"{email}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def test_register_and_basic_login_and_me():
    # Register a normal user
    payload = {"name": "Alice", "email": "alice@example.com", "password": "secretpass", "role": "resident"}
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["email"] == "alice@example.com"

    # Login returns no token for normal user
    r = client.post("/auth/login", data={"username": "alice@example.com", "password": "secretpass"})
    assert r.status_code == 200
    assert r.json().get("detail") == "Login successful"

    # Access protected endpoint with Basic auth
    r = client.get("/auth/me", headers=basic_header("alice@example.com", "secretpass"))
    assert r.status_code == 200
    me = r.json()
    assert me["email"] == "alice@example.com"
    assert me["role"] == "resident"


def test_admin_invite_flow():
    # Create admin user directly in DB
    from app.auth import hash as hash_utils
    from app.models.user import User

    db = TestingSessionLocal()
    hashed = hash_utils.hash_password("adminpass")
    admin_user = User(name="Admin", email="admin@example.com", password_hash=hashed, role="admin")
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    db.close()

    # Admin login -> should return token
    r = client.post("/auth/login", data={"username": "admin@example.com", "password": "adminpass"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    token = body["access_token"]

    # Create invite (admin-only)
    r = client.post("/auth/invite", json={"email": "newadmin@example.com", "role": "admin"}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    invite_token = r.json()["token"]

    # Accept invite
    payload = {"token": invite_token, "name": "New Admin", "email": "newadmin@example.com", "password": "newadminpass"}
    r = client.post("/auth/invite/accept", json=payload)
    assert r.status_code == 200, r.text

    # New admin can login and receive token
    r = client.post("/auth/login", data={"username": "newadmin@example.com", "password": "newadminpass"})
    assert r.status_code == 200
    assert "access_token" in r.json()

    # Reusing invite should fail
    r = client.post("/auth/invite/accept", json=payload)
    assert r.status_code == 400
