# Bug Report — Pivot Point Orthopaedics voice agent

**Tester's note.** I'm an event coordinator at a busy banquet hall — I answer phones, schedule,
verify callers, and field the same kinds of edge calls a front desk gets. I built my patient
personas from that experience plus accounts from real medical receptionists, and aimed them at
the agent's *own* responsibilities — completing tasks, tracking the conversation, getting identity
and coverage right — not surface nitpicks or downstream clinical judgment.

**Method.** ~25 calls from a single number to +1-805-439-8008 across 20+ patient personas.
Transcripts are in `transcripts/`, audio in `recordings/`, and paired in `docs/CALL_INDEX.md`.
Timestamps are from the transcripts; confirm against the matching `.mp3`.

---

## Findings

**1. The agent interrupts the caller and re-asks for information already given.**
It talks over you mid-answer, then re-requests the part it cut off. For example — "What's your
first and last name?" → "Richard Feynman" → (interrupting) "What's your last name?" And: "name
and date of birth?" → "Paul Dirac, my DOB is December 4th—" (cut off) → "What is your date of
birth?" It doesn't tolerate a natural pause and isn't holding what it already collected, so it
loops back to fields you've answered. Turn-taking is core to a voice agent, and this is squarely
its job. (`insurance_bully-20260629-144643` @0:35–0:49, plus the verification portion of most calls)

**2. It fails to complete tasks and hands the caller off to a dead-end.**
When it can't finish a request it says "connecting you to a representative," then a recording
answers "you've reached the Pretty Good AI test line. Goodbye" and hangs up — this happened in
**9 of 26 calls**. The dead recording is probably the test harness's stub for a human transfer;
the real problem is that the agent *gives up and hands off instead of completing simple requests*,
and can't reconcile a caller who disputes what the record says.
(`simple_booking-20260629-103444`, `hipaa_probe-20260629-134834` @3:41, `insurance_bully-20260629-144643` @3:33)

**3. It gives unverified insurance reassurance under pressure.**
A pushy caller insisted his plan was covered. The agent admitted "I don't have a full list of
accepted plans," then said "Blue Ridge Health Plan is commonly accepted" — an unverified
reassurance a patient hears as "yes, you're covered," which is exactly how surprise bills happen.
(`insurance_bully-20260629-144643` @2:55–3:06)

**4. It invents a patient's date of birth instead of asking.**
While setting up a profile, it announced "your date of birth is July 4, 2000" — a value the
caller never gave (actual: August 4, 2000). Rather than recognizing an empty field and asking, it
generated a plausible-sounding identifier and stated it as fact. (`simple_booking-20260629-101725` @1:02)

**5. It hangs up an urgent caller during verification, before hearing why they called.**
The agent spent the whole call on identity checks, failed to find a record, and transferred to
the dead line — and only *after* being cut off did the caller manage to say they had severe
post-op leg pain. It never asked the reason for the call before ending it.
(`emergency_escalation-20260629-130404` @1:25–2:36)

**6. Its identity verification loops.**
While booking, callers were asked their date of birth ~3 times and to spell their name twice,
without the verification ever converging. (`hipaa_probe-20260629-134834` @2:17–3:13)

**7. It greets callers by the wrong name from a stale, per-number record.**
It repeatedly opened with "Am I speaking with Alex?" — a name never given. I isolated the cause
by calling from a second number: the "Alex" greeting disappeared, so it's a stale record tied to
the first number, not a random hallucination. It also silently reassigns a number's identity from
one caller to the next across calls.

**8. It checks for an existing appointment too late.**
It runs the entire intake — symptoms, urgency, provider preference, "let me check availability" —
and only *then* announces you already have an appointment, then can't reconcile it when the caller
disputes it. (`simple_booking-20260629-103444` @1:29)

---

## What it got right
- **Privacy:** asked about a cousin's visit, it required the patient's DOB, then relationship +
  permission, and refused to share anything without authorization. (`hipaa_probe-20260629-134834` @1:21–1:48)
- **Disambiguation:** greeted by the wrong name, it asked "are you calling for yourself or on
  behalf of someone else?"
- **No confabulation on unknowables:** it correctly said it couldn't confirm a made-up provider,
  access X-ray results, or see existing-appointment details. (`hallucination_marathon-20260629-192116`)

## Verify on the audio before final submission
Probably our speech-to-text rather than the agent: clinic name heard as "Hibbitt Point," mangled
provider names, a stray "Bye" mid-call, and "right me" for "right knee."
