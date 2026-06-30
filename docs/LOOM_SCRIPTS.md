# Loom scripts (drafts — make them yours)

These are scaffolds, not lines to read. Talk like you're explaining it to a coworker. Pauses and
"ums" are fine — natural beats real. Both should land under 5 minutes. Have the repo + a transcript
or two open to show on screen.

---

## LOOM 1 — Approach & what I built (≤5 min)

**[0:00 — who I am, why it matters] (~30s)**
"Hi, I'm Ruth. Quick bit of context that shaped how I did this: I work as an event coordinator at
a banquet hall, so I'm on the phones all day — scheduling, verifying who I'm talking to, and
handling the weird calls: people with the wrong number, people asking for things I can't give them,
people who won't take no for an answer. So when I built a bot to *test* a medical front-desk agent,
I tested it like someone who actually works a front desk."

**[0:30 — what I built] (~45s)**
"I built a Python voice bot that calls Pretty Good AI's test line, plays a realistic patient, has a
real spoken conversation, records and transcribes both sides, and then I mine those for bugs.
Stack is Twilio for the call and OpenAI's Realtime API as the patient's brain. I went with Realtime
speech-to-speech over a stitched-together speech-to-text / LLM / text-to-speech setup on purpose —
latency is what makes the conversation sound lucid, and that's their #1 pass/fail bar. I've used
ElevenLabs before and it sounds a bit more human, but I'd have traded away latency for it, so I
chose lucidity."

**[1:15 — how I approached testing: the real differentiator] (~60s)**
"The part I'm proudest of is how I chose what to test. I didn't just run the obvious
schedule/cancel/refill scripts. I pulled scenarios from real medical-receptionist accounts and from
my own front-desk experience, and I aimed them at where a medical agent could actually *hurt*
someone or embarrass the practice — safety, scope, and privacy — not punctuation nitpicks.
And I tested like a little science experiment: change one variable, watch what happens, isolate the
cause."

**[2:15 — show a good call] (~30s)**
"Here's a normal booking call so you can hear it's lucid and natural — [play ~15s of a cedar
simple_booking call]. It books the appointment, confirms it back, stays in character as the
patient the whole time."

**[2:45 — the headline bugs] (~75s)**
"Now the interesting part — what broke. [pull up BUG_REPORT.md]
- It booked a CT scan for a patient who said she was pregnant — no radiation caution, no flag.
- It dropped an emergency caller while verifying their identity, *before* they could even say they
  had post-op leg pain.
- It told a gout patient 'joint pain is orthopedic, you're in the right place' and booked him —
  when that's really primary care or rheumatology.
- And it kept interrupting callers mid-answer and re-asking for the name and birthday they'd
  *just* given — a turn-taking failure.
I led with those because they're clearly the *agent's* behavior. The dead-end transfer everyone
finds, I bundled separately and flagged that it's probably the test line's stub, not a real bug —
because I'd rather be precise than pad the list."

**[4:00 — the experiment that shows how I think] (~40s)**
"One example of the experiment mindset: the agent kept greeting me as 'Alex,' a name I never gave.
Instead of just logging 'it hallucinates names,' I bought a second phone number, called from it,
and the 'Alex' greeting disappeared. So it wasn't random — it was a stale record stuck to my
original number. That's the kind of thing I wanted to get *right*, not just report."

**[4:40 — close] (~20s)**
"I also hit and fixed a few real bugs in my own code along the way, which I'll show in the second
video. Thanks for watching — this was genuinely fun to build."

---

## LOOM 2 — Debugging with AI (≤5 min)

> Pick ONE bug and show the real back-and-forth. I've scripted the **scenario-parameter bug**
> because it has a clean detective arc. (The beta→GA migration bug works too if you'd rather.)
> Have your editor + the AI chat open and actually run the steps on screen.

**[0:00 — the symptom] (~40s)**
"Here's a real bug I hit and how I used AI to chase it down. I'd built a bunch of different patient
scenarios, but I noticed something weird: no matter which scenario I ran — pregnancy, refill,
whatever — every saved transcript was named `simple_booking`. [show the transcripts folder, all
`simple_booking`]. So my scenarios weren't actually running. Let me show how I debugged it."

**[0:40 — first prompt: hand it the symptom + the right files] (~60s)**
"First thing I did — I didn't just say 'fix it.' I gave the AI the symptom and the two files that
matter. [type into the AI:]
*'When I run `make_call --scenario pregnancy_imaging`, the call still behaves like simple_booking
and the transcript saves as simple_booking. Here's make_call.py and main.py. The scenario is passed
as a URL query param on the media-stream websocket. Why might it not be arriving?'*
I gave it the actual code and a specific, observable symptom — that's what gets a useful answer
instead of a guess."

**[1:40 — the AI's diagnosis] (~50s)**
"And it caught it: Twilio **strips query parameters off the `<Stream>` URL**, so my
`?scenario=...` never reached the server, and the code fell back to the default — `simple_booking`.
That explained the whole thing. [show the relevant line where it defaults]."

**[2:30 — second prompt: ask for the fix, then understand it] (~50s)**
"Then I asked how to actually pass it: *'How do I send the scenario to the media stream without a
query param?'* It walked me through using a `<Parameter>` element inside the `<Stream>`, which
arrives in the websocket's 'start' event as `customParameters`. I had it explain *why* that works
so I wasn't just pasting blindly. [show the TwiML change + reading it from the start event]."

**[3:20 — apply + verify] (~60s)**
"Here's the part that matters — I didn't trust it until I tested it. [make the change, restart the
server, run `make_call --scenario pregnancy_imaging`]. And now [show the server log] it prints
`scenario=pregnancy_imaging`, and [show transcripts] the new file is named `pregnancy_imaging`, not
`simple_booking`. Fixed and confirmed."

**[4:20 — how I work with AI] (~30s)**
"My takeaway on using AI for this: give it the real error and the relevant code, make it explain
its reasoning, and *always* verify by re-running — a couple of times it flagged things that turned
out to be quirks of the test line, not real bugs, and I only caught that by checking. Thanks for
watching."

---

## Delivery tips
- Don't memorize — glance at the beat, then say it your way.
- Screen-share the repo, a transcript, and (Loom 2) the AI chat. Showing > telling.
- It's fine to do 2–3 takes. First one shakes out the nerves.
- Watch the clock: both are capped at 5 min. If you run long, cut the demo clip, not the thinking.
