from tools.web_search import web_search


async def search_events(location: str, start_date: str, end_date: str, category: str | None = None) -> dict:
    query = f"{category + ' ' if category else ''}events in {location} between {start_date} and {end_date}"
    try:
        raw = await web_search(query, 8)
    except Exception as exc:
        return {"error": f"Web search failed: {exc}"}

    events = [
        {"title": r.get("title"), "summary": r.get("body"), "source_url": r.get("href")}
        for r in raw
    ]
    return {
        "location": location,
        "start_date": start_date,
        "end_date": end_date,
        "category": category,
        "events": events,
        "note": "Sourced from general web search — verify dates/tickets on the official event page before relying on them.",
    }
