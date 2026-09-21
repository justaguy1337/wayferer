import datetime

import httpx

from config import settings

GEOCODE_URL = "https://api.openweathermap.org/geo/1.0/direct"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


async def get_weather(location: str, date: str) -> dict:
    """date is 'YYYY-MM-DD'. OpenWeather's free tier only forecasts ~5 days out;
    beyond that we return a climatology-style note instead of fabricating data."""
    if not settings.openweather_api_key:
        return {"error": "OPENWEATHER_API_KEY is not configured in backend.env"}

    async with httpx.AsyncClient(timeout=20) as client:
        geo_resp = await client.get(
            GEOCODE_URL,
            params={"q": location, "limit": 1, "appid": settings.openweather_api_key},
        )
        if geo_resp.status_code >= 400:
            return {"error": f"OpenWeather geocode error {geo_resp.status_code}"}
        geo = geo_resp.json()
        if not geo:
            return {"error": f"Could not resolve location '{location}'"}
        lat, lon = geo[0]["lat"], geo[0]["lon"]

        target_date = datetime.date.fromisoformat(date)
        days_out = (target_date - datetime.date.today()).days

        if days_out < 0 or days_out > 5:
            return {
                "location": location,
                "date": date,
                "note": (
                    "Requested date is outside the 5-day forecast window supported by the "
                    "free OpenWeather API. Treat as unconfirmed and re-check closer to the trip."
                ),
                "forecast_available": False,
            }

        resp = await client.get(
            FORECAST_URL,
            params={"lat": lat, "lon": lon, "appid": settings.openweather_api_key, "units": "metric"},
        )
        if resp.status_code >= 400:
            return {"error": f"OpenWeather forecast error {resp.status_code}"}
        data = resp.json()

    day_entries = [e for e in data.get("list", []) if e["dt_txt"].startswith(date)]
    if not day_entries:
        return {"location": location, "date": date, "forecast_available": False, "note": "No forecast entries for this date"}

    temps = [e["main"]["temp"] for e in day_entries]
    rain_probs = [e.get("pop", 0) * 100 for e in day_entries]
    conditions = [e["weather"][0]["main"] for e in day_entries]
    winds = [e["wind"]["speed"] for e in day_entries]

    return {
        "location": location,
        "date": date,
        "forecast_available": True,
        "temperature_min": round(min(temps), 1),
        "temperature_max": round(max(temps), 1),
        "condition": max(set(conditions), key=conditions.count),
        "rain_probability": round(max(rain_probs), 1),
        "wind_speed": round(sum(winds) / len(winds), 1),
    }
