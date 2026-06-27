"""
FastAPI server that bridges a Twilio phone call <-> the OpenAI Realtime API.

Flow:
  make_call.py  -> tells Twilio to dial the PGAI test line
  Twilio answers -> hits /outbound-twiml, which returns TwiML telling Twilio to open a
                    Media Stream websocket back to /media-stream
  /media-stream -> pipes caller audio to OpenAI Realtime (our "patient" brain) and pipes
                   the model's audio back to Twilio, while logging both sides to a transcript.

Run:  uvicorn src.main:app --port 8000   (expose with: ngrok http 8000)
"""
import asyncio
import base64
import json
import time
from datetime import datetime
from pathlib import Path

import websockets
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from . import config
from .scenarios import full_instructions

app = FastAPI()

TRANSCRIPT_DIR = Path(__file__).resolve().parent.parent / "transcripts"
TRANSCRIPT_DIR.mkdir(exist_ok=True)

# OpenAI Realtime event types we relay/log.
LOG_EVENT_TYPES = {"error", "response.done", "session.updated"}


@app.get("/", response_class=PlainTextResponse)
async def health():
    return "PGAI caller bot is running."


@app.api_route("/outbound-twiml", methods=["GET", "POST"])
async def outbound_twiml(request: Request):
    """Returned to Twilio when the call connects. Opens the media stream."""
    scenario = request.query_params.get("scenario", "simple_booking")
    ws_url = f"wss://{config.PUBLIC_HOSTNAME}/media-stream?scenario={scenario}"
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="{ws_url}" />
  </Connect>
</Response>"""
    return HTMLResponse(content=twiml, media_type="application/xml")


@app.websocket("/media-stream")
async def media_stream(twilio_ws: WebSocket):
    """Bidirectional bridge between Twilio and OpenAI Realtime."""
    await twilio_ws.accept()
    scenario = twilio_ws.query_params.get("scenario", "simple_booking")
    instructions = full_instructions(scenario)

    transcript: list[dict] = []
    call_start = time.time()
    stream_sid = {"value": None}

    def stamp() -> str:
        elapsed = int(time.time() - call_start)
        return f"{elapsed // 60}:{elapsed % 60:02d}"

    def log_line(speaker: str, text: str):
        if text and text.strip():
            transcript.append({"t": stamp(), "speaker": speaker, "text": text.strip()})

    url = f"wss://api.openai.com/v1/realtime?model={config.REALTIME_MODEL}"
    headers = {
        "Authorization": f"Bearer {config.OPENAI_API_KEY}",
        "OpenAI-Beta": "realtime=v1",
    }

    async with websockets.connect(url, additional_headers=headers) as openai_ws:
        # Configure the session: audio format Twilio uses (g711 u-law 8kHz),
        # server-side voice activity detection for natural turn-taking, and
        # transcription of what we HEAR (= the PGAI agent's speech).
        await openai_ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "turn_detection": {"type": "server_vad"},
                "input_audio_format": "g711_ulaw",
                "output_audio_format": "g711_ulaw",
                "voice": config.REALTIME_VOICE,
                "instructions": instructions,
                "modalities": ["text", "audio"],
                "input_audio_transcription": {"model": "whisper-1"},
            },
        }))

        async def twilio_to_openai():
            """Caller (PGAI agent) audio -> OpenAI."""
            try:
                async for message in twilio_ws.iter_text():
                    data = json.loads(message)
                    event = data.get("event")
                    if event == "start":
                        stream_sid["value"] = data["start"]["streamSid"]
                    elif event == "media":
                        await openai_ws.send(json.dumps({
                            "type": "input_audio_buffer.append",
                            "audio": data["media"]["payload"],
                        }))
                    elif event == "stop":
                        break
            except Exception as e:
                print("twilio_to_openai ended:", e)

        async def openai_to_twilio():
            """OpenAI (our patient) audio -> Twilio, plus transcript logging."""
            try:
                async for raw in openai_ws:
                    response = json.loads(raw)
                    rtype = response.get("type")

                    if rtype in LOG_EVENT_TYPES:
                        print("openai:", rtype, response.get("error", ""))

                    # Our bot's audio -> back to the phone call.
                    if rtype == "response.audio.delta" and stream_sid["value"]:
                        await twilio_ws.send_text(json.dumps({
                            "event": "media",
                            "streamSid": stream_sid["value"],
                            "media": {"payload": response["delta"]},
                        }))

                    # What our bot SAID (the patient).
                    elif rtype == "response.audio_transcript.done":
                        log_line("PATIENT (bot)", response.get("transcript", ""))

                    # What our bot HEARD (the PGAI agent).
                    elif rtype == "conversation.item.input_audio_transcription.completed":
                        log_line("PGAI AGENT", response.get("transcript", ""))

                    # Barge-in: caller started talking -> stop our playback.
                    elif rtype == "input_audio_buffer.speech_started" and stream_sid["value"]:
                        await twilio_ws.send_text(json.dumps({
                            "event": "clear",
                            "streamSid": stream_sid["value"],
                        }))
            except Exception as e:
                print("openai_to_twilio ended:", e)

        await asyncio.gather(twilio_to_openai(), openai_to_twilio())

    _save_transcript(scenario, transcript)


def _save_transcript(scenario: str, transcript: list[dict]):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = TRANSCRIPT_DIR / f"{scenario}-{ts}"
    # Human-readable
    with open(f"{base}.txt", "w") as f:
        f.write(f"Scenario: {scenario}\nRecorded: {ts}\n\n")
        for line in transcript:
            f.write(f"[{line['t']}] {line['speaker']}: {line['text']}\n")
    # Machine-readable (for analysis/analyze_transcripts.py)
    with open(f"{base}.json", "w") as f:
        json.dump({"scenario": scenario, "recorded": ts, "turns": transcript}, f, indent=2)
    print(f"Saved transcript: {base}.txt")
