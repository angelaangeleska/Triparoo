"""Shared Amadeus OAuth2 client-credentials token cache.

Both the flight and hotel providers authenticate against the same Amadeus
account, so the access token is fetched once per process and reused until it
is close to expiry instead of being re-requested on every search call.
"""

from __future__ import annotations

import time

import httpx

from app.core.config import settings

_token: str | None = None
_expires_at: float = 0.0


async def get_amadeus_access_token(client: httpx.AsyncClient) -> str:
    global _token, _expires_at

    if _token and time.monotonic() < _expires_at:
        return _token

    resp = await client.post(
        f"{settings.AMADEUS_BASE_URL}/v1/security/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": settings.AMADEUS_CLIENT_ID,
            "client_secret": settings.AMADEUS_CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp.raise_for_status()
    data = resp.json()
    _token = data["access_token"]
    # Refresh a minute early to avoid racing the real expiry.
    _expires_at = time.monotonic() + max(int(data.get("expires_in", 1799)) - 60, 60)
    return _token


def invalidate_amadeus_token() -> None:
    global _token, _expires_at
    _token = None
    _expires_at = 0.0
