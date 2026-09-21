import httpx

from config import settings
from tools.geocode import geocode as _geocode

GEOAPIFY_BASE = "https://api.geoapify.com/v2/places"
DETAILS_BASE = "https://api.geoapify.com/v2/place-details"


CATEGORY_MAP = {
    "anime": "entertainment.culture,commercial.gift_and_souvenir",
    "food": "catering.restaurant,catering.cafe",
    "nature": "natural,leisure.park",
    "museum": "entertainment.museum",
    "attraction": "tourism.attraction,tourism.sights",
    "shopping": "commercial.shopping_mall",
    "restaurant": "catering.restaurant",
}


def _resolve_categories(query: str | None, category: str | None) -> str:
    if category and category in CATEGORY_MAP:
        return CATEGORY_MAP[category]
    if query:
        q = query.lower()
        for key, cats in CATEGORY_MAP.items():
            if key in q:
                return cats
    return "tourism.attraction,tourism.sights,entertainment,catering.restaurant"


def _slim_feature(props: dict) -> dict:
    # Geoapify's place_id is a long opaque token needed verbatim by get_place_details and
    # optimize_itinerary, so it's kept as-is; everything else here is trimmed hard since this
    # payload re-enters LLM context (and this org's Groq tier caps requests at 8k tokens total).
    address = props.get("formatted") or ""
    if len(address) > 70:
        address = address[:67] + "..."
    return {
        "place_id": props.get("place_id"),
        "name": props.get("name") or props.get("address_line1"),
        "category": (props.get("categories") or [None])[0],
        "address": address,
        "lat": props.get("lat"),
        "lon": props.get("lon"),
        "distance_m": props.get("distance"),
    }


async def search_places(query: str, location: str, max_results: int = 10, category: str | None = None) -> dict:
    if not settings.geoapify_api_key:
        return {"error": "GEOAPIFY_API_KEY is not configured in backend.env"}

    coords = await _geocode(location)
    if not coords:
        return {"error": f"Could not resolve location '{location}'"}
    lat, lon = coords
    categories = _resolve_categories(query, category)

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            GEOAPIFY_BASE,
            params={
                "categories": categories,
                "filter": f"circle:{lon},{lat},15000",
                "bias": f"proximity:{lon},{lat}",
                "limit": max_results,
                "apiKey": settings.geoapify_api_key,
            },
        )
        if resp.status_code >= 400:
            return {"error": f"Geoapify error {resp.status_code}", "detail": resp.text[:300]}
        data = resp.json()

    results = [_slim_feature(f.get("properties", {})) for f in data.get("features", [])]
    return {"location": location, "query": query, "results": results}


async def get_place_details(place_id: str) -> dict:
    if not settings.geoapify_api_key:
        return {"error": "GEOAPIFY_API_KEY is not configured in backend.env"}

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            DETAILS_BASE,
            params={"id": place_id, "apiKey": settings.geoapify_api_key},
        )
        if resp.status_code >= 400:
            return {"error": f"Geoapify error {resp.status_code}", "detail": resp.text[:300]}
        data = resp.json()

    features = data.get("features", [])
    if not features:
        return {"error": "No details found for this place_id"}
    props = features[0].get("properties", {})
    return {
        "place_id": place_id,
        "name": props.get("name"),
        "address": props.get("formatted"),
        "opening_hours": props.get("opening_hours"),
        "website": props.get("website"),
        "phone": props.get("contact", {}).get("phone") if props.get("contact") else None,
        "categories": props.get("categories", []),
        "wiki_and_media": props.get("wiki_and_media"),
    }


async def search_nearby(latitude: float, longitude: float, category: str = "attraction", radius: int = 1000) -> dict:
    if not settings.geoapify_api_key:
        return {"error": "GEOAPIFY_API_KEY is not configured in backend.env"}

    categories = CATEGORY_MAP.get(category, "tourism.attraction,catering.restaurant")
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            GEOAPIFY_BASE,
            params={
                "categories": categories,
                "filter": f"circle:{longitude},{latitude},{radius}",
                "bias": f"proximity:{longitude},{latitude}",
                "limit": 10,
                "apiKey": settings.geoapify_api_key,
            },
        )
        if resp.status_code >= 400:
            return {"error": f"Geoapify error {resp.status_code}", "detail": resp.text[:300]}
        data = resp.json()

    results = [_slim_feature(f.get("properties", {})) for f in data.get("features", [])]
    return {"center": {"lat": latitude, "lon": longitude}, "radius_m": radius, "results": results}
