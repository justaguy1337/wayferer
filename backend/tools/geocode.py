import httpx

from config import settings

GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"


async def geocode(location: str) -> tuple[float, float] | None:
    if not settings.geoapify_api_key:
        return None
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            GEOCODE_URL,
            params={"text": location, "limit": 1, "apiKey": settings.geoapify_api_key},
        )
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features", [])
        if not features:
            return None
        lon, lat = features[0]["geometry"]["coordinates"]
        return lat, lon
