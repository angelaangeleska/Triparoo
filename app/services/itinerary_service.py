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
from app.services.activity_matching import attraction_matches_interest, attraction_matches_interests
from app.services.cost_estimator import CostEstimatorService
from app.services.groq_service import generate_itinerary_with_ai


class ChildActivityService:
    def __init__(self, session: AsyncSession):
        self.dest_repo = DestinationRepository(session)

    async def recommend(self, request: ChildActivitiesRequest) -> ChildActivitiesResponse:
        dest = await self.dest_repo.get_with_relations(request.destination_id)
        if not dest:
            raise NotFoundError("Destination not found")

        results = []
        interest_set = {i.lower().strip() for i in request.interests if i and i.strip()}
        for att in dest.attractions or []:
            if not att.family_friendly:
                continue
            if not (att.min_age <= request.age <= att.max_age):
                continue
            if interest_set and not attraction_matches_interests(att, request.interests):
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
            if interest_set:
                matched = [i for i in request.interests if attraction_matches_interest(att, i)]
                if matched:
                    score += 15 + min(len(matched) * 5, 15)
                    labels = ", ".join(m.replace("_", " ") for m in matched)
                    reasons.append(f"Matches: {labels}")

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
        attraction_names = [a.name for a in attractions]

        members_list = [
            {"age": m.age, "interests": m.interests if hasattr(m, "interests") else []}
            for m in request.members
        ]

        city = dest.city.name if dest.city else "destination"
        country = dest.city.country.name if dest.city and dest.city.country else ""

        # AI генерирање на итинерар
        ai_text = await generate_itinerary_with_ai(
            city=city,
            country=country,
            duration_days=request.duration_days,
            members=members_list,
            budget=request.budget if hasattr(request, "budget") else 1000,
            attractions=attraction_names,
        )

        # Парсирај го AI текстот во денови
        days = []
        lines = ai_text.strip().split("\n")
        current_day_num = 0
        current_items = []
        current_title = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith("day ") and ":" in line:
                if current_day_num > 0:
                    days.append(ItineraryDayRead(
                        day_number=current_day_num,
                        title=current_title,
                        items=current_items,
                    ))
                current_day_num += 1
                current_title = line
                current_items = []
            elif current_day_num > 0 and line.startswith("-"):
                current_items.append(ItineraryDayItem(
                    time="",
                    activity=line[1:].strip(),
                    estimated_cost=0,
                ))

        if current_day_num > 0:
            days.append(ItineraryDayRead(
                day_number=current_day_num,
                title=current_title,
                items=current_items,
            ))

        # Ако парсирањето не успеало, стави го AI текстот во еден ден
        if not days:
            days.append(ItineraryDayRead(
                day_number=1,
                title="Your AI-Generated Itinerary",
                items=[ItineraryDayItem(time="", activity=ai_text, estimated_cost=0)],
            ))

        end_date = request.start_date + timedelta(days=request.duration_days) if request.start_date else None
        estimate = await self.cost_estimator.estimate_trip(
            dest,
            len(request.members),
            request.start_date,
            end_date,
        )

        return ItineraryResponse(
            destination_id=dest.id,
            city=city,
            country=country,
            total_estimated_cost=round(estimate["flight"] + estimate["accommodation"], 2),
            days=days,
        )