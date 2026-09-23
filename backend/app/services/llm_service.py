"""
LLM-based query understanding + response generation.

Two-step flow:
  1. `understand_query`  -> ask the model to classify intent and extract a
     location from free-text (in any language), returned as strict JSON.
  2. `generate_reply`    -> feed the fetched weather data back to the model
     and ask it to produce a natural-language, user-friendly answer in the
     requested language.

This keeps "understanding" and "phrasing" separate so the weather facts you
show the user always come from the real API data, not from the LLM's own
guess (avoids hallucinated numbers).
"""
import json
from typing import Optional

from openai import AsyncOpenAI

from app.config import settings

client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
)

INTENT_SYSTEM_PROMPT = """You are a query-understanding engine for a weather assistant called WeatherGPT.
Given a user's message (which may be in English or an Indian regional language),
classify it and extract a location.

Respond with ONLY a JSON object, no other text, matching this shape:
{
  "intent": "current_weather" | "forecast" | "alerts" | "general",
  "location": string or null,   // best-guess place name mentioned, null if none given
  "days": integer or null       // number of forecast days requested, if applicable
}

Rules:
- "current_weather": asking what the weather is like right now / today.
- "forecast": asking about upcoming days, "will it rain tomorrow", weekly outlook.
- "alerts": asking about warnings, cyclones, floods, storms, advisories, danger.
- "general": greetings, thanks, or anything not about a specific weather lookup.
- If no location is mentioned, set "location" to null.
"""

REPLY_SYSTEM_PROMPT = """You are WeatherGPT, a friendly, concise conversational weather assistant
built for farmers, aviation, disaster managers, and the general public in India.

You will be given structured weather data as JSON. Turn it into a short, clear,
natural-language answer in the requested language. Rules:
- Only state facts present in the data. Never invent numbers.
- Keep it conversational and to the point (2-4 sentences), unless data includes
  multiple forecast days, in which case briefly summarize each.
- If the data includes active alerts, lead with the alert and its severity,
  in plain non-alarmist language, and suggest a sensible precaution.
- If given a language other than English, respond fully in that language.
"""


async def understand_query(message: str) -> dict:
    resp = await client.chat.completions.create(
        model=settings.OPENROUTER_MODEL,
        messages=[
            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    print("OPENROUTER RAW RESPONSE:", repr(resp.choices[0].message.content))
return json.loads(resp.choices[0].message.content)


async def generate_reply(user_message: str, intent: str, weather_data: Optional[dict], language: str) -> str:
    context = {
        "user_message": user_message,
        "intent": intent,
        "language": language,
        "weather_data": weather_data,
    }
    resp = await client.chat.completions.create(
        model=settings.OPENROUTER_MODEL,
        messages=[
            {"role": "system", "content": REPLY_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(context, default=str)},
        ],
        temperature=0.4,
    )
    return resp.choices[0].message.content.strip()


async def general_reply(user_message: str, language: str) -> str:
    resp = await client.chat.completions.create(
        model=settings.OPENROUTER_MODEL,
        messages=[
            {"role": "system", "content": (
                "You are WeatherGPT, a friendly weather assistant. "
                f"Reply briefly in language code '{language}'. "
                "If asked something unrelated to weather, gently steer back to what you can help with."
            )},
            {"role": "user", "content": user_message},
        ],
        temperature=0.5,
    )
    return resp.choices[0].message.content.strip()
