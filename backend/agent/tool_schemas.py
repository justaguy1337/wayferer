TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_places",
            "description": "Search for attractions, restaurants, nature spots, museums, etc. near a location. Use this to discover candidate places before building an itinerary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Free-text description of what to look for, e.g. 'anime attractions' or 'ramen restaurants'."},
                    "location": {"type": "string", "description": "City or area name, e.g. 'Tokyo'."},
                    "max_results": {"type": "integer", "default": 20},
                    "category": {"type": "string", "description": "Optional category hint: anime, food, nature, museum, attraction, shopping, restaurant."},
                },
                "required": ["query", "location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_place_details",
            "description": "Get opening hours, website, contact info and other details for one specific place. Only call this for places you've shortlisted, not every search result.",
            "parameters": {
                "type": "object",
                "properties": {"place_id": {"type": "string"}},
                "required": ["place_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_nearby",
            "description": "Find places around a specific coordinate, e.g. restaurants near a hotel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                    "category": {"type": "string", "description": "anime, food, nature, museum, attraction, shopping, restaurant"},
                    "radius": {"type": "integer", "default": 1000, "description": "Search radius in meters."},
                },
                "required": ["latitude", "longitude"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_route",
            "description": "Calculate travel time and distance between two coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "'lat,lon' string"},
                    "destination": {"type": "string", "description": "'lat,lon' string"},
                    "mode": {"type": "string", "enum": ["car", "walk", "bike", "transit"], "default": "car"},
                },
                "required": ["origin", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_route_matrix",
            "description": "Calculate travel times between multiple locations at once. Useful for clustering places geographically before scheduling.",
            "parameters": {
                "type": "object",
                "properties": {
                    "locations": {"type": "array", "items": {"type": "string"}, "description": "List of 'lat,lon' strings."},
                    "mode": {"type": "string", "enum": ["car", "walk", "bike", "transit"], "default": "car"},
                },
                "required": ["locations"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather forecast for a location and date. Only reliable within ~5 days of today; further out it returns a note instead of fabricated data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                },
                "required": ["location", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": "Search flight offers between two airports.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "Origin IATA airport code, e.g. BLR"},
                    "destination": {"type": "string", "description": "Destination IATA airport code, e.g. NRT"},
                    "departure_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "return_date": {"type": "string", "description": "YYYY-MM-DD, omit for one-way"},
                    "passengers": {"type": "integer", "default": 1},
                },
                "required": ["origin", "destination", "departure_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_hotels",
            "description": "Search real hotel rates near a location via LiteAPI, sorted cheapest first. Sandbox pricing (test data), not confirmed bookable rates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City or area name, e.g. 'Tokyo' or 'Shinjuku, Tokyo'"},
                    "check_in": {"type": "string", "description": "YYYY-MM-DD"},
                    "check_out": {"type": "string", "description": "YYYY-MM-DD"},
                    "guests": {"type": "integer", "default": 1},
                    "max_price": {"type": "number", "description": "Optional max total stay price in INR to filter results."},
                },
                "required": ["location", "check_in", "check_out"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_events",
            "description": "Find events (concerts, festivals, exhibitions, markets) happening in a location during a date range, via web search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "category": {"type": "string", "description": "e.g. anime, music, food, sports"},
                },
                "required": ["location", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_travel_requirements",
            "description": "Look up visa/entry/passport requirements for a nationality traveling to a destination, via web search prioritizing official sources.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nationality": {"type": "string", "description": "e.g. Indian, US"},
                    "destination": {"type": "string"},
                    "travel_date": {"type": "string", "description": "YYYY-MM-DD"},
                },
                "required": ["nationality", "destination", "travel_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": "Convert an amount from one currency to another using current exchange rates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "from_currency": {"type": "string", "description": "3-letter ISO code, e.g. INR"},
                    "to_currency": {"type": "string", "description": "3-letter ISO code, e.g. JPY"},
                },
                "required": ["amount", "from_currency", "to_currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_budget",
            "description": "Sum trip costs by category and compare against the user's total budget. All amounts must already be converted to the same currency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "flights": {"type": "number", "default": 0},
                    "hotels": {"type": "number", "default": 0},
                    "food": {"type": "number", "default": 0},
                    "transport": {"type": "number", "default": 0},
                    "activities": {"type": "number", "default": 0},
                    "miscellaneous": {"type": "number", "default": 0},
                    "total_budget": {"type": "number", "description": "The user's stated total budget, in the same currency."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "optimize_itinerary",
            "description": "Deterministically build a day-by-day schedule from a list of candidate places, respecting trip dates, pace, and weather. Call this once you've gathered enough places for the whole trip.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string"},
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "places": {
                        "type": "array",
                        "description": "Candidate places gathered from search_places/search_nearby.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "place_id": {"type": "string"},
                                "name": {"type": "string"},
                                "lat": {"type": "number"},
                                "lon": {"type": "number"},
                                "category": {"type": "string"},
                                "address": {"type": "string"},
                            },
                            "required": ["name"],
                        },
                    },
                    "pace": {"type": "string", "enum": ["relaxed", "moderate", "packed"], "default": "moderate"},
                    "daily_start_time": {"type": "string", "default": "09:00"},
                    "daily_end_time": {"type": "string", "default": "21:00"},
                    "weather_by_date": {
                        "type": "object",
                        "description": "Map of YYYY-MM-DD -> weather object returned by get_weather, for dates you've checked.",
                        "additionalProperties": True,
                    },
                    "flight": {
                        "type": "object",
                        "description": "The single best flight offer you chose from search_flights, shown to the user in the itinerary UI. Include airline/carrier, price, currency, departure/arrival times, and stops.",
                    },
                    "hotel": {
                        "type": "object",
                        "description": "The single best hotel you chose from search_hotels, shown to the user in the itinerary UI. Include name, price/rate, and address.",
                    },
                },
                "required": ["destination", "start_date", "end_date", "places"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_itinerary",
            "description": "Check a generated itinerary for time overlaps, excessive activity counts, weather conflicts, and budget overruns. Always call this after optimize_itinerary or modify_itinerary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "itinerary": {"type": "object", "description": "The itinerary object returned by optimize_itinerary or modify_itinerary."},
                    "budget": {"type": "object", "description": "The object returned by calculate_budget, if available."},
                },
                "required": ["itinerary"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "modify_itinerary",
            "description": "Remove and/or add one activity on a specific day of an existing itinerary. Source any replacement activity yourself first (e.g. via search_places) before calling this.",
            "parameters": {
                "type": "object",
                "properties": {
                    "itinerary": {"type": "object", "description": "The current itinerary object."},
                    "day_number": {"type": "integer"},
                    "remove_activity_name": {"type": "string", "description": "Name (or substring) of the activity to remove."},
                    "add_activity": {
                        "type": "object",
                        "description": "New activity to insert, with name/category/lat/lon/address/start_time/end_time.",
                    },
                },
                "required": ["itinerary", "day_number"],
            },
        },
    },
]


def _strip_unsupported_schema_keys(schema):
    """Gemini's function-parameter schema is a stricter subset of JSON Schema than OpenAI's —
    notably it rejects 'additionalProperties'. Strip anything it doesn't understand."""
    if isinstance(schema, dict):
        return {k: _strip_unsupported_schema_keys(v) for k, v in schema.items() if k != "additionalProperties"}
    if isinstance(schema, list):
        return [_strip_unsupported_schema_keys(v) for v in schema]
    return schema


def to_gemini_tool():
    from google.genai import types

    declarations = [
        types.FunctionDeclaration(
            name=t["function"]["name"],
            description=t["function"].get("description", ""),
            parameters=_strip_unsupported_schema_keys(t["function"].get("parameters")),
        )
        for t in TOOLS
    ]
    return types.Tool(function_declarations=declarations)


# Friendly, human-readable progress labels streamed to the frontend while a tool is running.
TOOL_PROGRESS_LABELS = {
    "search_places": "Discovering places to visit in {location}…",
    "get_place_details": "Checking details for a shortlisted place…",
    "search_nearby": "Looking for places nearby…",
    "calculate_route": "Calculating travel time between stops…",
    "calculate_route_matrix": "Mapping travel times between all your stops…",
    "get_weather": "Checking the weather forecast…",
    "search_flights": "Finding the best flights for you…",
    "search_hotels": "Searching for the right hotels for you…",
    "search_events": "Looking for events happening during your trip…",
    "get_travel_requirements": "Checking visa & entry requirements…",
    "convert_currency": "Converting currency…",
    "calculate_budget": "Crunching the budget numbers…",
    "optimize_itinerary": "Building your day-by-day itinerary…",
    "validate_itinerary": "Double-checking your itinerary for conflicts…",
    "modify_itinerary": "Updating your itinerary…",
}


def progress_label(tool_name: str, args: dict) -> str:
    template = TOOL_PROGRESS_LABELS.get(tool_name, f"Running {tool_name}…")
    try:
        return template.format(**args)
    except Exception:
        return template
