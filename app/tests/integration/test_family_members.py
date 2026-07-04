import pytest


async def _register_and_login(client, email="family@example.com"):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": email.split("@")[0], "password": "SecurePass123!"},
    )
    login = await client.post("/api/v1/auth/login/json", json={"email": email, "password": "SecurePass123!"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_family_members_require_auth(client):
    response = await client.get("/api/v1/family-members")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_and_list_family_members(client):
    headers = await _register_and_login(client)

    create = await client.post(
        "/api/v1/family-members",
        json={"age": 9, "gender": "female", "interests": ["disney", "science"], "name": "Mia"},
        headers=headers,
    )
    assert create.status_code == 201
    body = create.json()
    assert body["age"] == 9
    assert body["name"] == "Mia"

    listing = await client.get("/api/v1/family-members", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


@pytest.mark.asyncio
async def test_update_family_member(client):
    headers = await _register_and_login(client, email="update@example.com")
    create = await client.post(
        "/api/v1/family-members",
        json={"age": 8, "interests": ["museum"]},
        headers=headers,
    )
    member_id = create.json()["id"]

    update = await client.put(
        f"/api/v1/family-members/{member_id}",
        json={"age": 9, "interests": ["museum", "art"]},
        headers=headers,
    )
    assert update.status_code == 200
    assert update.json()["age"] == 9
    assert update.json()["interests"] == ["museum", "art"]


@pytest.mark.asyncio
async def test_delete_family_member(client):
    headers = await _register_and_login(client, email="delete@example.com")
    create = await client.post("/api/v1/family-members", json={"age": 5, "interests": []}, headers=headers)
    member_id = create.json()["id"]

    delete = await client.delete(f"/api/v1/family-members/{member_id}", headers=headers)
    assert delete.status_code == 204

    listing = await client.get("/api/v1/family-members", headers=headers)
    assert listing.json() == []


@pytest.mark.asyncio
async def test_cannot_access_other_users_family_member(client):
    headers_a = await _register_and_login(client, email="userA@example.com")
    headers_b = await _register_and_login(client, email="userB@example.com")

    create = await client.post("/api/v1/family-members", json={"age": 12, "interests": []}, headers=headers_a)
    member_id = create.json()["id"]

    update = await client.put(
        f"/api/v1/family-members/{member_id}", json={"age": 13, "interests": []}, headers=headers_b
    )
    assert update.status_code == 404

    delete = await client.delete(f"/api/v1/family-members/{member_id}", headers=headers_b)
    assert delete.status_code == 404
