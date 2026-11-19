import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from google.genai import errors

import database
from agent.orchestrator import run_agent_turn
from models import ChatRequest

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    if database.get_session(req.session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        try:
            async for event in run_agent_turn(req.session_id, req.message, force=req.force):
                yield f"data: {json.dumps(event, default=str)}\n\n"
        except Exception as exc:
            message = str(exc)
            if isinstance(exc, errors.ServerError) and exc.code == 503:
                message = "Gemini is temporarily overloaded. Please try sending your message again in a moment."
            yield f"data: {json.dumps({'type': 'error', 'message': message})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
