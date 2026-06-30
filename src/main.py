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
from .scenarios import full_instructions, get_scenario

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
    ws_url = f"wss://{config.PUBLIC_HOSTNAME}/media-stream"
    # Pass the scenario as a <Parameter> (NOT a URL query param — Twilio strips those
    # off the Stream URL). It arrives in the websocket "start" event's customParameters.
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="{ws_url}">
      <Parameter name="scenario" value="{scenario}" />
    </Stream>
  </Connect>
</Response>"""
    return HTMLResponse(content=twiml, media_type="application/xml")


@app.websocket("/media-stream")
async def media_stream(twilio_ws: WebSocket):
    """Bidirectional bridge between Twilio and OpenAI Realtime."""
    await twilio_ws.accept()

    transcript: list[dict] = []
    call_start = time.time()
    stream_sid = {"value": None}

    # The scenario is delivered as a <Parameter>, which Twilio sends inside the "start"
    # event (customParameters) — NOT as a URL query param. Read it before configuring OpenAI.
    scenario = "simple_booking"
    async for message in twilio_ws.iter_text():
        data = json.loads(message)
        if data.get("event") == "start":
            stream_sid["value"] = data["start"]["streamSid"]
            scenario = data["start"].get("customParameters", {}).get("scenario", scenario)
            break

    instructions = full_instructions(scenario)
    voice = get_scenario(scenario).get("voice") or config.REALTIME_VOICE
    print(f"Call started: scenario={scenario}, voice={voice}")

    # Track when each side STARTED speaking, so the transcript is ordered by speech
    # time rather than by when transcription happens to finish (Whisper lags on the
    # agent side, which otherwise prints answers above their questions).
    timing = {"agent_start": 0.0, "bot_start": None}

    def log_line(speaker: str, text: str, when: float):
        if text and text.strip():
            transcript.append({"sec": max(when - call_start, 0.0),
                               "speaker": speaker, "text": text.strip()})

    url = f"wss://api.openai.com/v1/realtime?model={config.REALTIME_MODEL}"
    headers = {
        "Authorization": f"Bearer {config.OPENAI_API_KEY}",
    }

    async with websockets.connect(url, additional_headers=headers) as openai_ws:
        # Configure the session (Realtime API GA shape). Audio is G.711 u-law 8kHz
        # (what Twilio sends), written as {"type": "audio/pcmu"}. Server-side VAD gives
        # natural turn-taking; transcription logs what we HEAR (the PGAI agent).
        await openai_ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "type": "realtime",
                "output_modalities": ["audio"],
                "instructions": instructions,
                "audio": {
                    "input": {
                        "format": {"type": "audio/pcmu"},
                        "turn_detection": {"type": "server_vad"},
                        "transcription": {"model": "whisper-1"},
                    },
                    "output": {
                        "format": {"type": "audio/pcmu"},
                        "voice": voice,
                    },
                },
            },
        }))

        async def twilio_to_openai():
            """Caller (PGAI agent) audio -> OpenAI."""
            try:
                async for message in twilio_ws.iter_text():
                    data = json.loads(message)
                    event = data.get("event")
                    if event == "media":
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

                    # Our bot's audio -> back to the phone call. (GA event name.)
                    if rtype == "response.output_audio.delta" and stream_sid["value"]:
                        if timing["bot_start"] is None:
                            timing["bot_start"] = time.time()
                        await twilio_ws.send_text(json.dumps({
                            "event": "media",
                            "streamSid": stream_sid["value"],
                            "media": {"payload": response["delta"]},
                        }))

                    # What our bot SAID (the patient). (GA event name.)
                    elif rtype == "response.output_audio_transcript.done":
                        log_line("PATIENT (bot)", response.get("transcript", ""),
                                 timing["bot_start"] or time.time())
                        timing["bot_start"] = None

                    # What our bot HEARD (the PGAI agent).
                    elif rtype == "conversation.item.input_audio_transcription.completed":
                        log_line("PGAI AGENT", response.get("transcript", ""),
                                 timing["agent_start"] or time.time())

                    # Barge-in: caller started talking -> note start time + stop playback.
                    elif rtype == "input_audio_buffer.speech_started":
                        timing["agent_start"] = time.time()
                        if stream_sid["value"]:
                            await twilio_ws.send_text(json.dumps({
                                "event": "clear",
                                "streamSid": stream_sid["value"],
                            }))
            except Exception as e:
                print("openai_to_twilio ended:", e)

        twilio_task = asyncio.create_task(twilio_to_openai())
        openai_task = asyncio.create_task(openai_to_twilio())
        try:
            # Finish as soon as EITHER side ends (e.g. the caller hangs up), then
            # cancel the other — otherwise we hang waiting on the OpenAI socket and
            # never save the transcript.
            _, pending = await asyncio.wait(
                {twilio_task, openai_task}, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
        finally:
            _save_transcript(scenario, transcript)


def _save_transcript(scenario: str, transcript: list[dict]):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = TRANSCRIPT_DIR / f"{scenario}-{ts}"

    # Order by when each side started speaking, then format mm:ss.
    ordered = sorted(transcript, key=lambda x: x.get("sec", 0.0))

    def fmt(sec: float) -> str:
        s = int(sec)
        return f"{s // 60}:{s % 60:02d}"

    turns = [{"t": fmt(l["sec"]), "speaker": l["speaker"], "text": l["text"]} for l in ordered]

    # Human-readable
    with open(f"{base}.txt", "w") as f:
        f.write(f"Scenario: {scenario}\nRecorded: {ts}\n\n")
        for l in turns:
            f.write(f"[{l['t']}] {l['speaker']}: {l['text']}\n")
    # Machine-readable (for analysis/analyze_transcripts.py)
    with open(f"{base}.json", "w") as f:
        json.dump({"scenario": scenario, "recorded": ts, "turns": turns}, f, indent=2)
    print(f"Saved transcript: {base}.txt")
