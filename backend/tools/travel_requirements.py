from tools.web_search import web_search


async def get_travel_requirements(nationality: str, destination: str, travel_date: str) -> dict:
    query = (
        f"official visa and entry requirements for {nationality} citizens traveling to "
        f"{destination} {travel_date} passport validity site:gov OR site:mofa OR site:embassy"
    )
    try:
        raw = await web_search(query, 8)
    except Exception as exc:
        return {"error": f"Web search failed: {exc}"}

    sources = [
        {"title": r.get("title"), "summary": r.get("body"), "source_url": r.get("href")}
        for r in raw
    ]
    return {
        "nationality": nationality,
        "destination": destination,
        "travel_date": travel_date,
        "sources": sources,
        "note": (
            "These are web-search leads, not a guarantee. Prioritize official government/embassy/"
            "immigration sites in the results above, and tell the user to verify before booking."
        ),
    }
