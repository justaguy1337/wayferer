import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / "backend.env", override=True)


class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    geoapify_api_key: str = os.getenv("GEOAPIFY_API_KEY", "")
    tomtom_api_key: str = os.getenv("TOMTOM_API_KEY", "")
    openweather_api_key: str = os.getenv("OPENWEATHER_API_KEY", "")

    duffel_api_key: str = os.getenv("DUFFEL_API_KEY", "")
    liteapi_key: str = os.getenv("LITEAPI_KEY", "")

    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    database_path: str = os.getenv("DATABASE_PATH", str(BASE_DIR / "travel_agent.db"))


settings = Settings()
