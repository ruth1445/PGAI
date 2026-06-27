"""Loads configuration from environment variables (.env)."""
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
TARGET_NUMBER = os.getenv("TARGET_NUMBER", "+18054398008")
PUBLIC_HOSTNAME = os.getenv("PUBLIC_HOSTNAME", "").replace("https://", "").replace("http://", "").rstrip("/")
PORT = int(os.getenv("PORT", "8000"))
REALTIME_VOICE = os.getenv("REALTIME_VOICE", "coral")
REALTIME_MODEL = os.getenv("REALTIME_MODEL", "gpt-realtime-mini")


def require(*names: str) -> None:
    """Fail loudly if a required env var is missing."""
    missing = [n for n in names if not globals().get(n)]
    if missing:
        raise SystemExit(
            f"Missing required env vars: {', '.join(missing)}.\n"
            f"Copy .env.example to .env and fill them in."
        )
