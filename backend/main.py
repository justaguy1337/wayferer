from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database
from config import settings
from routers import chat, trips

app = FastAPI(title="AI Travel Planner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    database.init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(chat.router)
app.include_router(trips.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
