import json
from datetime import date
from typing import AsyncGenerator

from google import genai
from google.genai import types

import database
from agent.registry import call_tool, extract_itinerary
from agent.tool_schemas import progress_label, to_gemini_tool
from config import settings

MAX_ITERATIONS = 20
# Gemini's context window is 1M+ tokens, so this is just a sane ceiling against a truly
# pathological tool response, not a tight budget like a smaller-context provider would need.
RESULT_CHAR_LIMIT = 40000

FALLBACK_TEXT = (
    "I gathered a lot of information but ran out of steps before wrapping up — could you ask me "
    "to continue, or narrow the request a bit?"
)

SYSTEM_PROMPT = f"""You are an expert AI travel planner agent. Today's date is {date.today().isoformat()}.

You help the user research destinations, flights, hotels, attractions, weather, routes, events and
travel/visa requirements, then build and continuously refine a personalized day-by-day itinerary.

You have tools for: places search & details, nearby search, routing (single route + route matrix),
weather, flight search, hotel search, event search, travel/visa requirements, currency conversion,
budget calculation, itinerary optimization, itinerary validation, and itinerary modification.

Guidelines:
- Ask the user for any essential missing details (origin city, dates, budget, number of travelers,
  nationality for visa checks, interests, pace preference) before doing heavy research, but don't
  interrogate them — ask only what you truly need, and make sensible assumptions for the rest.
- Use search_places / search_nearby to gather a good spread of candidate places (respect the user's
  stated interests) before calling optimize_itinerary. Pass everything you've gathered in one call.
  Gather at least (pace target × number of days) places — relaxed=3/day, moderate=4/day, packed=6/day
  — e.g. ~12 places for a 3-day moderate trip. optimize_itinerary spreads whatever you give it evenly
  across the days, so too few places means later days end up thin or empty. Once you have enough,
  stop searching and move on — don't keep calling search_places "just in case".
- After search_flights/search_hotels, pick the single best option (balance price, timing, stops,
  rating) and pass it as the `flight`/`hotel` argument to optimize_itinerary so it's shown to the user
  in the itinerary UI — don't just mention it in chat text and drop it. If a search comes back empty
  or errors (e.g. web search rate-limited), do NOT invent a plausible-sounding flight/hotel from your
  own knowledge — omit that argument entirely and tell the user you couldn't find live options right
  now, so they know to check themselves rather than trusting a fabricated name and price.
- Do currency conversions with convert_currency and work in a single currency (default to the
  currency the user stated their budget in) when calling calculate_budget.
- After optimize_itinerary or modify_itinerary, always call calculate_budget (if you have cost data)
  and then validate_itinerary. If validation reports issues, fix them (e.g. via modify_itinerary or
  by re-optimizing) before presenting the plan as final, unless the issue is minor and you explain it.
- get_weather only returns real forecasts within ~5 days of today; for trips further out, say so
  plainly instead of inventing weather.
- get_travel_requirements and search_events use general web search rather than a live booking API —
  treat results as leads to verify, not certainties, and tell the user to confirm on an official site.
  search_flights and search_hotels are real pricing APIs (Duffel, LiteAPI), but LiteAPI's sandbox
  pricing is still test data, so say so when quoting a rate.
- The itinerary you build via optimize_itinerary/modify_itinerary is shown to the user in a dedicated
  UI panel (day-by-day cards, budget breakdown, map). Do NOT re-paste the full itinerary as text in
  your chat reply — instead, write a short, warm, conversational summary of what you did, key
  highlights, trade-offs, or questions, and point out anything worth their attention (budget status,
  weather warnings, validation issues).
- When the user asks for a change, use modify_itinerary (sourcing any replacement place yourself
  first) rather than rebuilding the whole plan from scratch, unless the change is substantial.
"""

_TOOL = to_gemini_tool()

# Cheap/fast models don't always track "I already have enough data" reliably across many tool
# turns, so cap the repetition-prone research tools per turn as a hard guardrail rather than
# relying on prompting alone. Anything not listed is left uncapped (deterministic tools like
# calculate_budget/validate_itinerary are cheap to re-run and rarely loop).
TOOL_CALL_LIMITS = {
    "search_places": 5,
    "search_nearby": 5,
    "get_place_details": 6,
    "search_flights": 3,
    "search_hotels": 3,
    "search_events": 2,
    "get_travel_requirements": 2,
    "get_weather": 6,
    "calculate_route": 6,
    "calculate_route_matrix": 3,
}


def _safe_json(obj) -> str:
    try:
        text = json.dumps(obj, default=str)
    except TypeError:
        text = str(obj)
    if len(text) > RESULT_CHAR_LIMIT:
        text = text[:RESULT_CHAR_LIMIT] + "... [truncated]"
    return text


def _parse_tool_result(content: str) -> dict:
    """Gemini's FunctionResponse.response must be a struct (dict), not a raw string."""
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else {"result": parsed}
    except (json.JSONDecodeError, TypeError):
        return {"result": content}


def _extract_text(content) -> str:
    if not content or not content.parts:
        return ""
    return "".join(p.text for p in content.parts if getattr(p, "text", None))


async def _classify_new_trip(client: genai.Client, current_destination: str, message: str) -> bool:
    prompt = (
        f"The user is currently planning a trip to {current_destination}. Their new message is:\n"
        f'"{message}"\n\n'
        "Does this message describe planning a DIFFERENT trip to a different destination, or is it "
        "about/continuing the CURRENT trip (questions, changes, additions, budget talk, etc. for the "
        "same destination)? Reply with exactly one word: NEW or CONTINUE."
    )
    try:
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(temperature=0, max_output_tokens=10),
        )
        text = _extract_text(response.candidates[0].content).strip().upper()
        return text.startswith("NEW")
    except Exception:
        return False


async def _missing_essentials(client: genai.Client, session_id: str, message: str) -> str | None:
    """Only checked while the session has no itinerary yet. Cheap/fast models don't reliably
    self-regulate on "ask before researching" from prompting alone, so this is a hard gate: if
    origin/budget/dates are missing, the caller forces a tool-free, text-only turn instead of
    trusting the model to decide not to call tools on its own. The question itself should still be
    the same helpful, comprehensive ask the model used to produce on its own (dates, travelers, pace,
    interests) — not just the bare minimum to unblock research."""
    prev_summary = database.get_trip_summary(session_id)
    context = f"What's known so far: {prev_summary}\n\n" if prev_summary else ""
    prompt = (
        "A user is talking to an AI travel agent about planning a trip. Before doing real research "
        "(flights, hotels, budget math), the agent needs a clear enough picture: origin city, trip "
        "dates or duration, and budget (or an explicit 'no budget limit') are the blocking essentials. "
        "Number of travelers, pace preference (relaxed/moderate/packed), and interests are also worth "
        "asking about when unknown, though not strictly blocking.\n\n"
        f"{context}Latest message: \"{message}\"\n\n"
        "Considering everything known so far (not just the latest message in isolation): if origin, "
        "budget, or dates/duration are still missing or unclear, and the user hasn't explicitly said "
        "to just use your own judgment/defaults, write ONE warm, welcoming message asking for exactly "
        "what's missing — the blocking essentials, plus travelers/pace/interests if those are also "
        "unknown (a short numbered or bulleted list reads better than a wall of questions). Otherwise, "
        "if origin, budget, and dates/duration are all reasonably clear, reply with exactly: PROCEED"
    )
    try:
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(temperature=0.4, max_output_tokens=300),
        )
        text = _extract_text(response.candidates[0].content).strip()
        if not text or text.upper().startswith("PROCEED"):
            return None
        return text
    except Exception:
        return None


async def _update_trip_summary(client: genai.Client, session_id: str, user_message: str, assistant_text: str) -> None:
    prev_summary = database.get_trip_summary(session_id) or "(none yet)"
    prompt = (
        "Maintain a compact running summary of this trip-planning conversation for the agent's own "
        f"future reference.\n\nPrevious summary:\n{prev_summary}\n\n"
        f"Latest user message: {user_message}\n"
        f"Latest assistant response: {assistant_text[:2000]}\n\n"
        "Write an updated summary covering: destination, dates, travelers, budget, preferences, key "
        "decisions made so far (chosen flight/hotel, itinerary highlights), and open questions. Plain "
        "text, no markdown, under 200 words."
    )
    try:
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=350),
        )
        summary = _extract_text(response.candidates[0].content).strip()
        if summary:
            database.save_trip_summary(session_id, summary)
    except Exception:
        pass


def _build_contents(session_id: str) -> list[types.Content]:
    rows = database.get_messages(session_id)
    contents = []
    for r in rows:
        if r["role"] == "user":
            contents.append(types.Content(role="user", parts=[types.Part(text=r["content"] or "")]))
        elif r["role"] == "assistant" and r["tool_calls"]:
            parts = [
                types.Part(function_call=types.FunctionCall(name=tc["name"], args=json.loads(tc["arguments"] or "{}")))
                for tc in r["tool_calls"]
            ]
            contents.append(types.Content(role="model", parts=parts))
        elif r["role"] == "assistant":
            contents.append(types.Content(role="model", parts=[types.Part(text=r["content"] or "")]))
        elif r["role"] == "tool":
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part(function_response=types.FunctionResponse(name=r["name"], response=_parse_tool_result(r["content"])))],
                )
            )
    return contents


async def run_agent_turn(session_id: str, user_message: str, force: bool = False) -> AsyncGenerator[dict, None]:
    if not settings.gemini_api_key:
        yield {"type": "error", "message": "GEMINI_API_KEY is not configured in backend.env"}
        return

    client = genai.Client(api_key=settings.gemini_api_key)

    session = database.get_session(session_id)
    existing_itinerary = session.get("itinerary") if session else None
    if existing_itinerary and not force:
        if await _classify_new_trip(client, existing_itinerary.get("destination", "the current trip"), user_message):
            yield {"type": "confirm_new_trip", "message": user_message, "current_destination": existing_itinerary.get("destination")}
            return

    system_instruction = SYSTEM_PROMPT
    trip_summary = database.get_trip_summary(session_id)
    if trip_summary:
        system_instruction += f"\n\nRunning summary of this trip so far (for your own reference):\n{trip_summary}"

    if not existing_itinerary and not force:
        missing = await _missing_essentials(client, session_id, user_message)
        if missing:
            database.add_message(session_id, "user", content=user_message)
            database.add_message(session_id, "assistant", content=missing)
            yield {"type": "token", "content": missing}
            yield {"type": "done"}
            await _update_trip_summary(client, session_id, user_message, missing)
            return

    config = types.GenerateContentConfig(tools=[_TOOL], system_instruction=system_instruction, temperature=0.5)

    database.add_message(session_id, "user", content=user_message)
    contents = _build_contents(session_id)
    call_counts: dict[str, int] = {}

    for _ in range(MAX_ITERATIONS):
        response = await client.aio.models.generate_content(model=settings.gemini_model, contents=contents, config=config)

        candidate = response.candidates[0]
        parts = candidate.content.parts or [] if candidate.content else []
        function_calls = [p.function_call for p in parts if getattr(p, "function_call", None)]

        if function_calls:
            assistant_tool_calls = [
                {"id": fc.id or f"call_{i}", "name": fc.name, "arguments": json.dumps(dict(fc.args or {}), default=str)}
                for i, fc in enumerate(function_calls)
            ]
            database.add_message(session_id, "assistant", content=None, tool_calls=assistant_tool_calls)
            contents.append(candidate.content)

            for fc in function_calls:
                name = fc.name
                args = dict(fc.args or {})

                call_counts[name] = call_counts.get(name, 0) + 1
                limit = TOOL_CALL_LIMITS.get(name)

                yield {"type": "tool_start", "tool": name, "label": progress_label(name, args)}

                if limit and call_counts[name] > limit:
                    result = {
                        "error": (
                            f"You've already called {name} {limit} times this turn — that's enough. "
                            "Stop calling it and move on to the next step (e.g. optimize_itinerary) "
                            "with what you already have."
                        )
                    }
                else:
                    result = await call_tool(name, args)

                yield {"type": "tool_end", "tool": name, "label": progress_label(name, args), "result": result}

                itinerary = extract_itinerary(name, result)
                if itinerary is not None:
                    database.save_itinerary(session_id, itinerary)
                    yield {"type": "itinerary_update", "itinerary": itinerary}

                if name == "calculate_budget" and isinstance(result, dict) and "breakdown" in result:
                    database.save_budget(session_id, result)
                    yield {"type": "budget_update", "budget": result}

                if name == "search_flights" and isinstance(result, dict) and result.get("offers"):
                    options = result["offers"][:5]
                    database.save_flight_options(session_id, options)
                    yield {"type": "flight_options", "options": options}

                if name == "search_hotels" and isinstance(result, dict) and result.get("hotels"):
                    options = result["hotels"][:5]
                    database.save_hotel_options(session_id, options)
                    yield {"type": "hotel_options", "options": options}

                result_str = _safe_json(result)
                database.add_message(session_id, "tool", content=result_str, tool_call_id=fc.id or "", name=name)
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part(function_response=types.FunctionResponse(name=name, response=_parse_tool_result(result_str)))],
                    )
                )

            continue

        final_text = _extract_text(candidate.content)
        database.add_message(session_id, "assistant", content=final_text)
        yield {"type": "token", "content": final_text}
        yield {"type": "done"}
        await _update_trip_summary(client, session_id, user_message, final_text)
        return

    contents.append(
        types.Content(
            role="user",
            parts=[
                types.Part(
                    text=(
                        "You've used up your research budget for this turn. Do not call any more tools. "
                        "Summarize your best answer or plan right now using only what you've already gathered, "
                        "and tell the user what's still missing or what you'd refine next."
                    )
                )
            ],
        )
    )
    try:
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.5),
        )
        final_text = _extract_text(response.candidates[0].content) or FALLBACK_TEXT
    except Exception:
        final_text = FALLBACK_TEXT

    database.add_message(session_id, "assistant", content=final_text)
    yield {"type": "token", "content": final_text}
    yield {"type": "done"}
    await _update_trip_summary(client, session_id, user_message, final_text)
