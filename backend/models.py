from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    message: str
    force: bool = False


class CreateSessionRequest(BaseModel):
    title: str | None = None


class RenameSessionRequest(BaseModel):
    title: str
