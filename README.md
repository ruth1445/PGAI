# Pretty Good AI Engineering Challenge

An automated Python voice bot that calls the Pretty Good AI test line, role-plays realistic
orthopedic patients (Pivot Point Orthopaedics), records & transcribes both sides of each call,
and surfaces bugs in the agent's behavior.

See [`docs/BUG_REPORT.md`](docs/BUG_REPORT.md) for findings and [`docs/BUG_PLAYBOOK.md`](docs/BUG_PLAYBOOK.md)
for the full probe set + per-persona map.

## Setup (once)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in Twilio + OpenAI keys (see .env.example)
```
You'll also need [ngrok](https://ngrok.com/download) (free) to expose the local server, and an
OpenAI key with Realtime access.

## Run a call

**One command (after setup):**
```bash
python run.py                  # default scenario (simple_booking)
python run.py urgent_vs_phone  # any scenario
```
`run.py` starts ngrok, auto-detects the public URL, launches the server pointed at it, and places
the call — no copy-pasting the tunnel URL. Leave it running until the call ends (the transcript
saves on hangup), then Ctrl+C.

<details><summary>Or run the steps manually (three terminals)</summary>

```bash
# 1) start the server
uvicorn src.main:app --port 8000

# 2) expose it — put the printed host (e.g. abc123.ngrok-free.dev) into PUBLIC_HOSTNAME in .env,
#    then restart terminal 1 so it picks up the change
ngrok http 8000

# 3) place one call with a chosen scenario
python -m src.make_call --scenario simple_booking
```
</details>

List every scenario name with `python -m src.make_call --scenario list` (it prints the options).
When a call ends, a both-sides, time-ordered transcript saves to `transcripts/`.

## Recordings & analysis
```bash
python -m src.fetch_recordings          # downloads call audio as .mp3 into recordings/
python -m analysis.analyze_transcripts  # auto-flags candidate bugs -> analysis/candidate_bugs.md
```
The analyzer proposes *candidates*; the final [`docs/BUG_REPORT.md`](docs/BUG_REPORT.md) is curated by hand.

```
