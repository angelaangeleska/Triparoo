from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import decode_token
from app.db.session import get_async_session
from app.integrations.accommodations.mock_accommodation import MockAccommodationProvider
from app.integrations.flights.factory import get_flight_provider
from app.models.user import User
from app.recommendation.mock_llm import MockLLMProvider

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_db(session: Annotated[AsyncSession, Depends(get_async_session)]) -> AsyncSession:
    return session


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_id = int(payload["sub"])
    except (ValueError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


async def get_optional_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    if not token:
        return None
    try:
        return await get_current_user(token, session)
    except HTTPException:
        return None


def get_flight_provider_dep(session: AsyncSession = Depends(get_db)):
    return get_flight_provider(session)


def get_accommodation_provider(session: AsyncSession = Depends(get_db)) -> MockAccommodationProvider:
    return MockAccommodationProvider(session)


def get_recommendation_provider() -> MockLLMProvider:
    return MockLLMProvider()


def handle_app_exception(exc: AppException) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)
