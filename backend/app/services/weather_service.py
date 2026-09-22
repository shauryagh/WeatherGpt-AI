"""
Weather data provider service.

Uses OpenWeatherMap as the concrete data source for the MVP because it gives
current weather + forecast + government-issued severe weather alerts through
one API family, with a generous free tier — good for a fast demo.

Swap-out point: replace the internals of these three functions with calls to
IMD/NWP (GFS/WRF) outputs later; the function signatures / return shapes are
what the rest of the app (LLM service, routers) depends on, so nothing else
needs to change.
"""
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.config import settings


class WeatherServiceError(Exception):
    pass


async def geocode_location(city: str) -> tuple[float, float, str]:
    """Turn a place name into (lat, lon, resolved_display_name)."""
    url = f"{settings.OPENWEATHER_BASE_URL}/geo/1.0/direct"
    params = {"q": city, "limit": 1, "appid": settings.OPENWEATHER_API_KEY}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        results = resp.json()

    if not results:
        raise WeatherServiceError(f"Could not find location: {city}")

    place = results[0]
    display_name = ", ".join(
        filter(None, [place.get("name"), place.get("state"), place.get("country")])
    )
    return place["lat"], place["lon"], display_name


async def get_current_weather(lat: float, lon: float, location_name: Optional[str] = None) -> dict:
    url = f"{settings.OPENWEATHER_BASE_URL}/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    return {
        "location": location_name or data.get("name", "Unknown"),
        "latitude": lat,
        "longitude": lon,
        "temperature_c": data["main"]["temp"],
        "feels_like_c": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
        "wind_speed_ms": data["wind"]["speed"],
        "condition": data["weather"][0]["main"],
        "description": data["weather"][0]["description"],
        "observed_at": datetime.now(timezone.utc),
    }


async def get_forecast(lat: float, lon: float, location_name: Optional[str] = None, days: int = 5) -> dict:
    """5-day / 3-hour forecast, collapsed to one representative entry per day."""
    url = f"{settings.OPENWEATHER_BASE_URL}/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    # Take the midday (~12:00) slot for each day as the representative forecast
    daily = []
    seen_dates = set()
    for entry in data.get("list", []):
        dt = datetime.fromtimestamp(entry["dt"], tz=timezone.utc)
        date_key = dt.date()
        if date_key in seen_dates:
            continue
        if dt.hour not in (11, 12, 13):
            continue
        seen_dates.add(date_key)
        daily.append({
            "datetime": dt,
            "temperature_c": entry["main"]["temp"],
            "condition": entry["weather"][0]["main"],
            "description": entry["weather"][0]["description"],
            "pop": entry.get("pop", 0.0),
        })
        if len(daily) >= days:
            break

    return {
        "location": location_name or data.get("city", {}).get("name", "Unknown"),
        "latitude": lat,
        "longitude": lon,
        "daily": daily,
    }


async def get_alerts(lat: float, lon: float, location_name: Optional[str] = None) -> dict:
    """
    Severe weather alerts via OpenWeatherMap One Call API 3.0.
    Requires a One Call 3.0 subscription (has a free tier with a request cap).
    """
    url = f"{settings.OPENWEATHER_BASE_URL}/data/3.0/onecall"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": settings.OPENWEATHER_API_KEY,
        "exclude": "minutely,hourly,daily,current",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    alerts = []
    for a in data.get("alerts", []):
        alerts.append({
            "event": a.get("event", "Weather Alert"),
            "severity": a.get("tags", [None])[0] if a.get("tags") else None,
            "description": a.get("description"),
            "source": a.get("sender_name", "OpenWeatherMap"),
            "issued_at": datetime.fromtimestamp(a["start"], tz=timezone.utc),
            "expires_at": datetime.fromtimestamp(a["end"], tz=timezone.utc) if a.get("end") else None,
        })

    return {"location": location_name or f"{lat},{lon}", "alerts": alerts}
