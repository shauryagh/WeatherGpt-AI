from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ChatMessage
from app.schemas import ChatRequest, ChatResponse
from app.services import llm_service, weather_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    # 1. Log the incoming user message
    db.add(ChatMessage(session_id=req.session_id, role="user", content=req.message, language=req.language))
    db.commit()

    # 2. Understand the query (intent + location) via the LLM
    try:
        understanding = await llm_service.understand_query(req.message)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Query understanding failed: {e}")

    intent = understanding.get("intent", "general")
    location_text = understanding.get("location")
    days = understanding.get("days") or 5

    weather_data = None
    location_resolved = None

    try:
        # 3. Resolve coordinates: prefer explicit lat/lon from the client (e.g. GPS),
        #    else geocode a location mentioned in the message.
        lat, lon = req.latitude, req.longitude
        if lat is None or lon is None:
            if location_text:
                lat, lon, location_resolved = await weather_service.geocode_location(location_text)
            elif intent != "general":
                # No location given and no GPS coords -> ask the user, don't guess.
                reply = (
                    "Could you tell me which location you'd like the weather for? "
                    "You can also share your device location."
                )
                db.add(ChatMessage(session_id=req.session_id, role="assistant", content=reply, language=req.language))
                db.commit()
                return ChatResponse(session_id=req.session_id, reply=reply, intent=intent)

        if intent == "current_weather":
            weather_data = await weather_service.get_current_weather(lat, lon, location_resolved)
            location_resolved = weather_data["location"]
        elif intent == "forecast":
            weather_data = await weather_service.get_forecast(lat, lon, location_resolved, days=days)
            location_resolved = weather_data["location"]
        elif intent == "alerts":
            weather_data = await weather_service.get_alerts(lat, lon, location_resolved)
            location_resolved = weather_data["location"]

    except weather_service.WeatherServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # 4. Generate the natural-language reply
    if intent == "general":
        reply_text = await llm_service.general_reply(req.message, req.language)
    else:
        reply_text = await llm_service.generate_reply(req.message, intent, weather_data, req.language)

    # 5. Log assistant reply
    db.add(ChatMessage(session_id=req.session_id, role="assistant", content=reply_text, language=req.language))
    db.commit()

    return ChatResponse(
        session_id=req.session_id,
        reply=reply_text,
        intent=intent,
        location_resolved=location_resolved,
        data=weather_data,
    )


@router.get("/history/{session_id}")
def get_history(session_id: str, db: Session = Depends(get_db)):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [
        {"role": m.role, "content": m.content, "created_at": m.created_at}
        for m in messages
    ]
