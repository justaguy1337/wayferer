import inspect

from tools.budget import calculate_budget
from tools.currency import convert_currency
from tools.events import search_events
from tools.flights import search_flights
from tools.hotels import search_hotels
from tools.modifier import modify_itinerary
from tools.optimizer import optimize_itinerary
from tools.places import get_place_details, search_nearby, search_places
from tools.routing import calculate_route, calculate_route_matrix
from tools.travel_requirements import get_travel_requirements
from tools.validator import validate_itinerary
from tools.weather import get_weather

TOOL_FUNCTIONS = {
    "search_places": search_places,
    "get_place_details": get_place_details,
    "search_nearby": search_nearby,
    "calculate_route": calculate_route,
    "calculate_route_matrix": calculate_route_matrix,
    "get_weather": get_weather,
    "search_flights": search_flights,
    "search_hotels": search_hotels,
    "search_events": search_events,
    "get_travel_requirements": get_travel_requirements,
    "convert_currency": convert_currency,
    "calculate_budget": calculate_budget,
    "optimize_itinerary": optimize_itinerary,
    "validate_itinerary": validate_itinerary,
    "modify_itinerary": modify_itinerary,
}

# Tools whose result should be persisted as the session's current itinerary snapshot.
ITINERARY_PRODUCING_TOOLS = {"optimize_itinerary", "modify_itinerary"}


async def call_tool(name: str, arguments: dict):
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return {"error": f"Unknown tool '{name}'"}
    try:
        if inspect.iscoroutinefunction(func):
            return await func(**arguments)
        return func(**arguments)
    except TypeError as exc:
        return {"error": f"Invalid arguments for {name}: {exc}"}
    except Exception as exc:
        return {"error": f"{name} failed: {exc}"}


def extract_itinerary(tool_name: str, result: dict) -> dict | None:
    if tool_name == "optimize_itinerary" and isinstance(result, dict) and "days" in result:
        return result
    if tool_name == "modify_itinerary" and isinstance(result, dict) and "itinerary" in result:
        return result["itinerary"]
    return None
