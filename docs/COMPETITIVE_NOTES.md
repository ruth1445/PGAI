# Competitive notes — how to stand out

Reviewed ~13 public submissions (READMEs + one full bug report). Purpose: NOT to copy —
to see what's table stakes vs. what differentiates, so our submission stands out.

## What everyone is doing (table stakes — won't differentiate us)
- Stack: Twilio + FastAPI + ngrok, with either OpenAI Realtime OR (Deepgram STT + GPT/Claude/Gemini + ElevenLabs/Cartesia TTS). One uses LiveKit+Telnyx.
- 10–18 patient scenarios; an LLM post-call bug analyzer; ARCHITECTURE.md; BUG_REPORT.md.
- Near-identical READMEs and scenario lists (scheduling, reschedule, cancel, refill,
  insurance, hours, urgent symptoms, confused elderly, Spanish/non-native, interruption, HIPAA).

## The COMMON bugs everyone is finding (so these are table stakes too)
Evidenced across competitor reports + our own first call:
1. **Dead-end transfer** — "Connecting you... Hello, you've reached the Pretty Good AI test
   line. Goodbye." Then hangs up. Reported as systemic (one tester: 10/12 calls). *We hit this
   in call #1 too.*
2. **Caller misidentification** — agent assumes a name ("Am I speaking with Sarah?" / "Alex?").
   *We hit "Alex" in call #1.*
3. **"I can't proceed further" / error loops** ("Something's not right" x3, no recovery).
4. **DOB/verification demanded for public info** (e.g. office hours).
5. **Name mis-transcription / fabrication** ("David Anderson" → "David Anne Anderson").
6. **Fabricated demo data** (invents a DOB "for demo purposes").
7. **Sentence repetition mid-response; cut-off instructions.**

> Implication: if our bug report leads with these, we look identical to the field. Acknowledge
> them briefly as "known/systemic," then go deeper.

## How WE stand out (our edge — lean in)
1. **Real-receptionist-sourced scenarios.** Nobody else grounded tests in actual medical
   front-desk accounts. Our urgent-vs-phone (triage liability), insurance-bully, new-patient-
   relative (HIPAA), provider-specific rules, religious accommodation, what-to-bring are novel angles.
2. **Domain credibility.** Ruth does this job (event coordinator who schedules + answers phones).
   The Loom can explain WHY each bug matters operationally — credibility no one else has.
3. **Bug report framing.** Organize by PATIENT-IMPACT severity; explicitly separate
   "known/systemic" from "novel findings"; each bug: timestamp + audio clip + why it matters +
   expected behavior. Meta-awareness (knowing what's common) itself signals rigor.
4. **The little things that differ from the samey crowd:**
   - README opens with the real-receptionist sourcing + tester background, not boilerplate.
   - Correctly name the clinic (Pivot Point Orthopaedics) + ortho-tailored scenarios.
   - Tight, honest iteration story in Loom 2 (our real beta→GA + transcript-hang fixes).
   - A short "if I ran this product, here's the #1 fix" operational take.
5. **Win on bug QUALITY + narrative, not stack or breadth.** 3–4 deep, high-severity bugs
   (safety: urgent-vs-phone triage, emergency escalation, HIPAA leak) beat a long shallow list.

## Don't
- Don't chase heavier engineering (LiveKit/Telnyx/test-harnesses) — not where we win; burns time.
- Don't lead with the common bugs.
- Don't keep researching — the picture is saturated. Finish OUR calls.
