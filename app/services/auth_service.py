import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.refresh_token import RefreshToken
from app.models.user import User


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register(self, email: str, username: str, password: str, **kwargs) -> User:
        existing = await self.session.execute(
            select(User).where((User.email == email) | (User.username == username))
        )
        if existing.scalar_one_or_none():
            raise ConflictError("Email or username already registered")

        user = User(
            email=email,
            username=username,
            hashed_password=hash_password(password),
            first_name=kwargs.get("first_name"),
            last_name=kwargs.get("last_name"),
            is_active=True,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def authenticate(self, email: str, password: str) -> User:
        result = await self.session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid credentials")
        if not user.is_active:
            raise UnauthorizedError("Account is inactive")
        user.last_login = datetime.now(timezone.utc)
        return user

    async def create_tokens(self, user: User) -> tuple[str, str]:
        access = create_access_token(user.id)
        refresh_raw = secrets.token_urlsafe(32)
        refresh_hash = hashlib.sha256(refresh_raw.encode()).hexdigest()
        expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        token = RefreshToken(user_id=user.id, token_hash=refresh_hash, expires_at=expires)
        self.session.add(token)
        await self.session.flush()
        return access, refresh_raw

    async def refresh_access_token(self, refresh_token: str) -> tuple[str, str]:
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash, RefreshToken.revoked.is_(False))
        )
        stored = result.scalar_one_or_none()
        if not stored or stored.expires_at < datetime.now(timezone.utc):
            raise UnauthorizedError("Invalid or expired refresh token")

        stored.revoked = True
        user_result = await self.session.execute(select(User).where(User.id == stored.user_id))
        user = user_result.scalar_one()
        return await self.create_tokens(user)

    async def revoke_refresh_token(self, refresh_token: str) -> None:
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        result = await self.session.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        stored = result.scalar_one_or_none()
        if stored:
            stored.revoked = True

    async def get_or_create_google_user(self, google_sub: str, email: str, name: str | None = None) -> User:
        result = await self.session.execute(select(User).where(User.google_sub == google_sub))
        user = result.scalar_one_or_none()
        if user:
            return user

        result = await self.session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            user.google_sub = google_sub
            return user

        username = email.split("@")[0]
        user = User(email=email, username=username, google_sub=google_sub, is_active=True)
        if name:
            parts = name.split(" ", 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else None
        self.session.add(user)
        await self.session.flush()
        return user
