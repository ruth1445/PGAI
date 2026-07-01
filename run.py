"""
One-command runner. After setup (deps installed, ngrok authed, .env filled), this:
  1. starts ngrok,
  2. auto-detects the public URL (no copy-paste into .env),
  3. starts the FastAPI server pointed at that URL,
  4. places one call for the chosen scenario,
  5. cleans up the server + tunnel on exit.

Usage:
    python run.py                       # default scenario (simple_booking)
    python run.py urgent_vs_phone       # any scenario name
"""
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request

PORT = os.getenv("PORT", "8000")


def get_ngrok_host(timeout_s: int = 20):
    """Poll ngrok's local API for the https tunnel host (without the scheme)."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen("http://localhost:4040/api/tunnels", timeout=2) as r:
                for t in json.load(r).get("tunnels", []):
                    url = t.get("public_url", "")
                    if url.startswith("https://"):
                        return url.replace("https://", "")
        except Exception:
            pass
        time.sleep(0.5)
    return None


def main():
    scenario = sys.argv[1] if len(sys.argv) > 1 else "simple_booking"
    procs = []
    try:
        print("Starting ngrok ...")
        procs.append(subprocess.Popen(
            ["ngrok", "http", PORT],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ))
        host = get_ngrok_host()
        if not host:
            sys.exit("Could not detect an ngrok https tunnel. Is ngrok installed and authed?")
        print(f"Public URL: https://{host}")

        # The server and the call both read PUBLIC_HOSTNAME from the environment.
        env = {**os.environ, "PUBLIC_HOSTNAME": host}

        print("Starting server ...")
        procs.append(subprocess.Popen(["uvicorn", "src.main:app", "--port", PORT], env=env))
        time.sleep(3)  # give the server a moment to come up

        print(f"Placing call: scenario={scenario}")
        subprocess.run([sys.executable, "-m", "src.make_call", "--scenario", scenario], env=env)

        print("\nCall placed. Leave this running until the call ends "
              "(the transcript saves on hangup), then press Ctrl+C.")
        signal.pause()
    except KeyboardInterrupt:
        print("\nShutting down ...")
    finally:
        for p in procs:
            p.terminate()


if __name__ == "__main__":
    main()
