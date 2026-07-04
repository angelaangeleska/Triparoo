"""AI-generated trip guide: restaurants, hidden gems, local tips, transportation.

Complements the structured recommend/itinerary flow with free-form,
personalized suggestions that don't fit a rigid schema. Grounded with the
destination's known attractions (and Google Places results, once
GOOGLE_PLACES_API_KEY is configured — see app/integrations/places) so the
model has real local context instead of inventing places from nothing.
"""

from __future__ import annotations

import json
import logging

from groq import AsyncGroq
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.integrations.places.base import PlaceSearchCriteria
from app.integrations.places.factory import get_places_provider
from app.repositories.catalog import DestinationRepository
from app.schemas.ai_guide import AIGuideItem, AITripGuideRequest, AITripGuideResponse

logger = logging.getLogger(__name__)

_SECTIONS = ("attractions", "restaurants", "hidden_gems", "local_tips", "transportation_tips")

_SYSTEM_PROMPT = (
    "You are a local travel expert creating a personalized family trip guide. Given the "
    "destination, family profile, budget, and already-known attractions, produce realistic, "
    "specific recommendations grounded in genuine local knowledge of that city — never invent "
    "generic chain names as if they were landmarks. Reply with ONLY JSON, no markdown, no "
    "commentary, in this exact shape: "
    '{"attractions": [{"title": "", "description": "", "why_recommended": ""}], '
    '"restaurants": [...], "hidden_gems": [...], "local_tips": [...], "transportation_tips": [...]} '
    "attractions/restaurants/hidden_gems should have 3-5 items each; local_tips and "
    "transportation_tips should have 2-4 short, practical items each."
)


def _valid_item(item) -> bool:
    return isinstance(item, dict) and bool(item.get("title"))


class AITripGuideService:
    def __init__(self, session: AsyncSession):
        self.dest_repo = DestinationRepository(session)
        self.places_provider = get_places_provider()

    async def generate(self, request: AITripGuideRequest) -> AITripGuideResponse:
        dest = await self.dest_repo.get_with_relations(request.destination_id)
        if not dest:
            raise NotFoundError("Destination not found")

        city = dest.city.name if dest.city else ""
        country = dest.city.country.name if dest.city and dest.city.country else ""

        if not settings.GROQ_API_KEY:
            return AITripGuideResponse(destination_id=dest.id, city=city, country=country, available=False)

        data = {}
        try:
            client = AsyncGroq(api_key=settings.GROQ_API_KEY)
            response = await client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": await self._build_prompt(city, country, dest, request)},
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            content = response.choices[0].message.content or ""
            data = self._parse(content)
        except Exception as exc:
            logger.warning("AI trip guide generation failed: %s", exc)

        sections = {
            section: [AIGuideItem(**item) for item in data.get(section, []) if _valid_item(item)]
            for section in _SECTIONS
        }
        return AITripGuideResponse(
            destination_id=dest.id,
            city=city,
            country=country,
            available=bool(data),
            **sections,
        )

    async def _build_prompt(self, city: str, country: str, dest, request: AITripGuideRequest) -> str:
        children = [m for m in request.members if m.age < 18]
        lines = [
            f"Destination: {city}, {country}.",
            f"Party: {len(request.members)} traveler(s)"
            + (
                f", including {len(children)} child(ren) aged {', '.join(str(c.age) for c in children)}"
                if children
                else ""
            )
            + ".",
            f"Budget: EUR {request.budget:.0f}.",
        ]
        interests = request.interests or sorted({i for c in children for i in c.interests})
        if interests:
            lines.append(f"Interests: {', '.join(interests)}.")
        known = [a.name for a in (dest.attractions or [])][:8]
        if known:
            lines.append(f"Already-known attractions (do not just repeat these): {', '.join(known)}.")

        # Ground restaurant/attraction suggestions in real current places when available.
        real_restaurants = await self.places_provider.search_places(
            PlaceSearchCriteria(city=city, country=country, category="restaurant", max_results=5)
        )
        if real_restaurants:
            names = ", ".join(f"{p.name} ({p.rating}★)" if p.rating else p.name for p in real_restaurants)
            lines.append(f"Real restaurants currently operating there, for inspiration: {names}.")

        return "\n".join(lines)

    @staticmethod
    def _parse(content: str) -> dict:
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if "\n" in text:
                text = text.split("\n", 1)[1]
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            return {}
        try:
            parsed = json.loads(text[start : end + 1])
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
