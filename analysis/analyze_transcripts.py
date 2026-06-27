"""
Automated post-call bug mining (the "idea B, reborn" feature).

Reads every transcript in ./transcripts/*.json and asks an LLM to surface CANDIDATE bugs
in the PGAI agent's behavior, with a timestamp, severity, and one-line rationale.

This does NOT write the final bug report — it produces a shortlist you then curate by hand
(useful, well-described bugs beat a long auto-generated list of nitpicks).

Run:  python -m analysis.analyze_transcripts
Output: analysis/candidate_bugs.md
"""
import json
from pathlib import Path
from openai import OpenAI

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src import config  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPT_DIR = ROOT / "transcripts"
OUT = Path(__file__).resolve().parent / "candidate_bugs.md"

SYSTEM = """You are a QA analyst reviewing a transcript of a test patient calling a medical
scheduling voice agent. Identify likely BUGS or quality issues in the AGENT's behavior only
(not the patient's). Look especially for:
- booking outside office hours / on closed days
- wrong date math (relative dates, "8 days from now", etc.)
- fabricated facts it can't know (copays, providers, policies)
- giving medical advice (out of scope)
- failing to escalate a possible emergency
- claiming an action happened without confirming it
- losing track of corrections / context

For each issue return: a short title, a severity (High/Medium/Low), the timestamp from the
transcript, and one sentence on why it's a problem. If nothing notable, say so. Be strict —
skip punctuation/wording nitpicks."""


def analyze_one(client: OpenAI, path: Path) -> str:
    data = json.loads(path.read_text())
    convo = "\n".join(f"[{t['t']}] {t['speaker']}: {t['text']}" for t in data["turns"])
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Scenario: {data['scenario']}\n\n{convo}"},
        ],
    )
    return resp.choices[0].message.content


def main():
    config.require("OPENAI_API_KEY")
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    files = sorted(TRANSCRIPT_DIR.glob("*.json"))
    if not files:
        raise SystemExit("No transcripts found. Run some calls first.")

    sections = ["# Candidate bugs (auto-generated — curate before submitting)\n"]
    for path in files:
        print(f"Analyzing {path.name} ...")
        sections.append(f"\n## {path.stem}\n\n{analyze_one(client, path)}\n")

    OUT.write_text("\n".join(sections))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
