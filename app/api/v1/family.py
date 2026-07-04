from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_db, handle_app_exception
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.family import FamilyMemberCreate, FamilyMemberRead
from app.services.family_service import FamilyMemberService

router = APIRouter(prefix="/family-members", tags=["Family"])


@router.get("", response_model=list[FamilyMemberRead])
async def list_family_members(
    session=Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = FamilyMemberService(session)
    return await service.list_for_user(user.id)


@router.post("", response_model=FamilyMemberRead, status_code=201)
async def create_family_member(
    payload: FamilyMemberCreate,
    session=Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = FamilyMemberService(session)
    return await service.create(user.id, payload)


@router.put("/{member_id}", response_model=FamilyMemberRead)
async def update_family_member(
    member_id: int,
    payload: FamilyMemberCreate,
    session=Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        service = FamilyMemberService(session)
        return await service.update(user.id, member_id, payload)
    except AppException as exc:
        raise handle_app_exception(exc)


@router.delete("/{member_id}", status_code=204)
async def delete_family_member(
    member_id: int,
    session=Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        service = FamilyMemberService(session)
        await service.delete(user.id, member_id)
    except AppException as exc:
        raise handle_app_exception(exc)
