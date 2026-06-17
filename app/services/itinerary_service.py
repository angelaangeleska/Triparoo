from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.catalog import DestinationRepository
from app.schemas.trip_planner import (
    ChildActivitiesRequest,
    ChildActivitiesResponse,
    ChildActivityResult,
    ItineraryDayItem,
    ItineraryDayRead,
    ItineraryRequest,
    ItineraryResponse,
)
from app.services.cost_estimator import CostEstimatorService


class ChildActivityService:
    def __init__(self, session: AsyncSession):
        self.dest_repo = DestinationRepository(session)

    async def recommend(self, request: ChildActivitiesRequest) -> ChildActivitiesResponse:
        dest = await self.dest_repo.get_with_relations(request.destination_id)
        if not dest:
            raise NotFoundError("Destination not found")

        results = []
        for att in dest.attractions or []:
            if not att.family_friendly:
                continue
            if not (att.min_age <= request.age <= att.max_age):
                continue

            score = 60.0
            reasons = []
            if att.min_age <= request.age <= att.max_age:
                score += 20
                reasons.append("Age-appropriate")
            if request.age >= 6 and ("theme_park" in att.tags or "disney" in att.name.lower()):
                score += 15
                reasons.append("Great for school-age children")
            if request.age >= 8 and "museum" in att.category.lower():
                score += 10
                reasons.append("Educational and interactive")
            interest_set = {i.lower() for i in request.interests}
            if any(t in interest_set for t in (att.tags or [])):
                score += 15
                reasons.append("Matches stated interests")

            results.append(
                ChildActivityResult(
                    id=att.id,
                    name=att.name,
                    category=att.category,
                    description=att.description,
                    price=att.price,
                    match_score=min(score, 100.0),
                    reason="; ".join(reasons) or "Family-friendly attraction",
                )
            )
        results.sort(key=lambda r: r.match_score, reverse=True)
        return ChildActivitiesResponse(activities=results)


class ItineraryService:
    def __init__(self, session: AsyncSession):
        self.dest_repo = DestinationRepository(session)
        self.cost_estimator = CostEstimatorService(session)

    async def generate(self, request: ItineraryRequest) -> ItineraryResponse:
        dest = await self.dest_repo.get_with_relations(request.destination_id)
        if not dest:
            raise NotFoundError("Destination not found")

        attractions = sorted(
            [a for a in (dest.attractions or []) if a.family_friendly],
            key=lambda a: a.price,
        )
        days = []
        total_cost = 0.0

        for day_num in range(1, request.duration_days + 1):
            items = []
            if day_num == 1:
                items.append(ItineraryDayItem(time="Morning", activity="Arrival & hotel check-in", estimated_cost=0))
                if attractions:
                    att = attractions[0]
                    items.append(
                        ItineraryDayItem(
                            time="Afternoon",
                            activity=att.name,
                            description=att.description,
                            estimated_cost=att.price * len(request.members),
                        )
                    )
                    total_cost += att.price * len(request.members)
                title = f"Day {day_num}: Arrival in {dest.city.name if dest.city else 'destination'}"
            elif day_num == request.duration_days:
                items.append(ItineraryDayItem(time="Morning", activity="Souvenir shopping & leisure", estimated_cost=0))
                items.append(ItineraryDayItem(time="Afternoon", activity="Departure", estimated_cost=0))
                title = f"Day {day_num}: Departure"
            else:
                att_idx = (day_num - 2) % max(len(attractions), 1)
                if attractions:
                    att = attractions[att_idx]
                    items.append(
                        ItineraryDayItem(
                            time="Full day",
                            activity=att.name,
                            description=att.description,
                            estimated_cost=att.price * len(request.members),
                        )
                    )
                    total_cost += att.price * len(request.members)
                    title = f"Day {day_num}: {att.name}"
                else:
                    items.append(ItineraryDayItem(time="Full day", activity="City exploration", estimated_cost=0))
                    title = f"Day {day_num}: Explore the city"

            days.append(ItineraryDayRead(day_number=day_num, title=title, items=items))

        end_date = request.start_date + timedelta(days=request.duration_days) if request.start_date else None
        estimate = await self.cost_estimator.estimate_trip(
            dest,
            len(request.members),
            request.start_date,
            end_date,
        )
        total_cost += estimate["flight"] + estimate["accommodation"]

        return ItineraryResponse(
            destination_id=dest.id,
            city=dest.city.name if dest.city else "",
            country=dest.city.country.name if dest.city and dest.city.country else "",
            total_estimated_cost=round(total_cost, 2),
            days=days,
        )
