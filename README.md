# PGAI Caller Bot

An automated voice bot that calls the Pretty Good AI test line, role-plays realistic
patients, records & transcribes the calls, and helps surface bugs in the agent.

**Stack:** Python · Twilio Programmable Voice (Media Streams) · OpenAI Realtime API · FastAPI
The bot streams the live phone audio into the OpenAI Realtime API (a low-latency
speech-to-speech model) acting as the "patient," and streams its replies back to the call.

---

## Setup (once)

1. **Install dependencies**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure secrets** — copy the example and fill in your keys:
   ```bash
   cp .env.example .env
   ```
   You need a Twilio account (with a phone number) and an OpenAI key with Realtime access.

3. **Install [ngrok](https://ngrok.com/download)** (free) to expose your local server.

## Run a call

Three terminals (after setup):

```bash
# 1. start the server
uvicorn src.main:app --port 8000

# 2. expose it; copy the https host (e.g. abc123.ngrok-free.app) into PUBLIC_HOSTNAME in .env
ngrok http 8000

# 3. place a call with a chosen scenario
python -m src.make_call --scenario refill
```

Listen live in the [Twilio console](https://console.twilio.com). When the call ends, a
transcript (both sides, timestamped) is saved to `transcripts/`.

## Get the recordings & analyze

```bash
python -m src.fetch_recordings          # downloads call audio as .mp3 into recordings/
python -m analysis.analyze_transcripts  # auto-flags candidate bugs -> analysis/candidate_bugs.md
```

## Scenarios

Personas live in [`src/scenarios.py`](src/scenarios.py) — each is a patient with one clear
goal, designed to probe a specific failure mode (date math, office hours, scope, escalation,
etc.). Add your own and call it by name. See [`docs/BUG_IDEAS.md`](docs/BUG_IDEAS.md) for the
testing taxonomy behind them.

## Layout

```
src/main.py              FastAPI server: Twilio <-> OpenAI Realtime bridge + transcript logging
src/make_call.py         places one outbound call for a scenario (recorded)
src/fetch_recordings.py  downloads call audio as mp3
src/scenarios.py         patient personas / test scenarios
analysis/                automated post-call bug mining
docs/                    architecture notes + bug-hunting taxonomy
recordings/ transcripts/ submission artifacts
```

> Only ever calls the assessment line (`TARGET_NUMBER`, default +1-805-439-8008). Secrets stay
> in `.env` (git-ignored); see `.env.example` for the required variables.
