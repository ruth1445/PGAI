"""
Places ONE outbound call to the PGAI test line for a given scenario.

Prereqs (once): server running + ngrok pointing at it, .env filled in.
  Terminal 1:  uvicorn src.main:app --port 8000
  Terminal 2:  ngrok http 8000     (copy the https host into PUBLIC_HOSTNAME in .env)
  Terminal 3:  python -m src.make_call --scenario refill

The call is recorded (dual channel) so you get both sides as audio for the submission.
Download recordings afterward with:  python -m src.fetch_recordings
"""
import argparse
from twilio.rest import Client

from . import config
from .scenarios import SCENARIOS


def make_call(scenario: str):
    config.require("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER",
                   "PUBLIC_HOSTNAME", "OPENAI_API_KEY")
    if scenario not in SCENARIOS:
        raise SystemExit(f"Unknown scenario '{scenario}'. Options: {', '.join(SCENARIOS)}")

    # Safety guardrail: only ever dial the PGAI assessment line.
    if config.TARGET_NUMBER != "+18054398008":
        raise SystemExit(
            f"Refusing to call {config.TARGET_NUMBER}: this bot only calls the PGAI "
            f"test line (+18054398008)."
        )

    client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
    twiml_url = f"https://{config.PUBLIC_HOSTNAME}/outbound-twiml?scenario={scenario}"

    call = client.calls.create(
        to=config.TARGET_NUMBER,
        from_=config.TWILIO_FROM_NUMBER,
        url=twiml_url,
        record=True,                     # record the call
        recording_channels="dual",       # both sides on separate channels
    )
    print(f"Calling {config.TARGET_NUMBER} | scenario='{scenario}' | call SID: {call.sid}")
    print("Listen live in the Twilio console; transcript saves automatically when it ends.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="simple_booking",
                        help=f"One of: {', '.join(SCENARIOS)}")
    args = parser.parse_args()
    make_call(args.scenario)
