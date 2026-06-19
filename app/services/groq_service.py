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