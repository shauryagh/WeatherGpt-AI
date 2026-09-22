from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.services import weather_service
from app.schemas import CurrentWeatherResponse, ForecastResponse, AlertsResponse

router = APIRouter(prefix="/api/weather", tags=["weather"])


async def _resolve_coords(city: Optional[str], lat: Optional[float], lon: Optional[float]):
    if lat is not None and lon is not None:
        return lat, lon, city
    if city:
        lat, lon, resolved_name = await weather_service.geocode_location(city)
        return lat, lon, resolved_name
    raise HTTPException(status_code=400, detail="Provide either 'city' or both 'lat' and 'lon'.")


@router.get("/current", response_model=CurrentWeatherResponse)
async def current_weather(
    city: Optional[str] = Query(None),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
):
    try:
        lat, lon, name = await _resolve_coords(city, lat, lon)
        return await weather_service.get_current_weather(lat, lon, name)
    except weather_service.WeatherServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/forecast", response_model=ForecastResponse)
async def forecast(
    city: Optional[str] = Query(None),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    days: int = Query(5, ge=1, le=5),
):
    try:
        lat, lon, name = await _resolve_coords(city, lat, lon)
        return await weather_service.get_forecast(lat, lon, name, days=days)
    except weather_service.WeatherServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/alerts", response_model=AlertsResponse)
async def alerts(
    city: Optional[str] = Query(None),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
):
    try:
        lat, lon, name = await _resolve_coords(city, lat, lon)
        return await weather_service.get_alerts(lat, lon, name)
    except weather_service.WeatherServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))
