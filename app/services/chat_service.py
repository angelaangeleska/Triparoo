from groq import Groq
from app.core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

BASE_SYSTEM_PROMPT = """You are a helpful family travel assistant for Triparoo, a family trip planning platform.

When recommending destinations:
- Always consider the family budget
- Always consider children's ages
- Suggest specific attractions suitable for the family
- Be concise and friendly
- If asked about prices, give approximate EUR amounts
- Always respond in the same language the user writes in

Keep responses short and conversational (2-4 sentences max unless listing options)."""


def build_system_prompt(destinations: list[dict]) -> str:
    dest_info = "\n".join([
        f"- {d['city']}, {d['country']}: family score {d['family_score']}, "
        f"attractions: {', '.join(d['attractions'])}"
        for d in destinations
    ])
    return f"{BASE_SYSTEM_PROMPT}\n\nAvailable destinations:\n{dest_info}"


async def chat_with_ai(
    message: str,
    history: list[dict],
    destinations: list[dict],
) -> str:
    system_prompt = build_system_prompt(destinations)
    
    messages = [{"role": "system", "content": system_prompt}]
    
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    
    messages.append({"role": "user", "content": message})
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=500,
        temperature=0.7,
    )
    
    return response.choices[0].message.content