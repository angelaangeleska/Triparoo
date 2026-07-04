from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.trip_request import TripRequest
from app.repositories.base import GenericRepository


class TripRequestRepository(GenericRepository[TripRequest]):
    model = TripRequest

    async def list_for_user(self, user_id: int) -> list[TripRequest]:
        result = await self.session.execute(
            select(TripRequest)
            .where(TripRequest.user_id == user_id)
            .options(selectinload(TripRequest.members), selectinload(TripRequest.recommendations))
            .order_by(TripRequest.created_at.desc())
        )
        return list(result.scalars().unique().all())

    async def get_for_user(self, user_id: int, trip_request_id: int) -> TripRequest | None:
        result = await self.session.execute(
            select(TripRequest)
            .where(TripRequest.id == trip_request_id, TripRequest.user_id == user_id)
            .options(selectinload(TripRequest.members), selectinload(TripRequest.recommendations))
        )
        return result.scalar_one_or_none()
