"""Groq-based LLM reasoning for the hybrid recommendation engine.

Implements the `RecommendationProvider` protocol (app/recommendation/base.py)
so it plugs into `HybridRecommendationService` exactly like the flight/
accommodation providers plug into their factories. Never raises — any Groq
failure or missing API key falls back to a deterministic templated
explanation so the recommend endpoint keeps working.
"""

from __future__ import annotations

import json
import logging

from groq import AsyncGroq

from app.core.config import settings
from app.recommendation.base import (
    RecommendationContext,
    RecommendationExplanation,
    ScoredDestination,
)

logger = logging.getLogger(__name__)

_RECOMMEND_SYSTEM_PROMPT = (
    "You are a warm, knowledgeable family travel advisor. Given a family's profile and a "
    "shortlist of already rule-scored candidate destinations, write a short natural-language "
    "explanation for each one describing why it suits THIS family, and your own independent "
    "0-100 match score reflecting how well it fits their ages, interests, and budget. "
    "Reply with ONLY a JSON array, no markdown, no commentary, in this exact shape: "
    '[{"destination_id": <int>, "match_score": <0-100>, "explanation": "<2-3 sentences>", '
    '"highlights": ["<short phrase>", "<short phrase>"]}]'
)

_ITINERARY_SYSTEM_PROMPT = (
    "You are a friendly travel writer. Given a family's day-by-day itinerary outline, write one "
    "short, vivid sentence (max 25 words) per day that sets the mood — no logistics, just "
    "atmosphere. Reply with ONLY a JSON array, no markdown: "
    '[{"day_number": <int>, "narrative": "<one sentence>"}]'
)


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            text = text.split("\n", 1)[1]
    return text.strip()


class GroqRecommendationProvider:
    """RecommendationProvider implementation backed by Groq's hosted LLMs."""

    def __init__(self):
        self._client = AsyncGroq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def _build_prompt(self, context: RecommendationContext, candidates: list[ScoredDestination]) -> str:
        children = [m for m in context.members if m.age < 18]
        adults = [m for m in context.members if m.age >= 18]
        family_desc = f"{len(adults)} adult(s)"
        if children:
            ages = ", ".join(str(c.age) for c in children)
            interests = sorted({i for c in children for i in c.interests})
            family_desc += f" and {len(children)} child(ren) aged {ages}"
            if interests:
                family_desc += f", interested in {', '.join(interests)}"

        lines = [f"Family: {family_desc}.", f"Budget: EUR {context.budget:.0f}."]
        if context.origin_label:
            lines.append(f"Departing from: {context.origin_label}.")
        lines.append("Candidate destinations (already ranked by a rule engine):")
        for c in candidates:
            lines.append(
                f"- id={c.destination_id}: {c.city}, {c.country} — rule score {c.rule_score:.0f}/100, "
                f"estimated total cost EUR {c.estimated_total_cost:.0f}."
            )
        return "\n".join(lines)

    async def explain_recommendations(
        self, context: RecommendationContext, candidates: list[ScoredDestination]
    ) -> list[RecommendationExplanation]:
        if not candidates:
            return []
        if not self.enabled:
            return self._fallback(candidates)

        try:
            response = await self._client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": _RECOMMEND_SYSTEM_PROMPT},
                    {"role": "user", "content": self._build_prompt(context, candidates)},
                ],
                temperature=0.6,
                max_tokens=1200,
            )
            content = response.choices[0].message.content or ""
            return self._parse_response(content, candidates)
        except Exception as exc:
            logger.warning("Groq recommendation call failed, falling back to rule score: %s", exc)
            return self._fallback(candidates)

    def _parse_response(
        self, content: str, candidates: list[ScoredDestination]
    ) -> list[RecommendationExplanation]:
        text = _strip_code_fence(content)
        start, end = text.find("["), text.rfind("]")
        if start == -1 or end == -1:
            return self._fallback(candidates)
        try:
            items = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return self._fallback(candidates)

        by_id = {c.destination_id: c for c in candidates}
        results: list[RecommendationExplanation] = []
        seen: set[int] = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            dest_id = item.get("destination_id")
            if dest_id not in by_id or dest_id in seen:
                continue
            seen.add(dest_id)
            try:
                match_score = float(item.get("match_score", by_id[dest_id].rule_score))
            except (TypeError, ValueError):
                match_score = by_id[dest_id].rule_score
            match_score = max(0.0, min(100.0, match_score))
            results.append(
                RecommendationExplanation(
                    destination_id=dest_id,
                    llm_score=match_score,
                    explanation=str(item.get("explanation", "")).strip(),
                    highlights=[str(h) for h in (item.get("highlights") or [])][:5],
                )
            )

        for c in candidates:
            if c.destination_id not in seen:
                results.append(self._fallback([c])[0])
        return results

    @staticmethod
    def _fallback(candidates: list[ScoredDestination]) -> list[RecommendationExplanation]:
        return [
            RecommendationExplanation(
                destination_id=c.destination_id,
                llm_score=c.rule_score,
                explanation=(
                    f"{c.city}, {c.country} scored {c.rule_score:.0f}/100 for your family based on "
                    "budget fit, season, and child-friendly attractions."
                ),
                highlights=[],
            )
            for c in candidates
        ]


async def generate_itinerary_narratives(city: str, country: str, days: list) -> dict[int, str]:
    """One short atmospheric sentence per itinerary day. Returns {} on any failure or missing key."""
    if not settings.GROQ_API_KEY or not days:
        return {}

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    outline = "\n".join(f"Day {d.day_number}: {d.title}" for d in days)
    try:
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": _ITINERARY_SYSTEM_PROMPT},
                {"role": "user", "content": f"Destination: {city}, {country}\n{outline}"},
            ],
            temperature=0.7,
            max_tokens=600,
        )
        content = response.choices[0].message.content or ""
        return _parse_narratives(content)
    except Exception as exc:
        logger.warning("Groq itinerary narrative call failed: %s", exc)
        return {}


def _parse_narratives(content: str) -> dict[int, str]:
    text = _strip_code_fence(content)
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        return {}
    try:
        items = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}

    result: dict[int, str] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            result[int(item["day_number"])] = str(item["narrative"]).strip()
        except (KeyError, TypeError, ValueError):
            continue
    return result
