# Architecture

The bot places an outbound call with Twilio and bridges the live phone audio to the OpenAI
Realtime API (GA), which plays the patient. When the call connects, Twilio fetches TwiML from
`/outbound-twiml`, which opens a **Media Stream** websocket to `/media-stream` and passes the
chosen scenario as a `<Parameter>` (not a URL query param — Twilio strips those off the Stream
URL, a bug that silently made every call run the default scenario until fixed). The handler reads
the scenario from the websocket "start" event, configures the Realtime session with that
persona's instructions and voice, then runs two concurrent loops: one forwards the caller's audio
(the PGAI agent) into the model as `input_audio_buffer.append`, the other forwards the model's
`response.output_audio` back to Twilio. Audio stays in Twilio's native G.711 μ-law
(`{"type":"audio/pcmu"}`) end-to-end, so there's no re-encoding. Server-side VAD handles
turn-taking and a barge-in handler clears playback when the agent starts talking. Each turn is
transcribed (the model's own output plus Whisper on what it hears) and written to a transcript
**ordered by when each side started speaking** — not by when transcription finishes, which
otherwise prints answers above their questions. Calls are recorded dual-channel via Twilio for
the required audio.

**Key design choices.** I chose Twilio + OpenAI Realtime (speech-to-speech) over an
STT→LLM→TTS pipeline (e.g. Deepgram + ElevenLabs) because the lowest latency is what makes the
conversation lucid — the #1 evaluation gate — and it's far less code to keep coherent. The
tradeoff is voice timbre: Realtime voices sound slightly more synthetic than ElevenLabs, but
lucidity matters more here than voice-acting realism. Patient behavior is fully data-driven: each
scenario in `scenarios.py` is a small system prompt with one goal, its own voice and identity,
plus a shared rule block (lucidity, English-only, "describe symptoms like a real patient").
Scenarios were sourced from real medical-receptionist accounts and clinical-safety edge cases, so
they probe the agent's actual failure points. Bug discovery is deliberately decoupled from the
call — an offline pass over the transcripts proposes *candidate* bugs that I curate by hand —
which keeps the live calls realistic (no in-call "that's a bug!" narration) while still scaling
analysis across every call.
