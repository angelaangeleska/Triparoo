from groq import Groq
from app.core.config import settings


client = Groq(api_key=settings.GROQ_API_KEY)


async def generate_itinerary_with_ai(
    city: str,
    country: str,
    duration_days: int,
    members: list,
    budget: float,
    attractions: list[str],
) -> str:
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

async def explain_recommendations_with_ai(
    context_members: list,
    budget: float,
    destinations: list[dict],
) -> list[dict]:
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