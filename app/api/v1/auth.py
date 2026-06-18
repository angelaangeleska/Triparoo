from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_current_user, get_db, handle_app_exception
from app.auth.oauth.google import GoogleOAuthService
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.auth import TokenRefreshRequest, TokenResponse, UserLogin, UserRead, UserRegister
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead, status_code=201)
async def register(payload: UserRegister, session=Depends(get_db)):
    try:
        service = AuthService(session)
        user = await service.register(
            email=payload.email,
            username=payload.username,
            password=payload.password,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
        return user
    except AppException as exc:
        raise handle_app_exception(exc)


@router.post("/login", response_model=TokenResponse)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session=Depends(get_db)):
    try:
        service = AuthService(session)
        user = await service.authenticate(form_data.username, form_data.password)
        access, refresh = await service.create_tokens(user)
        return TokenResponse(access_token=access, refresh_token=refresh)
    except AppException as exc:
        raise handle_app_exception(exc)


@router.post("/login/json", response_model=TokenResponse)
async def login_json(payload: UserLogin, session=Depends(get_db)):
    try:
        service = AuthService(session)
        user = await service.authenticate(payload.email, payload.password)
        access, refresh = await service.create_tokens(user)
        return TokenResponse(access_token=access, refresh_token=refresh)
    except AppException as exc:
        raise handle_app_exception(exc)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: TokenRefreshRequest, session=Depends(get_db)):
    try:
        service = AuthService(session)
        access, refresh = await service.refresh_access_token(payload.refresh_token)
        return TokenResponse(access_token=access, refresh_token=refresh)
    except AppException as exc:
        raise handle_app_exception(exc)


@router.post("/logout", status_code=204)
async def logout(payload: TokenRefreshRequest, session=Depends(get_db)):
    service = AuthService(session)
    await service.revoke_refresh_token(payload.refresh_token)


@router.get("/me", response_model=UserRead)
async def me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.get("/google/login")
async def google_login():
    oauth = GoogleOAuthService()
    try:
        url, state = oauth.get_authorization_url()
        return {"authorization_url": url, "state": state}
    except AppException as exc:
        raise handle_app_exception(exc)


@router.get("/google/callback", response_model=TokenResponse)
async def google_callback(code: str, session=Depends(get_db)):
    oauth = GoogleOAuthService()
    try:
        userinfo = await oauth.exchange_code(code)
        service = AuthService(session)
        user = await service.get_or_create_google_user(
            google_sub=userinfo["sub"],
            email=userinfo["email"],
            name=userinfo.get("name"),
        )
        access, refresh = await service.create_tokens(user)
        return TokenResponse(access_token=access, refresh_token=refresh)
    except AppException as exc:
        raise handle_app_exception(exc)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
