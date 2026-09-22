# WeatherGPT Backend (MVP)

A FastAPI backend for **WeatherGPT** — a conversational AI weather assistant.
This is a fast, working MVP covering the core loop: natural-language chat →
intent understanding → live weather data → natural-language reply, plus
direct REST endpoints for current weather, forecast, and alerts.

## What's included

| Feature | Status |
|---|---|
| Conversational chat endpoint (`/api/chat`) with GPT-based intent + location extraction | ✅ |
| Current weather, 5-day forecast, severe weather alerts (OpenWeatherMap) | ✅ |
| Chat history persistence (PostgreSQL) | ✅ |
| CORS configured for a separate frontend | ✅ |
| Multilingual replies (pass a `language` code; LLM replies in that language) | ✅ basic |
| NWP model (GFS/WRF) integration, MQTT/WIS2.0, voice input, GIS layers | 🔲 not in this MVP — see "Next steps" |

## Architecture

```
app/
  main.py              FastAPI app, CORS, router registration
  config.py            Settings (reads .env)
  database.py          SQLAlchemy engine/session
  models.py            ORM models (ChatMessage, WeatherAlertLog)
  schemas.py           Pydantic request/response types
  routers/
    chat.py            POST /api/chat, GET /api/chat/history/{session_id}
    weather.py         GET /api/weather/{current,forecast,alerts}
  services/
    weather_service.py Wraps OpenWeatherMap (geocoding, current, forecast, alerts)
    llm_service.py      Wraps OpenAI (intent extraction + reply generation)
```

**Design choice:** the LLM never invents weather numbers. It only classifies
intent/location, then a separate call turns the *real* API data into natural
language. This keeps answers factually grounded.

## Setup

### 1. Prerequisites
- Python 3.11+
- PostgreSQL (or use the included `docker-compose.yml`)
- An [OpenAI API key](https://platform.openai.com/api-keys)
- An [OpenWeatherMap API key](https://openweathermap.org/api) — free tier works
  for current weather + 5-day forecast. The `/alerts` endpoint uses **One Call
  API 3.0**, which needs a separate (also has free tier) subscription.

### 2. Install

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and fill in OPENAI_API_KEY, OPENWEATHER_API_KEY, DATABASE_URL
```

### 3. Start Postgres (if you don't have one running)

```bash
docker compose up -d db
```

### 4. Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive Swagger docs.

## Connecting your TypeScript UI

Example fetch from your frontend:

```ts
async function sendChatMessage(sessionId: string, message: string, language = "en") {
  const res = await fetch("http://localhost:8000/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message, language }),
  });
  if (!res.ok) throw new Error(`Chat request failed: ${res.status}`);
  return res.json(); // { session_id, reply, intent, location_resolved, data }
}
```

```ts
async function getCurrentWeather(city: string) {
  const res = await fetch(`http://localhost:8000/api/weather/current?city=${encodeURIComponent(city)}`);
  return res.json();
}
```

Set `ALLOWED_ORIGINS` in `.env` to your frontend's dev/prod URL(s), comma-separated.

## API Reference

### `POST /api/chat`
```json
// Request
{ "session_id": "abc-123", "message": "Will it rain in Chennai tomorrow?", "language": "en" }

// Response
{
  "session_id": "abc-123",
  "reply": "Yes, there's a moderate chance of rain in Chennai tomorrow...",
  "intent": "forecast",
  "location_resolved": "Chennai, Tamil Nadu, IN",
  "data": { "location": "...", "daily": [ ... ] }
}
```

### `GET /api/weather/current?city=Delhi`
### `GET /api/weather/forecast?city=Delhi&days=5`
### `GET /api/weather/alerts?city=Delhi`
### `GET /api/chat/history/{session_id}`
### `GET /api/health`

## Next steps to fill out the full problem statement

This MVP focuses on speed-to-demo. To grow toward the full spec:

1. **NWP models (GFS/WRF):** replace/augment `weather_service.py` with calls
   to NOAA GFS or your own WRF output (via NetCDF/GRIB parsing, e.g. `xarray`
   + `cfgrib`), served through a dedicated ingestion microservice.
2. **IMD / government data:** add another provider module to `services/` for
   India Meteorological Department bulletins/warnings.
3. **Real-time ingestion at scale:** introduce MQTT or WIS2.0 subscriber
   workers that write into `weather_alert_log` and push updates over
   WebSocket to connected clients.
4. **Voice:** add an endpoint that accepts audio, transcribes via Whisper,
   and feeds the text into the existing `/api/chat` pipeline; return TTS
   audio in the response.
5. **Multilingual depth:** currently relies on the LLM's own multilingual
   ability. For production, validate against known Indian language edge
   cases and consider a dedicated translation layer for numbers/units.
6. **Auth & rate limiting:** add API keys/JWT auth and per-user rate limits
   before any public deployment.
7. **Migrations:** replace `Base.metadata.create_all` with Alembic once the
   schema stabilizes.
