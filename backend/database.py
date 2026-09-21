import json
import sqlite3
import time
import uuid
from contextlib import contextmanager

from config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT 'New trip',
    itinerary TEXT,
    budget TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,
    tool_calls TEXT,
    tool_call_id TEXT,
    name TEXT,
    created_at REAL NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions (id)
);
"""

# Columns added after the initial release. CREATE TABLE IF NOT EXISTS won't add columns to an
# already-existing table, so new columns go here instead of editing SCHEMA above.
SESSION_COLUMN_MIGRATIONS = {
    "trip_summary": "TEXT",
    "flight_options": "TEXT",
    "hotel_options": "TEXT",
}


@contextmanager
def get_db():
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript(SCHEMA)
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(sessions)")}
        for col, col_type in SESSION_COLUMN_MIGRATIONS.items():
            if col not in existing:
                conn.execute(f"ALTER TABLE sessions ADD COLUMN {col} {col_type}")


def create_session(title: str = "New trip") -> str:
    session_id = str(uuid.uuid4())
    now = time.time()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO sessions (id, title, itinerary, budget, created_at, updated_at) VALUES (?, ?, NULL, NULL, ?, ?)",
            (session_id, title, now, now),
        )
    return session_id


def list_sessions() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_session(session_id: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        data["itinerary"] = json.loads(data["itinerary"]) if data["itinerary"] else None
        data["budget"] = json.loads(data["budget"]) if data["budget"] else None
        data["flight_options"] = json.loads(data["flight_options"]) if data["flight_options"] else None
        data["hotel_options"] = json.loads(data["hotel_options"]) if data["hotel_options"] else None
        return data


def delete_session(session_id: str):
    with get_db() as conn:
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))


def rename_session(session_id: str, title: str):
    with get_db() as conn:
        conn.execute(
            "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
            (title, time.time(), session_id),
        )


def save_itinerary(session_id: str, itinerary: dict):
    with get_db() as conn:
        conn.execute(
            "UPDATE sessions SET itinerary = ?, updated_at = ? WHERE id = ?",
            (json.dumps(itinerary), time.time(), session_id),
        )


def save_budget(session_id: str, budget: dict):
    with get_db() as conn:
        conn.execute(
            "UPDATE sessions SET budget = ?, updated_at = ? WHERE id = ?",
            (json.dumps(budget), time.time(), session_id),
        )


def save_trip_summary(session_id: str, summary: str):
    with get_db() as conn:
        conn.execute("UPDATE sessions SET trip_summary = ? WHERE id = ?", (summary, session_id))


def get_trip_summary(session_id: str) -> str | None:
    with get_db() as conn:
        row = conn.execute("SELECT trip_summary FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return row["trip_summary"] if row else None


def save_flight_options(session_id: str, options: list[dict]):
    with get_db() as conn:
        conn.execute("UPDATE sessions SET flight_options = ? WHERE id = ?", (json.dumps(options), session_id))


def save_hotel_options(session_id: str, options: list[dict]):
    with get_db() as conn:
        conn.execute("UPDATE sessions SET hotel_options = ? WHERE id = ?", (json.dumps(options), session_id))


def add_message(
    session_id: str,
    role: str,
    content: str | None = None,
    tool_calls: list | None = None,
    tool_call_id: str | None = None,
    name: str | None = None,
):
    now = time.time()
    with get_db() as conn:
        conn.execute(
            """INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id, name, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                role,
                content,
                json.dumps(tool_calls) if tool_calls else None,
                tool_call_id,
                name,
                now,
            ),
        )
        conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))


def get_messages(session_id: str) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["tool_calls"] = json.loads(d["tool_calls"]) if d["tool_calls"] else None
            result.append(d)
        return result
