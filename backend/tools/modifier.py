def modify_itinerary(
    itinerary: dict,
    day_number: int,
    remove_activity_name: str | None = None,
    add_activity: dict | None = None,
) -> dict:
    """Removes an activity (by case-insensitive substring match on name) and/or inserts a new
    one into the given day. The caller is expected to have already sourced the replacement
    activity (e.g. via search_places) and provided its start_time/end_time."""
    days = itinerary.get("days", [])
    day = next((d for d in days if d.get("day_number") == day_number), None)
    if day is None:
        return {"error": f"Day {day_number} not found in itinerary"}

    removed = None
    if remove_activity_name:
        needle = remove_activity_name.lower()
        activities = day.get("activities", [])
        for i, a in enumerate(activities):
            if needle in (a.get("name") or "").lower():
                removed = activities.pop(i)
                break
        if removed is None:
            return {"error": f"No activity matching '{remove_activity_name}' found on day {day_number}"}

    if add_activity:
        day.setdefault("activities", []).append(add_activity)
        day["activities"].sort(key=lambda a: a.get("start_time", "00:00"))

    return {"itinerary": itinerary, "removed": removed, "added": add_activity}
