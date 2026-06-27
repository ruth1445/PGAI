# Architecture

The bot places an outbound call with Twilio and bridges the live phone audio to the OpenAI
Realtime API, which acts as the "patient." When the call connects, Twilio fetches TwiML from
`/outbound-twiml` that opens a **Media Stream** websocket to `/media-stream`. That handler runs
two concurrent loops: one forwards the caller's audio (the PGAI agent) into the Realtime
session as `input_audio_buffer.append`, and the other forwards the model's `response.audio`
back to Twilio. Audio is exchanged in Twilio's native G.711 μ-law format end-to-end, so no
re-encoding is needed. Server-side voice-activity detection handles turn-taking, and a barge-in
handler clears playback when the agent starts talking — together these give the natural pacing
the assessment weighs most heavily. Each turn is transcribed (the model's own output plus
Whisper transcription of what it hears) and written to a timestamped transcript; calls are
recorded dual-channel via Twilio for the required audio artifacts.

**Key design choices.** I chose Twilio + OpenAI Realtime (speech-to-speech) over an
STT→LLM→TTS pipeline because the lowest latency is what makes the conversation sound lucid —
the #1 evaluation gate — and it's far less code to keep coherent. Patient behavior is fully
data-driven: each scenario in `scenarios.py` is a small system prompt with one clear goal and a
shared "speak like a human" rule block, so new test cases are added without touching the audio
plumbing. Bug discovery is deliberately decoupled from the call — an offline pass over the
transcripts proposes *candidate* bugs that I then curate by hand — which keeps the live calls
realistic (no in-call "that's a bug!" narration) while still scaling analysis across every call.
