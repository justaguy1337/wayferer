import datetime

from tools.optimizer import PACE_TARGETS


def _parse(t: str) -> datetime.datetime:
    return datetime.datetime.strptime(t, "%H:%M")


def validate_itinerary(itinerary: dict, budget: dict | None = None) -> dict:
    issues = []
    pace = itinerary.get("pace", "moderate")
    max_activities = PACE_TARGETS.get(pace, PACE_TARGETS["moderate"])

    for day in itinerary.get("days", []):
        day_num = day.get("day_number")
        activities = sorted(day.get("activities", []), key=lambda a: a.get("start_time", "00:00"))

        if len(activities) > max_activities:
            issues.append(
                {
                    "type": "TOO_MANY_ACTIVITIES",
                    "day": day_num,
                    "message": f"Day {day_num} has {len(activities)} activities, more than the '{pace}' pace target of {max_activities}.",
                }
            )

        for a in activities:
            try:
                start = _parse(a["start_time"])
                end = _parse(a["end_time"])
            except (KeyError, ValueError):
                issues.append({"type": "INVALID_SCHEDULE", "day": day_num, "message": f"Activity '{a.get('name')}' has an invalid or missing start/end time."})
                continue
            if end <= start:
                issues.append({"type": "INVALID_SCHEDULE", "day": day_num, "message": f"Activity '{a.get('name')}' ends before it starts."})

            if a.get("weather_warning"):
                issues.append({"type": "WEATHER_CONFLICT", "day": day_num, "message": f"'{a.get('name')}': {a['weather_warning']}"})

        for i in range(len(activities) - 1):
            try:
                end_i = _parse(activities[i]["end_time"])
                start_next = _parse(activities[i + 1]["start_time"])
            except (KeyError, ValueError):
                continue
            if end_i > start_next:
                issues.append(
                    {
                        "type": "TIME_OVERLAP",
                        "day": day_num,
                        "message": f"'{activities[i]['name']}' overlaps with '{activities[i + 1]['name']}'.",
                    }
                )
            elif (start_next - end_i).total_seconds() / 60 > 90:
                issues.append(
                    {
                        "type": "EXCESSIVE_TRAVEL_GAP",
                        "day": day_num,
                        "message": f"Over 90 minutes of gap/travel between '{activities[i]['name']}' and '{activities[i + 1]['name']}'.",
                    }
                )

    if budget and budget.get("over_budget"):
        issues.append(
            {
                "type": "BUDGET_EXCEEDED",
                "day": None,
                "message": f"Total spend exceeds budget by {abs(budget.get('difference', 0))}.",
            }
        )

    return {"valid": len(issues) == 0, "issues": issues}
