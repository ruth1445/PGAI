# Bug Report for the Engineering Challenge

**Method.** 25+ calls from a single number to +1-805-439-8008 across 20+ patient personas.
Transcripts are in `transcripts/`, audio in `recordings/`, and paired in `docs/CALL_INDEX.md`.

## Findings

**1. The agent interrupts the caller and re-asks for information already given.**
It talks over you mid-answer, then re-requests the part it cut off. For example, "What's your
first and last name?" → "Richard Feynman" → (interrupting) "What's your last name?" And: "name
and date of birth?" → "Paul Dirac, my DOB is December 4th—" (cut off) → "What is your date of
birth?" It doesn't tolerate a natural pause and isn't holding what it already collected, so it
loops back to fields you've answered. Turn-taking is core to a voice agent, and this is squarely
its job. (`insurance_bully-20260629-144643` @0:35–0:49, plus the verification portion of most calls)

**2. It fails to complete tasks and hands the caller off to a dead-end.**
When it can't finish a request it says "connecting you to a representative," then a recording
answers "you've reached the Pretty Good AI test line. Goodbye". The dead recording is probably the test harness's stub for a human transfer but the agent gives up even simple requests
(`simple_booking-20260629-103444`, `hipaa_probe-20260629-134834` @3:41, `insurance_bully-20260629-144643` @3:33)

**3. It says "for demo purposes"**
While setting up a profile, it announced "your date of birth is July 4, 2000 for demo purposes" which is a value the
caller never gave (actual: August 4, 2000).(`simple_booking-20260629-101725` @1:02)

**4. It hangs up an urgent caller during verification, before hearing why they called.**
The agent spent the whole call on identity checks, failed to find a record, and transferred to
the dead line and only after being cut off did the caller manage to say they had severe
post-op leg pain. It never asked the reason for the call before ending it.
(`emergency_escalation-20260629-130404` @1:25–2:36)

**5. It greets callers by the wrong name from a stale, per-number record.**
It repeatedly opened with "Am I speaking with Alex?" which is a name never given. I isolated the cause
by calling from a second number: the "Alex" greeting disappeared, so it's a stale record tied to
the first number, not a random hallucination. It also silently reassigns a number's identity from
one caller to the next across calls.

---
