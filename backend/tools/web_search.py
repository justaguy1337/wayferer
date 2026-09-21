import asyncio

from duckduckgo_search import DDGS


def _search_sync(query: str, max_results: int) -> list[dict]:
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))


async def web_search(query: str, max_results: int = 8) -> list[dict]:
    return await asyncio.to_thread(_search_sync, query, max_results)
