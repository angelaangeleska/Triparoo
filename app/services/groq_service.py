import json
import logging
from datetime import date

from groq import Groq

from app.core.config import settings

logger = logging.getLogger(__name__)

MONTH_NAMES = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def _get_client() -> Groq | None:
    if not settings.GROQ_API_KEY.strip():
        return None
    return Groq(api_key=settings.GROQ_API_KEY)


async def generate_itinerary_with_ai(
    city: str,
    country: str,
    duration_days: int,
    members: list,
    budget: float,
    attractions: list[str],
    real_attractions: list[dict] | None = None,
    regenerate_count: int = 0,
) -> str | None:
    members_desc = []
    youngest_age: int | None = None
    for m in members:
        age = m.get("age", "?")
        if isinstance(age, int):
            youngest_age = age if youngest_age is None else min(youngest_age, age)
        interests = m.get("interests", [])
        if interests:
            members_desc.append(f"age {age} (interests: {', '.join(interests)})")
        else:
            members_desc.append(f"age {age}")
    members_str = ", ".join(members_desc)

    has_toddlers = youngest_age is not None and youngest_age <= 4

    if real_attractions:
        attraction_lines = []
        for i, att in enumerate(real_attractions[:20], 1):
            name = att.get("name", "Unknown")
            category = att.get("category", "attraction")
            description = att.get("description") or "Popular local attraction"
            lat = att.get("latitude")
            lon = att.get("longitude")
            coords = f" ({lat:.4f}, {lon:.4f})" if lat is not None and lon is not None else ""
            attraction_lines.append(
                f"{i}. {name} [{category}]{coords} — {description[:200]}"
            )
        attractions_block = "\n".join(attraction_lines)
        attractions_instruction = (
            "Build the itinerary PRIMARILY around these REAL places from OpenStreetMap. "
            "Use the exact place names from OpenStreetMap. Group nearby attractions on the same day "
            "using their coordinates. Do not invent fictional venues when a real one fits."
        )
    else:
        attractions_str = ", ".join(attractions[:6]) if attractions else "local attractions"
        attractions_block = attractions_str
        attractions_instruction = (
            "Use the available attractions listed above, plus well-known family-friendly spots in the city."
        )

    scheduling_notes = [
        "Consider typical opening hours — schedule indoor museums mid-morning, parks in afternoon.",
        "Allow 20–45 minutes travel time between attractions; cluster geographically close places.",
        "Include lunch (~12:00–13:00) and dinner (~18:30–19:30) breaks each day.",
    ]
    if has_toddlers:
        scheduling_notes.append(
            "Include a quiet rest/nap window (~12:30–14:30) for toddlers; keep afternoons lighter."
        )
    scheduling_block = "\n".join(f"- {note}" for note in scheduling_notes)

    regenerate_block = ""
    if regenerate_count > 0:
        regenerate_block = (
            f"\nThis is regeneration #{regenerate_count}. Create a FRESH itinerary with "
            "DIFFERENT attractions and activities than a typical first pass — explore "
            "alternative neighborhoods, lesser-known spots, and varied pacing.\n"
        )

    prompt = f"""Create a detailed {duration_days}-day family travel itinerary for {city}, {country}.
{regenerate_block}
Family members: {members_str}
Total budget: ${budget}

{attractions_instruction}

Real attractions and activities:
{attractions_block}

Family scheduling guidelines:
{scheduling_block}

For each day provide:
- Morning activity (with approximate time, e.g. 9:30 AM)
- Afternoon activity
- Evening activity
- Estimated daily cost

Write like a professional travel guide: specific place names, logical geographic order, realistic pacing for families with children. Format each day clearly as "Day 1:", "Day 2:", etc. Use bullet points starting with "-" for each activity."""

    client = _get_client()
    if not client:
        return None

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert family travel planner. Create practical, fun, and "
                    "budget-conscious itineraries using real attractions. Prioritize geographic "
                    "efficiency, age-appropriate pacing, and realistic daily schedules."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=2000,
        temperature=min(0.7 + regenerate_count * 0.08, 0.95),
    )

    return response.choices[0].message.content


def _format_members_for_prompt(members: list) -> str:
    members_desc = []
    for m in members:
        age = m.get("age", "?")
        gender = m.get("gender")
        interests = m.get("interests") or []
        parts = [f"age {age}"]
        if gender:
            parts.append(f"gender {gender}")
        if interests:
            parts.append(f"interests: {', '.join(interests)}")
        members_desc.append(", ".join(parts))
    return "; ".join(members_desc)


def _format_travel_dates(
    travel_month: int | None,
    start_date: date | None,
    end_date: date | None,
) -> str:
    if start_date and end_date:
        return f"{start_date.isoformat()} to {end_date.isoformat()}"
    if start_date:
        return start_date.isoformat()
    if travel_month and 1 <= travel_month <= 12:
        return MONTH_NAMES[travel_month - 1]
    return "not specified"


async def score_destinations_with_ai(
    members: list,
    budget: float,
    travel_month: int | None,
    destinations: list[dict],
    start_date: date | None = None,
    end_date: date | None = None,
    regenerate_count: int = 0,
) -> list[dict]:
    """Score destinations 0-100 for a specific family using Groq."""
    if not destinations:
        return []

    client = _get_client()
    if not client:
        return _fallback_groq_scores(destinations, regenerate_count)

    members_str = _format_members_for_prompt(members)
    travel_dates_str = _format_travel_dates(travel_month, start_date, end_date)

    dest_lines = []
    for d in destinations:
        dest_lines.append(f"- {d['city']}, {d['country']}")
    dest_list = "\n".join(dest_lines)

    regenerate_block = ""
    if regenerate_count > 0:
        regenerate_block = (
            f"\nThis is regeneration #{regenerate_count}. Offer FRESH perspectives — highlight "
            "different angles, alternative activities, and varied reasons than a typical first ranking.\n"
        )

    prompt = f"""Score each destination from 0 to 100 for how well it fits THIS specific family.
{regenerate_block}All destinations listed are already within the family's ${budget:.0f} budget — do NOT rank by price or cost.
Rank by children's interests, age fit, season, and travel timing only.

Family members: {members_str}
Travel dates: {travel_dates_str}

Destinations (all within budget):
{dest_list}

Scoring priorities (in order):
1. Children's stated interests — match activities and vibe to what kids enjoy
2. Age appropriateness — toddlers need easy pacing; teens need engaging experiences
3. Season and weather for the travel dates/month
4. Family-friendly atmosphere

Do NOT penalize or favor destinations based on cost — budget is already handled separately.

Return JSON only — an array with one object per destination:
[
  {{"city": "Paris", "llm_score": 85, "reason": "One sentence focused on interests, ages, and season fit."}}
]

Use the exact city names from the list. Return only valid JSON, no other text."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a family travel expert. Score destinations personally for each family. "
                        "Always respond with valid JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=min(0.4 + regenerate_count * 0.08, 0.85),
        )
        text = response.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(text)
        if not isinstance(parsed, list):
            logger.warning("Groq AI scoring returned non-list JSON")
            return _fallback_groq_scores(destinations, regenerate_count)

        results = []
        for item in parsed:
            if not isinstance(item, dict) or "city" not in item:
                continue
            score = item.get("llm_score", item.get("score", 50))
            try:
                score = max(0.0, min(100.0, float(score)))
            except (TypeError, ValueError):
                score = 50.0
            results.append(
                {
                    "city": str(item["city"]).strip(),
                    "llm_score": round(score, 2),
                    "reason": str(item.get("reason", item.get("explanation", ""))).strip(),
                }
            )
        if not results and regenerate_count > 0:
            return _fallback_groq_scores(destinations, regenerate_count)
        return results
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        logger.warning("Failed to parse Groq AI destination scores: %s", exc)
        return _fallback_groq_scores(destinations, regenerate_count)
    except Exception as exc:
        logger.warning("Groq AI destination scoring failed: %s", exc)
        return _fallback_groq_scores(destinations, regenerate_count)


def _fallback_groq_scores(destinations: list[dict], regenerate_count: int) -> list[dict]:
    if regenerate_count <= 0:
        return []
    reasons = [
        "Matches your family's profile and travel timing.",
        "Alternative destination with strong family appeal.",
        "Rotated pick highlighting different experiences.",
    ]
    results = []
    for i, dest in enumerate(destinations):
        score = 50 + (i * 9 + regenerate_count * 13) % 40
        results.append(
            {
                "city": dest["city"],
                "llm_score": round(float(score), 2),
                "reason": reasons[(i + regenerate_count) % len(reasons)],
            }
        )
    return results


async def explain_recommendations_with_ai(
    context_members: list,
    budget: float,
    destinations: list[dict],
) -> list[dict]:
    client = _get_client()
    if not client:
        return []

    print("GROQ CALLED")
    members_desc = []
    for m in context_members:
        age = m.get("age", "?")
        interests = m.get("interests", [])
        if interests:
            members_desc.append(f"age {age} (interests: {', '.join(interests)})")
        else:
            members_desc.append(f"age {age}")
    members_str = ", ".join(members_desc)

    dest_list = ""
    for i, d in enumerate(destinations[:5], 1):
        dest_list += f"{i}. {d['city']}, {d['country']} (score: {d['rule_score']}, cost: ${d['estimated_total_cost']})\n"

    prompt = f"""You are a family travel expert. Explain why each destination is recommended for this family.

Family: {members_str}
Budget: ${budget}

Top destinations:
{dest_list}

For each destination write:
- One sentence explanation why it fits this family
- 3 highlights (short phrases)

Respond in JSON format exactly like this:
[
  {{
    "city": "Paris",
    "explanation": "...",
    "highlights": ["highlight 1", "highlight 2", "highlight 3"]
  }}
]

Return only valid JSON, no other text."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a family travel expert. Always respond with valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=1000,
        temperature=0.5,
    )

    import json
    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    print(response.choices[0].message.content)
    return json.loads(text)