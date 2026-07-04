"""Persists trip-planner searches so users can revisit past recommendations.

TripRequest/TripMember/Recommendation had full tables and migrations from the
original scaffold but nothing ever wrote to them — every recommend() call
computed everything in memory and discarded it on response. This wires that
up: each search is recorded as a TripRequest with its TripMember snapshot and
one Recommendation row per ranked destination.
"""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.recommendation import Recommendation
from app.models.trip_member import TripMember
from app.models.trip_request import TripRequest
from app.repositories.trip_request import TripRequestRepository
from app.schemas.family import TripMemberInput


class TripHistoryService:
    def __init__(self, session: AsyncSession):
        self.repo = TripRequestRepository(session)

    async def record_search(
        self,
        user_id: int,
        members: list[TripMemberInput],
        budget: float,
        start_date: date | None,
        end_date: date | None,
        origin_airport_id: int | None,
        recommendations: list[dict],
    ) -> TripRequest:
        trip_request = TripRequest(
            user_id=user_id,
            origin_airport_id=origin_airport_id,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            status="searched",
        )
        trip_request.members = [
            TripMember(age=m.age, gender=m.gender, interests=m.interests) for m in members
        ]
        trip_request.recommendations = [
            Recommendation(
                user_id=user_id,
                type="destination",
                entity_id=r["destination_id"],
                rule_score=r["rule_score"],
                llm_score=r["llm_score"],
                final_score=r["final_score"],
                explanation={
                    "city": r["city"],
                    "country": r["country"],
                    "text": r["explanation"],
                    "highlights": r.get("highlights", []),
                    "estimated_total_cost": r["estimated_total_cost"],
                },
            )
            for r in recommendations
        ]
        return await self.repo.create(trip_request)

    async def list_for_user(self, user_id: int) -> list[TripRequest]:
        return await self.repo.list_for_user(user_id)

    async def get_for_user(self, user_id: int, trip_request_id: int) -> TripRequest:
        trip_request = await self.repo.get_for_user(user_id, trip_request_id)
        if not trip_request:
            raise NotFoundError("Trip not found")
        return trip_request
