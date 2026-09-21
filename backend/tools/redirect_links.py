from urllib.parse import quote


def google_flights_url(origin: str, destination: str, departure_date: str, return_date: str | None = None) -> str:
    query = f"Flights from {origin} to {destination} on {departure_date}"
    if return_date:
        query += f" returning {return_date}"
    return f"https://www.google.com/travel/flights?q={quote(query)}"


def google_hotels_url(hotel_name: str, location: str) -> str:
    query = f"{hotel_name} {location}".strip()
    return f"https://www.google.com/travel/hotels?q={quote(query)}"
