import httpx

from config import settings

TOMTOM_ROUTING_BASE = "https://api.tomtom.com/routing/1/calculateRoute"
TOMTOM_MATRIX_BASE = "https://api.tomtom.com/routing/1/matrix/2"

MODE_MAP = {
    "car": "car",
    "drive": "car",
    "driving": "car",
    "walk": "pedestrian",
    "walking": "pedestrian",
    "pedestrian": "pedestrian",
    "bike": "bicycle",
    "bicycle": "bicycle",
    "transit": "car",  # TomTom has no public transit mode; approximate with car/pedestrian
}


async def calculate_route(origin: str, destination: str, mode: str = "car") -> dict:
    """origin/destination are 'lat,lon' strings."""
    if not settings.tomtom_api_key:
        return {"error": "TOMTOM_API_KEY is not configured in backend.env"}

    travel_mode = MODE_MAP.get(mode.lower(), "car")
    url = f"{TOMTOM_ROUTING_BASE}/{origin}:{destination}/json"

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            url,
            params={"key": settings.tomtom_api_key, "travelMode": travel_mode},
        )
        if resp.status_code >= 400:
            return {"error": f"TomTom error {resp.status_code}", "detail": resp.text[:300]}
        data = resp.json()

    routes = data.get("routes", [])
    if not routes:
        return {"error": "No route found"}
    summary = routes[0]["summary"]
    return {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "distance_km": round(summary["lengthInMeters"] / 1000, 2),
        "duration_minutes": round(summary["travelTimeInSeconds"] / 60, 1),
    }


async def calculate_route_matrix(locations: list[str], mode: str = "car") -> dict:
    """locations is a list of 'lat,lon' strings. Returns an NxN duration/distance matrix."""
    if not settings.tomtom_api_key:
        return {"error": "TOMTOM_API_KEY is not configured in backend.env"}

    travel_mode = MODE_MAP.get(mode.lower(), "car")
    points = [{"point": {"latitude": float(lat), "longitude": float(lon)}} for loc in locations for lat, lon in [loc.split(",")]]

    body = {"origins": points, "destinations": points}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            TOMTOM_MATRIX_BASE,
            params={"key": settings.tomtom_api_key, "travelMode": travel_mode},
            json=body,
        )
        if resp.status_code >= 400:
            return {"error": f"TomTom error {resp.status_code}", "detail": resp.text[:300]}
        data = resp.json()

    n = len(locations)
    duration_matrix = [[0] * n for _ in range(n)]
    distance_matrix = [[0] * n for _ in range(n)]
    for cell in data.get("data", []):
        i = cell["originIndex"]
        j = cell["destinationIndex"]
        route = cell.get("routeSummary")
        if route:
            duration_matrix[i][j] = round(route["travelTimeInSeconds"] / 60, 1)
            distance_matrix[i][j] = round(route["lengthInMeters"] / 1000, 2)

    return {
        "locations": locations,
        "mode": mode,
        "duration_minutes_matrix": duration_matrix,
        "distance_km_matrix": distance_matrix,
    }
