from fastapi import APIRouter, HTTPException

import database
from models import CreateSessionRequest, RenameSessionRequest

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("")
def list_sessions():
    return database.list_sessions()


@router.post("")
def create_session(req: CreateSessionRequest):
    session_id = database.create_session(req.title or "New trip")
    return database.get_session(session_id)


@router.get("/{session_id}")
def get_session(session_id: str):
    session = database.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    session["messages"] = [
        m for m in database.get_messages(session_id) if m["role"] in ("user", "assistant") and m["content"]
    ]
    return session


@router.patch("/{session_id}")
def rename_session(session_id: str, req: RenameSessionRequest):
    if database.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    database.rename_session(session_id, req.title)
    return database.get_session(session_id)


@router.delete("/{session_id}")
def delete_session(session_id: str):
    if database.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    database.delete_session(session_id)
    return {"ok": True}
