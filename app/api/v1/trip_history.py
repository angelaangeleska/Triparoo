from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_db, handle_app_exception
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.trip_history import TripHistoryRead
from app.services.trip_history_service import TripHistoryService

router = APIRouter(prefix="/trip-history", tags=["Trip History"])


@router.get("", response_model=list[TripHistoryRead])
async def list_trip_history(
    session=Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = TripHistoryService(session)
    return await service.list_for_user(user.id)


@router.get("/{trip_request_id}", response_model=TripHistoryRead)
async def get_trip_history(
    trip_request_id: int,
    session=Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        service = TripHistoryService(session)
        return await service.get_for_user(user.id, trip_request_id)
    except AppException as exc:
        raise handle_app_exception(exc)
