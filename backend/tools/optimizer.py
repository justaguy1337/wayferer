import datetime
import math

PACE_TARGETS = {"relaxed": 3, "moderate": 4, "packed": 6}

DEFAULT_DURATION_MINUTES = {
    "museum": 120,
    "nature": 90,
    "park": 90,
    "attraction": 90,
    "restaurant": 60,
    "food": 60,
    "shopping": 90,
    "entertainment": 120,
}
OUTDOOR_CATEGORIES = {"nature", "park", "attraction"}
TRAVEL_BUFFER_MINUTES = 25


def _duration_for(category: str | None) -> int:
    if category and category.lower() in DEFAULT_DURATION_MINUTES:
        return DEFAULT_DURATION_MINUTES[category.lower()]
    return 90


def _polar_sort(places: list[dict]) -> list[dict]:
    lats = [p["lat"] for p in places if p.get("lat") is not None]
    lons = [p["lon"] for p in places if p.get("lon") is not None]
    if not lats:
        return places
    centroid = (sum(lats) / len(lats), sum(lons) / len(lons))

    def angle(p):
        if p.get("lat") is None or p.get("lon") is None:
            return 0
        return math.atan2(p["lat"] - centroid[0], p["lon"] - centroid[1])

    return sorted(places, key=angle)


def optimize_itinerary(
    destination: str,
    start_date: str,
    end_date: str,
    places: list[dict],
    pace: str = "moderate",
    daily_start_time: str = "09:00",
    daily_end_time: str = "21:00",
    weather_by_date: dict | None = None,
    flight: dict | None = None,
    hotel: dict | None = None,
) -> dict:
    start = datetime.date.fromisoformat(start_date)
    end = datetime.date.fromisoformat(end_date)
    num_days = (end - start).days + 1
    if num_days < 1:
        return {"error": "end_date must be on or after start_date"}

    target_per_day = PACE_TARGETS.get(pace, PACE_TARGETS["moderate"])
    weather_by_date = weather_by_date or {}

    ordered = _polar_sort(places)

    day_start = datetime.datetime.strptime(daily_start_time, "%H:%M")
    day_end = datetime.datetime.strptime(daily_end_time, "%H:%M")
    window_minutes = int((day_end - day_start).total_seconds() / 60)

    days = []
    idx = 0
    for day_num in range(1, num_days + 1):
        date = (start + datetime.timedelta(days=day_num - 1)).isoformat()
        weather = weather_by_date.get(date)
        rainy = bool(weather and weather.get("rain_probability", 0) >= 70)

        # If there aren't enough places to hit target_per_day on every remaining day, spread what's
        # left evenly instead of letting earlier days greedily exhaust the list and starving later
        # ones (recomputed each day so a day that under-fills due to the time window doesn't starve
        # the days after it either).
        remaining_days = num_days - day_num + 1
        remaining_places = len(ordered) - idx
        day_target = min(target_per_day, -(-remaining_places // remaining_days)) if remaining_places > 0 else 0

        activities = []
        clock = day_start
        count = 0
        while idx < len(ordered) and count < day_target:
            place = ordered[idx]
            category = (place.get("category") or "").lower()
            duration = _duration_for(category)

            if clock + datetime.timedelta(minutes=duration) > day_end:
                break

            activity = {
                "place_id": place.get("place_id"),
                "name": place.get("name"),
                "category": category or None,
                "lat": place.get("lat"),
                "lon": place.get("lon"),
                "address": place.get("address"),
                "start_time": clock.strftime("%H:%M"),
                "end_time": (clock + datetime.timedelta(minutes=duration)).strftime("%H:%M"),
            }
            if rainy and category in OUTDOOR_CATEGORIES:
                activity["weather_warning"] = (
                    f"{weather.get('rain_probability')}% rain chance forecast — consider an indoor alternative."
                )

            activities.append(activity)
            clock += datetime.timedelta(minutes=duration + TRAVEL_BUFFER_MINUTES)
            idx += 1
            count += 1

        days.append({"day_number": day_num, "date": date, "weather": weather, "activities": activities})

    unscheduled = ordered[idx:]
    return {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "pace": pace,
        "flight": flight,
        "hotel": hotel,
        "days": days,
        "unscheduled_places": [{"name": p.get("name"), "place_id": p.get("place_id")} for p in unscheduled],
    }
