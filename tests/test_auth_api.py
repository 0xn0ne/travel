"""End-to-end auth backend tests: register, login, /me, profile update."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.api.dependencies import get_db
from backend.main import app
from backend.models.database import Base

# In-memory test database
TEST_DB_URL = "sqlite+aiosqlite://"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionFactory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables for each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    """Test client with DB session override."""

    async def override_get_db():
        async with TestSessionFactory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------- Test 1: Register creates user and returns JWT ----------
async def test_register_creates_user_and_returns_jwt(client: AsyncClient):
    resp = await client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "secret123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test@example.com"
    assert "id" in data["user"]


# ---------- Test 2: Register with duplicate email returns 400 ----------
async def test_register_duplicate_email_returns_400(client: AsyncClient):
    await client.post("/api/auth/register", json={"email": "dup@example.com", "password": "secret123"})
    resp = await client.post("/api/auth/register", json={"email": "dup@example.com", "password": "other456"})
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


# ---------- Test 3: Login with correct credentials returns JWT ----------
async def test_login_correct_credentials(client: AsyncClient):
    await client.post("/api/auth/register", json={"email": "login@example.com", "password": "secret123"})
    resp = await client.post("/api/auth/login", json={"email": "login@example.com", "password": "secret123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login@example.com"


# ---------- Test 4: Login with wrong password returns 401 ----------
async def test_login_wrong_password_returns_401(client: AsyncClient):
    await client.post("/api/auth/register", json={"email": "wrong@example.com", "password": "secret123"})
    resp = await client.post("/api/auth/login", json={"email": "wrong@example.com", "password": "badpass"})
    assert resp.status_code == 401


# ---------- Test 5: GET /me with valid JWT returns user profile ----------
async def test_get_me_valid_jwt(client: AsyncClient):
    reg = await client.post("/api/auth/register", json={"email": "me@example.com", "password": "secret123"})
    token = reg.json()["access_token"]
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "me@example.com"
    assert "taste_tags_default" in data
    assert "budget_default" in data


# ---------- Test 6: GET /me without JWT returns 422 ----------
async def test_get_me_no_jwt_returns_422(client: AsyncClient):
    """Missing authorization header → FastAPI validation error (422)."""
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 422


# ---------- Test 7: GET /me with invalid JWT returns 401 ----------
async def test_get_me_invalid_jwt_returns_401(client: AsyncClient):
    resp = await client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401


# ---------- Test 8: PUT /auth/profile updates taste and budget ----------
async def test_update_profile(client: AsyncClient):
    reg = await client.post("/api/auth/register", json={"email": "profile@example.com", "password": "secret123"})
    token = reg.json()["access_token"]
    resp = await client.put(
        "/api/auth/profile",
        json={"taste_tags_default": '["咖啡","甜品"]', "budget_default": "经济"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["taste_tags_default"] == '["咖啡","甜品"]'
    assert data["budget_default"] == "经济"


# ---------- Test 9: PUT /auth/profile rejects invalid budget ----------
async def test_update_profile_invalid_budget(client: AsyncClient):
    reg = await client.post("/api/auth/register", json={"email": "budget@example.com", "password": "secret123"})
    token = reg.json()["access_token"]
    resp = await client.put(
        "/api/auth/profile",
        json={"taste_tags_default": "[]", "budget_default": "INVALID"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


# ---------- Test 10: PUT /auth/profile rejects invalid JSON tags ----------
async def test_update_profile_invalid_tags(client: AsyncClient):
    reg = await client.post("/api/auth/register", json={"email": "tags@example.com", "password": "secret123"})
    token = reg.json()["access_token"]
    resp = await client.put(
        "/api/auth/profile",
        json={"taste_tags_default": "not-json", "budget_default": "适中"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


# ---------- Test 11: GET /itineraries returns user's itineraries ----------
async def test_list_itineraries_empty(client: AsyncClient):
    reg = await client.post("/api/auth/register", json={"email": "it@example.com", "password": "secret123"})
    token = reg.json()["access_token"]
    resp = await client.get("/api/itineraries", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == []
