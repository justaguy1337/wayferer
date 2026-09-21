from tools.duffel_client import duffel_post
from tools.redirect_links import google_flights_url


async def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None = None,
    passengers: int = 1,
) -> dict:
    slices = [{"origin": origin, "destination": destination, "departure_date": departure_date}]
    if return_date:
        slices.append({"origin": destination, "destination": origin, "departure_date": return_date})

    body = {
        "slices": slices,
        "passengers": [{"type": "adult"} for _ in range(max(passengers, 1))],
        "cabin_class": "economy",
    }

    data = await duffel_post("/air/offer_requests?return_offers=true", body)
    if "error" in data:
        return data

    payload = data.get("data", {})
    offers = []
    for offer in payload.get("offers", [])[:10]:
        itineraries = []
        for sl in offer.get("slices", []):
            segments = [
                {
                    "from": seg["origin"]["iata_code"],
                    "to": seg["destination"]["iata_code"],
                    "departure_time": seg["departing_at"],
                    "arrival_time": seg["arriving_at"],
                    "carrier": seg["marketing_carrier"]["iata_code"],
                    "flight_number": seg["marketing_carrier_flight_number"],
                }
                for seg in sl.get("segments", [])
            ]
            itineraries.append({"segments": segments, "stops": len(segments) - 1})

        offers.append(
            {
                "id": offer.get("id"),
                "price": offer.get("total_amount"),
                "currency": offer.get("total_currency"),
                "itineraries": itineraries,
                "redirect_url": google_flights_url(origin, destination, departure_date, return_date),
            }
        )

    result = {
        "origin": origin,
        "destination": destination,
        "departure_date": departure_date,
        "return_date": return_date,
        "offers": offers,
    }
    if not payload.get("live_mode", True):
        result["note"] = "Duffel test-mode data — sandbox pricing on Duffel Airways, not real bookable fares."
    return result
