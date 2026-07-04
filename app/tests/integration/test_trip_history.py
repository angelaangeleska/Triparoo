import pytest


async def _register_and_login(client, email="history@example.com"):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": email.split("@")[0], "password": "SecurePass123!"},
    )
    login = await client.post("/api/v1/auth/login/json", json={"email": email, "password": "SecurePass123!"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_trip_history_requires_auth(client):
    response = await client.get("/api/v1/trip-history")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_recommend_records_trip_history(client):
    headers = await _register_and_login(client)

    recommend = await client.post(
        "/api/v1/trip-planner/recommend",
        json={
            "members": [{"age": 35, "interests": []}, {"age": 9, "interests": ["science"]}],
            "budget": 1500,
            "preferred_month": 8,
        },
        headers=headers,
    )
    assert recommend.status_code == 200

    history = await client.get("/api/v1/trip-history", headers=headers)
    assert history.status_code == 200
    body = history.json()
    assert len(body) == 1
    trip = body[0]
    assert trip["status"] == "searched"
    assert trip["budget"] == 1500
    assert len(trip["members"]) == 2
    assert {m["age"] for m in trip["members"]} == {35, 9}

    detail = await client.get(f"/api/v1/trip-history/{trip['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == trip["id"]


@pytest.mark.asyncio
async def test_cannot_view_other_users_trip_history(client):
    headers_a = await _register_and_login(client, email="historyA@example.com")
    headers_b = await _register_and_login(client, email="historyB@example.com")

    await client.post(
        "/api/v1/trip-planner/recommend",
        json={"members": [{"age": 30, "interests": []}], "budget": 1000, "preferred_month": 6},
        headers=headers_a,
    )
    history_a = await client.get("/api/v1/trip-history", headers=headers_a)
    trip_id = history_a.json()[0]["id"]

    forbidden = await client.get(f"/api/v1/trip-history/{trip_id}", headers=headers_b)
    assert forbidden.status_code == 404

    empty = await client.get("/api/v1/trip-history", headers=headers_b)
    assert empty.json() == []
