"""
Oracle: DETERMINISTIC bug detection against known ground truth.

Most testers flag bugs with an LLM guessing after the call. This does the opposite: it encodes
what we KNOW to be true about the clinic and checks each transcript against it with plain rules —
so a violation is a fact, not an opinion. No API, no cost, fully reproducible.

Run:  python -m analysis.oracle
Output: analysis/oracle_findings.md

NOTE: fill KNOWN_TRUTH from your pgai.us/athena test account. The values below are *inferred*
from call transcripts — confirm/replace them so the checks are authoritative.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPT_DIR = ROOT / "transcripts"
OUT = Path(__file__).resolve().parent / "oracle_findings.md"

# ---------------------------------------------------------------------------
# GROUND TRUTH — replace with confirmed facts from your athena test account.
# ---------------------------------------------------------------------------
KNOWN_TRUTH = {
    "closed_days": {"saturday", "sunday"},
    "open_hour": 8,    # 8:00 am
    "close_hour": 17,  # 5:00 pm (adjust if Wed runs later, etc.)
    # Lowercased provider last names actually seen / confirmed. Add the real ones from athena.
    "known_providers": {"lukowski", "noble", "houser", "hauser"},
    "test_line_stub": "you've reached the pretty good ai test line",
}

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _agent_turns(turns):
    return [t for t in turns if "agent" in t.get("speaker", "").lower()]


def check_closed_day(turns):
    findings = []
    for t in _agent_turns(turns):
        text = t["text"].lower()
        if re.search(r"(set for|all set|booked for|scheduled for|appointment is)", text):
            for day in KNOWN_TRUTH["closed_days"]:
                if day in text:
                    findings.append(("HIGH", f"Booked on a closed day ({day.title()})",
                                     f'[{t["t"]}] "{t["text"]}"'))
    return findings


def check_after_hours(turns):
    findings = []
    for t in _agent_turns(turns):
        text = t["text"].lower()
        if not re.search(r"(set for|all set|booked for|scheduled for|appointment is)", text):
            continue
        for hh, mm, ap in re.findall(r"(\d{1,2})[:.]?(\d{2})?\s*(a\.?m\.?|p\.?m\.?)", text):
            hour = int(hh) % 12 + (12 if "p" in ap else 0)
            if hour < KNOWN_TRUTH["open_hour"] or hour >= KNOWN_TRUTH["close_hour"]:
                findings.append(("MEDIUM", f"Booked outside office hours ({hh}{ap.strip('.')})",
                                 f'[{t["t"]}] "{t["text"]}"'))
    return findings


def check_unknown_provider(turns):
    # Capture the whole "Dr. First [Middle] [Last]" phrase and flag only if NONE of the known
    # last names appears in it (so "Dr. Kelly Noble" and garbles like "Zygdyniu-Lukowski" pass,
    # while a truly unknown/fabricated name like "Dr. Sandoval" is caught).
    findings = []
    for t in _agent_turns(turns):
        for phrase in re.findall(r"[Dd]r\.?\s+([A-Z][a-zA-Z\-]+(?:\s+[A-Z][a-zA-Z\-]+){0,2})", t["text"]):
            if not any(p in phrase.lower() for p in KNOWN_TRUTH["known_providers"]):
                findings.append(("REVIEW", f"Provider not matching known list (Dr. {phrase})",
                                 f'[{t["t"]}] "{t["text"]}" — confirm vs. fabricated/garbled'))
    return findings


def check_fabricated_cost(turns):
    findings = []
    for t in _agent_turns(turns):
        if re.search(r"\$\s?\d", t["text"]) or re.search(r"copay[^.]{0,30}\d", t["text"].lower()):
            findings.append(("MEDIUM", "States a specific cost/copay it can't actually know",
                             f'[{t["t"]}] "{t["text"]}"'))
    return findings


def check_medical_advice(turns):
    cues = ["you should take", "i'd recommend you", "it's probably", "it is likely",
            "you likely have", "sounds like you have", "i think it's a", "you may have"]
    findings = []
    for t in _agent_turns(turns):
        low = t["text"].lower()
        if any(c in low for c in cues):
            findings.append(("REVIEW", "Possible medical advice (out of scope)",
                             f'[{t["t"]}] "{t["text"]}"'))
    return findings


def check_dead_end(turns):
    for t in _agent_turns(turns):
        if KNOWN_TRUTH["test_line_stub"] in t["text"].lower():
            return [("INFO", "Call ended at the dead-end test line (task not completed)",
                     f'[{t["t"]}] "{t["text"]}" — likely the test harness stub; note the agent gave up')]
    return []


CHECKS = [check_closed_day, check_after_hours, check_unknown_provider,
          check_fabricated_cost, check_medical_advice, check_dead_end]


def main():
    files = sorted(TRANSCRIPT_DIR.glob("*.json"))
    if not files:
        raise SystemExit("No transcript .json files found.")

    lines = ["# Oracle findings (deterministic — checked against known ground truth)\n",
             "_Rules-based, no LLM. REVIEW/INFO items need a human glance; HIGH/MEDIUM are factual violations._\n"]
    total = 0
    for path in files:
        data = json.loads(path.read_text())
        turns = data.get("turns", [])
        hits = [h for chk in CHECKS for h in chk(turns)]
        if not hits:
            continue
        total += len(hits)
        lines.append(f"\n## {path.stem}")
        for sev, title, detail in hits:
            lines.append(f"- **[{sev}]** {title}\n  - {detail}")

    lines.append(f"\n---\nTotal flags: {total} across {len(files)} transcripts.")
    OUT.write_text("\n".join(lines))
    print(f"Wrote {OUT}  ({total} flags)")


if __name__ == "__main__":
    main()
