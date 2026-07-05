from datetime import timedelta
import random
import re

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
from app.services.tour_service import fetch_family_attractions

_CATEGORY_DEFAULT_PRICE: dict[str, float] = {
    "museum": 15.0,
    "gallery": 12.0,
    "zoo": 22.0,
    "aquarium": 20.0,
    "theme park": 45.0,
    "attraction": 12.0,
    "viewpoint": 0.0,
    "artwork": 0.0,
    "park": 0.0,
    "playground": 0.0,
    "nature reserve": 5.0,
    "water park": 35.0,
}
_MEAL_KEYWORDS = ("dinner", "lunch", "breakfast", "meal", "restaurant", "café", "cafe")
_FREE_KEYWORDS = ("walk", "stroll", "free", "viewpoint", "relax")


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

    @staticmethod
    def _build_fallback_itinerary(
        city: str,
        country: str,
        duration_days: int,
        budget: float,
        attractions: list,
    ) -> str:
        daily_budget = max(budget / duration_days, 50.0)
        names = [a.name for a in attractions] if attractions else [f"local sights in {city}"]
        lines: list[str] = []

        for day in range(1, duration_days + 1):
            lines.append(f"Day {day}: Family day in {city}")
            morning = names[(day - 1) % len(names)]
            afternoon = names[(day) % len(names)]
            evening = names[(day + 1) % len(names)]
            lines.append(f"- Morning: Explore {morning}")
            lines.append(f"- Afternoon: Visit {afternoon}")
            lines.append(
                f"- Evening: Relax and dinner (~€{daily_budget * 0.35:.0f} estimated for the family)"
            )

        return "\n".join(lines)

    @staticmethod
    def _category_default_price(category: str) -> float:
        return _CATEGORY_DEFAULT_PRICE.get(category.lower(), 10.0)

    @classmethod
    def _estimate_item_cost(
        cls,
        activity_text: str,
        db_attractions: list,
        real_attractions: list[dict],
        party_size: int,
    ) -> float:
        text_lower = activity_text.lower()
        for att in db_attractions:
            if att.name.lower() in text_lower:
                return round(att.price * party_size, 2)
        for att in real_attractions:
            name = att.get("name", "")
            if name and name.lower() in text_lower:
                unit = cls._category_default_price(att.get("category", "attraction"))
                return round(unit * party_size, 2)
        if any(word in text_lower for word in _MEAL_KEYWORDS):
            return round(18.0 * party_size, 2)
        if any(word in text_lower for word in _FREE_KEYWORDS):
            return 0.0
        return round(10.0 * party_size, 2)

    @staticmethod
    def _parse_inline_cost(text: str) -> float | None:
        match = re.search(r"€\s*(\d+(?:\.\d+)?)|\$\s*(\d+(?:\.\d+)?)", text)
        if not match:
            return None
        value = match.group(1) or match.group(2)
        return float(value)

    @classmethod
    def _apply_itinerary_costs(
        cls,
        days: list[ItineraryDayRead],
        db_attractions: list,
        real_attractions: list[dict],
        party_size: int,
    ) -> float:
        total = 0.0
        enriched_days: list[ItineraryDayRead] = []
        for day in days:
            enriched_items: list[ItineraryDayItem] = []
            for item in day.items:
                inline = cls._parse_inline_cost(item.activity)
                cost = inline if inline is not None else cls._estimate_item_cost(
                    item.activity, db_attractions, real_attractions, party_size
                )
                enriched_items.append(
                    ItineraryDayItem(
                        time=item.time,
                        activity=item.activity,
                        description=item.description,
                        estimated_cost=round(cost, 2),
                    )
                )
                total += cost
            enriched_days.append(
                ItineraryDayRead(
                    day_number=day.day_number,
                    title=day.title,
                    items=enriched_items,
                )
            )
        days.clear()
        days.extend(enriched_days)
        return round(total, 2)

    @staticmethod
    def _rotate_attractions(items: list, regenerate_count: int, seed: int) -> list:
        if not items or regenerate_count <= 0:
            return items
        rotated = items.copy()
        rng = random.Random(seed + regenerate_count * 7919)
        rng.shuffle(rotated)
        offset = regenerate_count % len(rotated)
        return rotated[offset:] + rotated[:offset]

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

        latitude = dest.latitude
        longitude = dest.longitude
        if dest.city:
            latitude = latitude if latitude is not None else dest.city.latitude
            longitude = longitude if longitude is not None else dest.city.longitude

        real_attractions = await fetch_family_attractions(city, latitude, longitude)
        if request.regenerate_count > 0:
            real_attractions = self._rotate_attractions(
                real_attractions, request.regenerate_count, dest.id
            )
            attractions = self._rotate_attractions(
                attractions, request.regenerate_count, dest.id + 1
            )

        # AI генерирање на итинерар (fallback to template when Groq is unavailable)
        ai_text = None
        try:
            ai_text = await generate_itinerary_with_ai(
                city=city,
                country=country,
                duration_days=request.duration_days,
                members=members_list,
                budget=request.budget if hasattr(request, "budget") else 1000,
                attractions=attraction_names,
                real_attractions=real_attractions or None,
                regenerate_count=request.regenerate_count,
            )
        except Exception:
            ai_text = None
        if not ai_text:
            ai_text = self._build_fallback_itinerary(
                city, country, request.duration_days, request.budget, attractions
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
                activity = line[1:].strip()
                if "estimated daily cost" in activity.lower():
                    continue
                time_match = re.search(r"\((\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)\)", activity)
                time_str = time_match.group(1) if time_match else ""
                current_items.append(ItineraryDayItem(
                    time=time_str,
                    activity=activity,
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

        party_size = len(request.members)
        activity_cost = self._apply_itinerary_costs(
            days, attractions, real_attractions, party_size
        )

        if activity_cost == 0 and attractions:
            top = attractions[:3]
            activity_cost = round(
                min(sum(a.price * party_size for a in top), 300.0 * party_size),
                2,
            )

        return ItineraryResponse(
            destination_id=dest.id,
            city=city,
            country=country,
            total_estimated_cost=activity_cost,
            days=days,
        )