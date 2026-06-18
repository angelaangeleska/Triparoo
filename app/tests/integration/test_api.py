import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_and_login(client):
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!",
        },
    )
    assert register.status_code == 201
    assert register.json()["email"] == "test@example.com"

    login = await client.post(
        "/api/v1/auth/login/json",
        json={"email": "test@example.com", "password": "SecurePass123!"},
    )
    assert login.status_code == 200
    data = login.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_destinations_empty(client):
    response = await client.get("/api/v1/destinations")
    assert response.status_code == 200
    assert response.json() == []
