import httpx

from config import settings

DUFFEL_BASE = "https://api.duffel.com"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.duffel_api_key}",
        "Duffel-Version": "v2",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def duffel_post(path: str, data: dict) -> dict:
    if not settings.duffel_api_key:
        return {"error": "DUFFEL_API_KEY is not configured in backend.env"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{DUFFEL_BASE}{path}", json={"data": data}, headers=_headers())
        if resp.status_code >= 400:
            return {"error": f"Duffel API error {resp.status_code}", "detail": resp.text[:500]}
        return resp.json()
