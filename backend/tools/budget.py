def calculate_budget(
    flights: float = 0,
    hotels: float = 0,
    food: float = 0,
    transport: float = 0,
    activities: float = 0,
    miscellaneous: float = 0,
    total_budget: float | None = None,
) -> dict:
    """All amounts are expected in the same currency (convert with convert_currency first)."""
    breakdown = {
        "flights": round(flights, 2),
        "hotels": round(hotels, 2),
        "food": round(food, 2),
        "transport": round(transport, 2),
        "activities": round(activities, 2),
        "miscellaneous": round(miscellaneous, 2),
    }
    total_spend = round(sum(breakdown.values()), 2)

    result = {"breakdown": breakdown, "total_spend": total_spend}

    if total_budget is not None:
        difference = round(total_budget - total_spend, 2)
        result["total_budget"] = total_budget
        result["difference"] = difference
        result["over_budget"] = difference < 0
        result["percent_used"] = round((total_spend / total_budget) * 100, 1) if total_budget else None

    return result
