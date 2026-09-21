import httpx

from config import settings
from tools.geocode import geocode
from tools.redirect_links import google_hotels_url

LITEAPI_URL = "https://api.liteapi.travel/v3.0/hotels/rates"
SEARCH_RADIUS_M = 8000


def _cheapest_rate(rate_entry: dict) -> tuple[float, str] | None:
    best = None
    for room_type in rate_entry.get("roomTypes", []):
        for rate in room_type.get("rates", []):
            total = (rate.get("retailRate", {}).get("total") or [{}])[0]
            amount = total.get("amount")
            if amount is None:
                continue
            if best is None or amount < best[0]:
                best = (amount, total.get("currency"))
    return best


async def search_hotels(
    location: str,
    check_in: str,
    check_out: str,
    guests: int = 1,
    max_price: float | None = None,
) -> dict:
    if not settings.liteapi_key:
        return {"error": "LITEAPI_KEY is not configured in backend.env"}

    coords = await geocode(location)
    if not coords:
        return {"error": f"Could not resolve location '{location}'"}
    lat, lon = coords

    body = {
        "latitude": lat,
        "longitude": lon,
        "radius": SEARCH_RADIUS_M,
        "checkin": check_in,
        "checkout": check_out,
        "currency": "INR",
        "guestNationality": "IN",
        "occupancies": [{"adults": max(guests, 1)}],
        "timeout": 8,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            LITEAPI_URL, json=body, headers={"X-API-Key": settings.liteapi_key, "Content-Type": "application/json"}
        )
        if resp.status_code >= 400:
            return {"error": f"LiteAPI error {resp.status_code}", "detail": resp.text[:300]}
        data = resp.json()

    rates_by_hotel_id = {d.get("hotelId"): d for d in data.get("data", [])}

    hotels = []
    for h in data.get("hotels", []):
        rate_entry = rates_by_hotel_id.get(h.get("id"))
        cheapest = _cheapest_rate(rate_entry) if rate_entry else None
        if cheapest is None:
            continue
        price, currency = cheapest
        if max_price is not None and price > max_price:
            continue
        hotels.append(
            {
                "name": h.get("name"),
                "address": h.get("address"),
                "lat": h.get("latitude"),
                "lon": h.get("longitude"),
                "rating": h.get("rating"),
                "stars": h.get("stars"),
                "price": round(price, 2),
                "currency": currency,
                "redirect_url": google_hotels_url(h.get("name") or "", location),
            }
        )

    hotels.sort(key=lambda x: x["price"])

    return {
        "location": location,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
        "hotels": hotels[:10],
    }
