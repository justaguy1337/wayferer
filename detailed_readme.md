# Wayfarer — Detailed Technical Reference

This is the deep-dive companion to the top-level `README.md` (which just covers setup). This
document explains *how* the system works, *why* it's built the way it is, and where to look for
each piece of behavior — for whoever picks this codebase up next, including future-you.

---

## 1. What this is

Wayfarer is a single-user, no-auth AI travel planner. A FastAPI backend runs an agentic loop
against Google Gemini, which calls 15 tools (real provider APIs + deterministic internal logic)
to research and build a day-by-day itinerary. A React/Vite frontend shows the agent's research
happening live (streamed tool-by-tool over SSE) and renders the resulting itinerary, budget, map,
and flight/hotel recommendations.

Everything is stored in one local SQLite file — no external database, no user accounts.

---

## 2. Architecture at a glance

```
Browser (React/Vite, :5173)
  │  REST: /api/sessions (CRUD)         SSE: POST /api/chat/stream
  ▼
FastAPI backend (main.py)
  routers/trips.py            routers/chat.py
       │                            │
       │                            ▼
       │                   agent/orchestrator.py
       │                   (Gemini tool-calling loop
       │                    + guardrails, see §5.4)
       │                            │
       │                    function_call / function_response
       │                            ▼
       │                   agent/registry.py → tools/*.py
       │                            │
       │              ┌─────────────┼──────────────────────┐
       │              ▼             ▼                       ▼
       │        External APIs   Web search            Deterministic
       │        (Geoapify,      (DuckDuckGo, no        internal logic
       │         TomTom,         key: events,          (budget math,
       │         OpenWeather,    visa/travel            itinerary
       │         Duffel,         requirements)          optimizer,
       │         LiteAPI,                                validator,
       │         Frankfurter)                             modifier)
       │                            │
       ▼                            ▼
  database.py  ◄─────────── all reads/writes go through here
       │
       ▼
  SQLite (backend/travel_agent.db) — sessions + messages tables
```

---

## 3. Tech stack

| Layer | Choice | Why |
|---|---|---|
| Backend framework | FastAPI + uvicorn | async-native, plays well with streaming and async tool calls |
| LLM | Google Gemini (`gemini-3.5-flash-lite`) | 1M-token context, cheapest current Flash-tier model (see §8 for why we moved off Groq) |
| Frontend | React + Vite | fast dev loop, no framework overhead needed for a single-page app |
| Storage | SQLite (stdlib `sqlite3`, no ORM) | single-user, zero-ops, file-based |
| Map | Leaflet + OpenStreetMap tiles | free, no API key |
| Charts | Hand-rolled inline SVG (`BudgetTrendChart.jsx`) | small enough not to need a charting library |

No MCP servers, no message queue, no auth layer — deliberately, given the single-user scope (see
§8.1).

---

## 4. Directory structure

```
backend/
  main.py                  FastAPI app, CORS, router mounting
  config.py                Settings (env vars), loaded once at import
  database.py              All SQLite access — schema, migrations, CRUD
  models.py                Pydantic request bodies
  backend.env               Real API keys (gitignored)
  backend.env.example       Template with signup links, no real values
  agent/
    orchestrator.py         The agent loop — see §5.4
    tool_schemas.py          Tool definitions (OpenAI-shaped) + Gemini schema converter
    registry.py              Dispatches a tool name/args to the actual Python function
  tools/                     One module per capability — see §5.6
  routers/
    chat.py                  POST /api/chat/stream (SSE)
    trips.py                 Session CRUD

frontend/
  src/
    App.jsx                  All top-level state + orchestration of API calls
    api.js                    fetch wrappers + the SSE stream reader
    components/               See §6.2
    styles/global.css          Design tokens (colors, fonts, radii)
```

---

## 5. Backend

### 5.1 `main.py`

Minimal: creates the FastAPI app, adds `CORSMiddleware` with `allow_origins=["*"]` /
`allow_credentials=False` (wide open — this is a local single-user app, and we hit enough
CORS/port friction during development that a strict allowlist wasn't worth it), calls
`database.init_db()` on startup, and mounts the two routers. Also has a `if __name__ ==
"__main__"` block so `python main.py` reads `HOST`/`PORT` from `backend.env` and runs with
`reload=True` — added specifically so the frontend's `VITE_API_BASE` and the backend's actual
port can never drift apart (see §9 for the saga that motivated this).

### 5.2 `config.py` and environment variables

`config.py` loads `backend.env` with `override=True` (so it always wins over any stray
shell-level environment variable — this was a real bug we hit once). All settings are plain class
attributes on a `Settings` singleton, imported everywhere as `from config import settings`.

| Env var | Used by | Get it at |
|---|---|---|
| `GEMINI_API_KEY` | `agent/orchestrator.py` (all LLM calls) | aistudio.google.com/apikey |
| `GEMINI_MODEL` | same | — (defaults to `gemini-3.5-flash-lite`) |
| `GEOAPIFY_API_KEY` | `tools/places.py`, `tools/geocode.py` | myprojects.geoapify.com |
| `TOMTOM_API_KEY` | `tools/routing.py` | developer.tomtom.com |
| `OPENWEATHER_API_KEY` | `tools/weather.py` | home.openweathermap.org/api_keys |
| `DUFFEL_API_KEY` | `tools/flights.py`, `tools/duffel_client.py` | app.duffel.com/join (instant, free test mode) |
| `LITEAPI_KEY` | `tools/hotels.py` | liteapi.travel (instant, free sandbox) |
| `HOST` / `PORT` | `main.py` | — |
| `DATABASE_PATH` | `database.py` | — (defaults to `backend/travel_agent.db`) |

No key needed for currency (`tools/currency.py`, hits Frankfurter directly) or web search
(`tools/events.py`, `tools/travel_requirements.py`, via `duckduckgo-search`).

### 5.3 `database.py` and schema

Two tables, no ORM:

```sql
sessions (id, title, itinerary, budget, trip_summary, flight_options, hotel_options,
          created_at, updated_at)
messages (id, session_id, role, content, tool_calls, tool_call_id, name, created_at)
```

`itinerary`, `budget`, `flight_options`, `hotel_options`, and each message's `tool_calls` are
stored as JSON text and parsed on read. A "session" *is* a trip *is* a chat — there's no
separate concept for any of the three; deleting a session deletes its whole conversation.

**Migrations**: `trip_summary`, `flight_options`, `hotel_options` were added after the initial
schema. Since `CREATE TABLE IF NOT EXISTS` doesn't add columns to an already-existing table,
`SESSION_COLUMN_MIGRATIONS` + a `PRAGMA table_info` check in `init_db()` adds any missing columns
on startup. Add new session-level columns there, not in `SCHEMA`, so existing `.db` files upgrade
automatically instead of needing to be deleted.

### 5.4 `agent/orchestrator.py` — the agent loop

This is the core of the system. `run_agent_turn(session_id, user_message, force=False)` is an
async generator; each `yield` is one SSE event sent to the frontend. Event types: `tool_start`,
`tool_end`, `itinerary_update`, `budget_update`, `flight_options`, `hotel_options`,
`confirm_new_trip`, `token`, `done`, `error`.

Step by step:

1. **New-trip detection** (only if the session already has a saved itinerary, and `force` isn't
   set): `_classify_new_trip()` makes one cheap Gemini call asking "is this message about a
   different destination, or continuing the current trip?" If it's a different trip, the turn
   stops immediately and yields `confirm_new_trip` — nothing is saved yet. The frontend shows a
   Yes/No banner; "Yes" creates a new session and resends the message there; "No" resends to the
   same session with `force=True`, which skips this check entirely.

2. **Missing-essentials gate** (only if there's no itinerary yet, and not forced):
   `_missing_essentials()` checks the running `trip_summary` plus the new message for the
   blocking essentials — origin, budget, dates/duration. If any are missing, the turn **never
   calls a single tool**: it saves the classifier's own clarifying question directly as the
   assistant's reply and returns. See §8.2 for why this is a hard gate rather than a prompt
   instruction.

3. **Build the Gemini `contents` list** from the session's full message history
   (`_build_contents()`), reconstructing `Content`/`Part`/`FunctionCall`/`FunctionResponse`
   objects from the plain JSON stored in SQLite. Notably, Gemini's `thought_signature` (an opaque
   continuity token for a specific tool-call exchange) is *not* persisted or replayed — this was
   verified empirically to still work fine across turns (see git history / conversation log for
   the test), so history reconstruction doesn't need to carry it.

4. **The tool-calling loop**, up to `MAX_ITERATIONS = 20`: call Gemini with
   `tools=[_TOOL]` → if the response contains `function_call` parts, execute each one via
   `agent/registry.py`, stream `tool_start`/`tool_end`, persist results, and loop; if it's a plain
   text response, that's the final answer — save it, yield `token` + `done`, and return.

   - **Circuit breaker**: `TOOL_CALL_LIMITS` caps how many times a given tool can actually execute
     within one turn (e.g. `search_places: 5`). Once hit, further calls to that tool get a
     synthetic `{"error": "stop calling this, move on"}` instead of hitting the real API — no
     extra cost, and it reliably unsticks the model without ever letting it truly loop forever.
   - **Side-effect persistence**: `optimize_itinerary`/`modify_itinerary` results save to
     `sessions.itinerary`; `calculate_budget` saves to `sessions.budget`; `search_flights` /
     `search_hotels` save their top-5 to `flight_options`/`hotel_options`. Each also emits its own
     SSE event so the frontend updates live, mid-turn, without waiting for the final text.
   - If `MAX_ITERATIONS` is exhausted without a text response, one final tool-free call is forced
     ("you've used your budget, wrap up now"); `FALLBACK_TEXT` is used if even that fails.

5. **Rolling trip summary**: after every final response (success or forced wrap-up),
   `_update_trip_summary()` makes one more Gemini call to fold the new exchange into a ~200-word
   running summary, saved to `sessions.trip_summary`. This summary is prepended to the system
   instruction on the *next* turn, and is what the missing-essentials/new-trip checks read instead
   of re-deriving state from scratch each time. It's also shown verbatim in `TripDashboard.jsx`.

### 5.5 `agent/tool_schemas.py` and `agent/registry.py`

`tool_schemas.py` defines all 15 tools once, in OpenAI's `{"type": "function", "function": {...}}`
shape (`TOOLS`). `to_gemini_tool()` converts that into Gemini's `types.Tool` at import time,
stripping keys Gemini's schema validator rejects (`additionalProperties` is the only one found so
far — Gemini's parameter schema is a stricter JSON-Schema subset than OpenAI's). Keeping the
canonical definition OpenAI-shaped means it'd be easy to point at a different OpenAI-compatible
provider again without rewriting every tool description.

`registry.py`'s `call_tool(name, args)` dispatches by name to the actual async/sync Python
function in `tools/`, and `extract_itinerary(name, result)` recognizes which tools produce an
itinerary payload worth persisting.

### 5.6 `tools/` — every tool

| Tool | Module | Provider | Notes |
|---|---|---|---|
| `search_places`, `search_nearby` | `places.py` | Geoapify | Results are deliberately slim (`_slim_feature`) — only `place_id`, `name`, one `category`, truncated `address`, `lat`/`lon`, `distance_m`. `place_id` is never altered (needed verbatim downstream). |
| `get_place_details` | `places.py` | Geoapify | Full detail (hours, website, contact) — only called for shortlisted places. |
| `calculate_route`, `calculate_route_matrix` | `routing.py` | TomTom | No public-transit mode in TomTom; approximated with car/pedestrian. |
| `get_weather` | `weather.py` | OpenWeather | Free tier only forecasts ~5 days out; further out, returns a note instead of fabricated data. |
| `search_flights` | `flights.py` | Duffel | Test-mode key → sandbox pricing on "Duffel Airways," not real bookable fares. Also attaches a constructed Google Flights `redirect_url`. |
| `search_hotels` | `hotels.py` | LiteAPI | Geocodes the location (`tools/geocode.py`), searches `/v3.0/hotels/rates`, matches the `hotels[]` static-content array to the `data[]` rates array by `hotelId`, takes the cheapest rate per hotel, returns top 10 cheapest-first. Sandbox key → test pricing. Also attaches a constructed Google Hotels `redirect_url`. |
| `search_events`, `get_travel_requirements` | `events.py`, `travel_requirements.py` | DuckDuckGo (`web_search.py`, shared helper) | No key, but genuinely rate-limits under repeated use (observed firsthand, not theoretical) — handled gracefully (returns an error the agent can talk around), not a crash. |
| `convert_currency` | `currency.py` | Frankfurter | No key. |
| `calculate_budget` | `budget.py` | — (internal) | Pure arithmetic; compares against `total_budget` if given. |
| `optimize_itinerary` | `optimizer.py` | — (internal) | See below. |
| `validate_itinerary` | `validator.py` | — (internal) | Checks time overlaps, activity-count vs. pace, weather conflicts, budget overrun. |
| `modify_itinerary` | `modifier.py` | — (internal) | Removes/adds one activity on a given day of an existing itinerary object; preserves `flight`/`hotel`/everything else untouched since it only touches `days[].activities`. |

**`optimize_itinerary` in detail**: places are polar-sorted around their geographic centroid
(`_polar_sort`) so consecutive places in the list tend to be near each other, then divided across
days. The per-day quota is **recomputed each day** as
`min(pace_target, ceil(remaining_places / remaining_days))` rather than a fixed quota — this
fixes a real bug where a fixed quota let Day 1 greedily consume most of a short place list, leaving
later days thin or empty (see §9). `flight`/`hotel` are optional passthrough arguments the agent
fills in from its own `search_flights`/`search_hotels` results; they're not looked up again here.

### 5.7 `routers/`

`chat.py`: `POST /api/chat/stream` wraps `run_agent_turn()` in a `StreamingResponse`
(`text/event-stream`), one `data: {...}\n\n` line per yielded event.

`trips.py`: plain CRUD over `database.py` — `GET/POST /api/sessions`, `GET/PATCH/DELETE
/api/sessions/{id}`. `GET /api/sessions/{id}` also attaches the session's `messages` (filtered to
user/assistant turns with content — tool-call bookkeeping rows aren't sent to the frontend).

---

## 6. Frontend

### 6.1 `App.jsx` — state and data flow

All state lives in `App.jsx`: `sessions`, `activeId`, `messages`, `itinerary`, `budget`,
`flightOptions`, `hotelOptions`, `tripSummary`, `pending` (the in-flight turn's activity feed +
streaming text), `pendingConfirm` (new-trip banner state), `showDashboard`.

`sendToAgent(sessionId, text, force)` is the single place that calls `streamChat()` and dispatches
every SSE event type to the right state setter. `handleSend()` (user typed something) appends the
user bubble once and delegates to `sendToAgent`; `resolveNewTripConfirm(startNew)` handles both
banner outcomes without re-adding a duplicate user bubble.

The assistant's final text is revealed with a client-side typewriter effect (`revealText()`) —
the backend sends the complete text in one `token` event, not a real token stream; the reveal
animation is purely cosmetic, done client-side to avoid an extra round trip.

### 6.2 Component reference

| Component | Purpose |
|---|---|
| `Sidebar` | Trip list, new/rename/delete-with-confirm |
| `ChatPanel` | Message list, empty state, new-trip confirm banner, hosts `Composer` |
| `Composer` | The input box; placeholder text changes based on *why* it's disabled (streaming vs. awaiting confirm) |
| `ActivityFeed` | Live "Finding the best flights for you…" pills while a turn is in flight |
| `ItineraryPanel` | The right-hand compact view: map, travel summary, budget chart, budget meter, recommended options, day cards |
| `TripDashboard` | Full-screen modal — same data, larger layout, plus the trip summary text |
| `DayCard` | One day's schedule (boarding-pass-style time rail) |
| `TripMap` | Leaflet map, one color per day, dashed route lines between that day's stops |
| `TravelSummary` | The *chosen* flight/hotel cards (from `itinerary.flight`/`itinerary.hotel`) |
| `RecommendedOptions` | The top-5 flight/hotel *options* (from `flightOptions`/`hotelOptions`), each linking out via `redirect_url`. Takes a `layout` prop: `"column"` (stacked, used in the sidebar) or `"row"` (hotels left / flights right, used in the dashboard) |
| `BudgetMeter` | Segmented bar breakdown by category |
| `BudgetTrendChart` | Line chart: cumulative spend across trip days vs. a dashed budget-ceiling reference line. Flights+hotel cost is charged to "Day 0" (pre-trip), the rest spread evenly across days. Clickable to open the dashboard (`expandable` prop turns this off inside the dashboard itself) |

### 6.3 SSE event → UI mapping

| Event | Frontend effect |
|---|---|
| `tool_start` / `tool_end` | `ActivityFeed` pill added / marked done |
| `itinerary_update` | `setItinerary()` — day cards, map, travel summary, budget chart all re-render |
| `budget_update` | `setBudget()` |
| `flight_options` / `hotel_options` | `setFlightOptions()` / `setHotelOptions()` — feeds `RecommendedOptions` |
| `confirm_new_trip` | `setPendingConfirm()` — shows the Yes/No banner, disables the composer |
| `token` | Client-side typewriter reveal, then appended to `messages` |
| `done` | Clears `pending`, re-enables composer |
| `error` | Shows the dismissable toast |

---

## 7. Setup & running

See the top-level `README.md`. Short version: `pip install -r backend/requirements.txt`, fill in
`backend/backend.env`, `python backend/main.py`; separately `npm install && npm run dev` in
`frontend/`.

---

## 8. Design decisions worth knowing about

### 8.1 Why no MCP, no auth, no separate DB server

The original architecture sketch for this project called for standing up real MCP servers per
provider. Given this is a single-user local tool, that was a deliberate simplification: tools are
plain async Python functions, organized and typed exactly as the MCP diagram grouped them, so
wrapping them in real MCP servers later is mechanical if ever needed — without paying for that
complexity (process lifecycle management, IPC) up front. Same logic for auth (none — it's your
own machine) and the database (SQLite file, not Postgres).

### 8.2 Why hard guardrails instead of better prompting

`gemini-3.5-flash-lite` was chosen for cost (see §8.3), but a cheap/fast model doesn't reliably
self-regulate on soft instructions the way a larger model might. This showed up twice in practice:

- It kept calling `search_places` far past the point of having enough data (observed: 30+ calls
  in one turn before being manually interrupted), despite the system prompt saying "stop once you
  have enough." Fix: `TOOL_CALL_LIMITS`, a hard per-tool cap enforced in code.
- It skipped asking for origin/budget/dates entirely and just fabricated defaults, despite the
  system prompt saying to ask first. Fix: `_missing_essentials()`, a hard gate that makes tool use
  literally impossible for that turn if essentials are missing — not a request the model can
  choose to ignore.

The lesson generalized: for a cheap/fast model, prefer a deterministic check with a forced
tool-free turn (or a synthetic tool error) over adding another sentence to the system prompt and
hoping.

### 8.3 Provider history — why Groq → Gemini, why Amadeus → Duffel, why DuckDuckGo → LiteAPI

- **LLM**: started on Groq (`openai/gpt-oss-120b`) per the original spec. Groq's account tier hard-
  caps a single request at 8000 tokens (prompt + tools schema + completion combined) — and the
  15-tool schema alone, plus a few tool results, blew past that almost immediately. Switched to
  Gemini for the 1M-token context, which eliminated the entire class of problem rather than
  requiring ever-more-aggressive context trimming.
- **Flights/hotels**: started on Amadeus for Developers per the original spec, but Amadeus
  decommissioned its free self-service portal in July 2026 (new signups are enterprise-only now).
  Flights moved to Duffel (instant free test-mode signup). Hotels first moved to Duffel Stays too,
  but that's gated behind a sales contact even on a paid Duffel account — so hotels moved again,
  to LiteAPI, which has a genuinely instant, free, no-approval sandbox key.
- **Hotels, second time**: before LiteAPI, hotels briefly used DuckDuckGo web search (same
  approach as events/visa lookups) to avoid a third API signup. It worked, but DDG's rate-limiting
  made it unreliable in practice (confirmed firsthand — not a hypothetical), so it was worth the
  one more signup once LiteAPI was found.

If Gemini's pricing/limits or any of these providers change again, the same "verify the actual
API empirically before writing code against docs" approach that caught the Duffel Stays gap and
the Gemini model-deprecation issue should be repeated rather than trusting documentation alone.

### 8.4 Why itinerary/budget/flight-options are separate SSE events, not just part of the final message

Tool results land mid-turn, often many seconds before the model produces its final conversational
text (which the system prompt explicitly tells it to keep short — the full itinerary is never
re-pasted as chat text). Streaming `itinerary_update`/`budget_update`/`flight_options`/
`hotel_options` as their own events lets the itinerary panel populate live, tool by tool, instead
of the whole UI staying blank until the entire turn finishes.

---

## 9. Known limitations

- **DuckDuckGo rate-limiting**: `search_events` and `get_travel_requirements` can return an error
  under repeated use from the same IP. Handled gracefully (the agent gets an error it can mention
  to the user), but there's no automatic retry/backoff beyond what the library does internally.
- **Sandbox pricing**: Duffel (test mode) and LiteAPI (sandbox key) both return realistic-*shaped*
  but not real bookable prices. Fine for planning, not for actually booking anything.
- **Windows dev-environment port/process quirks**: during development, `uvicorn --reload` and
  `taskkill`/`Stop-Process` occasionally failed to fully release a port (a stale process kept
  answering with old code, or the reload watcher wasn't restarting). If the backend seems to be
  running old code after a restart, verify with a curl `OPTIONS` request (or any endpoint) that
  the actual response matches current code, and if not, fully close the terminal window (not just
  Ctrl+C) rather than trusting a same-window restart.
- **`gemini-3.5-flash-lite` reliability**: see §8.2 — this model needs explicit code-level
  guardrails for anything safety- or cost-relevant; don't assume a new soft instruction added to
  `SYSTEM_PROMPT` alone will reliably change its behavior. Test empirically.
