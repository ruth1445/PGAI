"""
Downloads all Twilio call recordings as .mp3 into ./recordings/.
The challenge requires audio in mp3 or ogg format — Twilio serves mp3 directly.

Run:  python -m src.fetch_recordings
"""
from pathlib import Path
import requests
from twilio.rest import Client

from . import config

REC_DIR = Path(__file__).resolve().parent.parent / "recordings"
REC_DIR.mkdir(exist_ok=True)


def fetch_all():
    config.require("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN")
    client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)

    recordings = client.recordings.list(limit=50)
    if not recordings:
        print("No recordings found yet.")
        return

    for rec in recordings:
        mp3_url = f"https://api.twilio.com{rec.uri.replace('.json', '.mp3')}"
        out = REC_DIR / f"call-{rec.date_created:%Y%m%d-%H%M%S}-{rec.sid}.mp3"
        if out.exists():
            continue
        audio = requests.get(mp3_url, auth=(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN))
        audio.raise_for_status()
        out.write_bytes(audio.content)
        print(f"Saved {out.name} ({len(audio.content) // 1024} KB)")

    print(f"\nDone. Recordings in {REC_DIR}")


if __name__ == "__main__":
    fetch_all()
