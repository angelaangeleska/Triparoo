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
) -> str | None:
    members_desc = []
    for m in members:
        age = m.get("age", "?")
        interests = m.get("interests", [])
        if interests:
            members_desc.append(f"age {age} (interests: {', '.join(interests)})")
        else:
            members_desc.append(f"age {age}")
    members_str = ", ".join(members_desc)

    attractions_str = ", ".join(attractions[:6]) if attractions else "local attractions"

    prompt = f"""Create a detailed {duration_days}-day family travel itinerary for {city}, {country}.

Family members: {members_str}
Total budget: ${budget}
Available attractions: {attractions_str}

For each day provide:
- Morning activity
- Afternoon activity  
- Evening activity
- Estimated daily cost

Make it engaging, family-friendly, and realistic. Format each day clearly as "Day 1:", "Day 2:", etc."""

    client = _get_client()
    if not client:
        return None

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an expert family travel planner. Create practical, fun, and budget-conscious itineraries.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=1500,
        temperature=0.7,
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
) -> list[dict]:
    """Score destinations 0-100 for a specific family using Groq."""
    client = _get_client()
    if not client or not destinations:
        return []

    members_str = _format_members_for_prompt(members)
    travel_dates_str = _format_travel_dates(travel_month, start_date, end_date)

    dest_lines = []
    for d in destinations:
        dest_lines.append(f"- {d['city']}, {d['country']}")
    dest_list = "\n".join(dest_lines)

    prompt = f"""Score each destination from 0 to 100 for how well it fits THIS specific family.
All destinations listed are already within the family's ${budget:.0f} budget — do NOT rank by price or cost.
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
            temperature=0.4,
        )
        text = response.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(text)
        if not isinstance(parsed, list):
            logger.warning("Groq AI scoring returned non-list JSON")
            return []

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
        return results
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        logger.warning("Failed to parse Groq AI destination scores: %s", exc)
        return []
    except Exception as exc:
        logger.warning("Groq AI destination scoring failed: %s", exc)
        return []


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