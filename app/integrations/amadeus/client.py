"""Shared Amadeus Self-Service API client (test or production)."""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: "AmadeusClient | None" = None


class AmadeusClient:
    """OAuth2 client for Amadeus REST APIs."""

    def __init__(self) -> None:
        self._token: str | None = None

    @property
    def enabled(self) -> bool:
        return bool(settings.AMADEUS_CLIENT_ID and settings.AMADEUS_CLIENT_SECRET)

    async def _ensure_token(self, client: httpx.AsyncClient) -> str:
        if self._token:
            return self._token
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
        self._token = resp.json()["access_token"]
        return self._token

    async def get(
        self,
        path: str,
        *,
        params: dict | None = None,
        timeout: float = 25.0,
    ) -> httpx.Response:
        if not self.enabled:
            raise RuntimeError("Amadeus credentials are not configured")

        url = path if path.startswith("http") else f"{settings.AMADEUS_BASE_URL}{path}"
        async with httpx.AsyncClient(timeout=timeout) as client:
            token = await self._ensure_token(client)
            resp = await client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 401:
                self._token = None
                token = await self._ensure_token(client)
                resp = await client.get(
                    url,
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
            return resp

    async def get_json(self, path: str, *, params: dict | None = None, timeout: float = 25.0) -> dict:
        resp = await self.get(path, params=params, timeout=timeout)
        if resp.status_code != 200:
            logger.warning("Amadeus %s returned %s: %s", path, resp.status_code, resp.text[:300])
            return {}
        return resp.json()


def get_amadeus_client() -> AmadeusClient:
    global _client
    if _client is None:
        _client = AmadeusClient()
    return _client
