# PGAI Caller Bot — a patient simulator for testing the Pretty Good AI agent

An automated Python voice bot that calls the Pretty Good AI test line, role-plays realistic
orthopedic patients (Pivot Point Orthopaedics), records & transcribes both sides of each call,
and surfaces bugs in the agent's behavior.

## What makes this one different
- **Personas grounded in the real world** — built from accounts of actual medical receptionists
  plus my own front-desk experience (I'm an event coordinator who schedules and screens calls).
- **Clinically-grounded safety probes** most testers won't think of: pregnancy + radiation
  imaging, emergency-triage handling, diabetes vs. pre-op fasting, plus identity/HIPAA edge cases.
- **Experimentally isolated findings** — e.g., I proved the "wrong caller name" bug was a stale
  per-number record (not a hallucination) by repeating the call from a clean second number.

See [`docs/BUG_REPORT.md`](docs/BUG_REPORT.md) for findings and [`docs/BUG_PLAYBOOK.md`](docs/BUG_PLAYBOOK.md)
for the full probe set + per-persona map.

## Stack
Python · Twilio Programmable Voice (Media Streams) · **OpenAI Realtime API** (GA, speech-to-speech)
· FastAPI · ngrok. The live phone audio (G.711 μ-law) streams straight into the Realtime model
acting as the patient, and its speech streams back to the call. I chose Realtime over an
STT→LLM→TTS (e.g. ElevenLabs) pipeline because the lowest latency is what keeps the conversation
lucid — the #1 evaluation gate. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Setup (once)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in Twilio + OpenAI keys (see .env.example)
```
You'll also need [ngrok](https://ngrok.com/download) (free) to expose the local server, and an
OpenAI key with Realtime access.

## Run a call
Three terminals after setup:
```bash
# 1) start the server
uvicorn src.main:app --port 8000

# 2) expose it — put the printed host (e.g. abc123.ngrok-free.dev) into PUBLIC_HOSTNAME in .env,
#    then restart terminal 1 so it picks up the change
ngrok http 8000

# 3) place one call with a chosen scenario
python -m src.make_call --scenario simple_booking
```
List every scenario name with `python -m src.make_call --scenario list` (it prints the options).
When a call ends, a both-sides, time-ordered transcript saves to `transcripts/`.

## Recordings & analysis
```bash
python -m src.fetch_recordings          # downloads call audio as .mp3 into recordings/
python -m analysis.analyze_transcripts  # auto-flags candidate bugs -> analysis/candidate_bugs.md
```
The analyzer proposes *candidates*; the final [`docs/BUG_REPORT.md`](docs/BUG_REPORT.md) is curated by hand.

## Scenarios
21 patient personas live in [`src/scenarios.py`](src/scenarios.py). Each sets its own **goal**,
**voice**, and **identity** (name/DOB/phone). Shared rules enforce lucidity, an English-only lock,
and "describe symptoms like a real patient." Booking-completion personas inherit the one
registered test-patient identity so the agent can look them up; others call in as new patients.

## Layout
```
src/main.py              FastAPI server: Twilio <-> OpenAI Realtime bridge, transcript logging
src/make_call.py         places one recorded outbound call for a scenario
src/fetch_recordings.py  downloads call audio as mp3
src/scenarios.py         21 patient personas (goal + voice + identity)
src/config.py            env/config loading
analysis/                automated post-call bug mining
docs/                    ARCHITECTURE, BUG_REPORT, BUG_PLAYBOOK, BUG_IDEAS, COMPETITIVE_NOTES
recordings/ transcripts/ submission artifacts
```

> Safety: the bot only ever dials `TARGET_NUMBER` (+1-805-439-8008); any other number is rejected
> before contacting Twilio. Secrets live in `.env` (git-ignored) — see `.env.example`.
