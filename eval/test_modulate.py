"""Run Modulate emotion + Velma behaviour detection on phone-quality test clips.

Usage:  backend/.venv/bin/python eval/test_modulate.py [clip.wav ...]
Reads MODULATE_API_KEY from backend/.env. Writes eval/results/modulate_<clip>.json.
"""
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
KEY = dotenv_values(ROOT / "backend/.env").get("MODULATE_API_KEY") or os.getenv("MODULATE_API_KEY")
BASE = "https://platform.modulate.ai/api"
BEHAVIOURS = [
    "preset:caller_under_duress",
    "preset:personal_vulnerability",
    "preset:suicidal_and_self_injurious_ideation",
    "preset:child_safety_violation",
    "preset:direct_threat_physical",
    "preset:conflict_escalation",
]
OUT = ROOT / "eval/results"


def call(client, endpoint, path, extra=None):
    with open(path, "rb") as f:
        r = client.post(f"{BASE}/{endpoint}", headers={"X-API-Key": KEY},
                        files={"upload_file": (path.name, f, "audio/wav")}, data=extra or {})
    try:
        body = r.json()
    except ValueError:
        body = {"raw": r.text[:2000]}
    return r.status_code, body


def main():
    if not KEY:
        sys.exit("MODULATE_API_KEY missing")
    clips = [Path(p) for p in sys.argv[1:]] or sorted((ROOT / "eval/clips/phone").glob("clip*_phone.wav"))
    OUT.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=180) as client:
        for clip in clips:
            emo_status, emo = call(client, "velma-2-emotion-batch", clip)
            vel_status, vel = call(client, "velma-2-batch", clip, {"config": json.dumps({"behaviors": BEHAVIOURS})})
            result = {"clip": clip.name, "emotion_status": emo_status, "emotion": emo,
                      "velma_status": vel_status, "velma": vel}
            (OUT / f"modulate_{clip.stem}.json").write_text(json.dumps(result, indent=2))
            print(f"{clip.name}: emotion HTTP {emo_status}, velma HTTP {vel_status}")


if __name__ == "__main__":
    main()
