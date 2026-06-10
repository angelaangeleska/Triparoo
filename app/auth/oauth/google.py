import secrets

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client

from app.core.config import settings
from app.core.exceptions import AppException


class GoogleOAuthService:
    AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
    SCOPES = ["openid", "email", "profile"]

    def is_configured(self) -> bool:
        return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)

    def get_authorization_url(self) -> tuple[str, str]:
        if not self.is_configured():
            raise AppException("Google OAuth is not configured", status_code=503)

        state = secrets.token_urlsafe(16)
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        query = "&".join(f"{k}={httpx.QueryParams({k: v})[k]}" for k, v in params.items())
        return f"{self.AUTHORIZE_URL}?{query}", state

    async def exchange_code(self, code: str) -> dict:
        if not self.is_configured():
            raise AppException("Google OAuth is not configured", status_code=503)

        client = AsyncOAuth2Client(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )
        token = await client.fetch_token(
            self.TOKEN_URL,
            code=code,
            grant_type="authorization_code",
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
        )
        async with httpx.AsyncClient() as http:
            resp = await http.get(self.USERINFO_URL, headers={"Authorization": f"Bearer {token['access_token']}"})
            resp.raise_for_status()
            return resp.json()
