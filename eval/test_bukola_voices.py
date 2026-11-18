"""Compare expressive Bukola variants on Ayo's replies (crying + whisper clips), phone format.

Usage: backend/.venv/bin/python eval/test_bukola_voices.py
Uses AYO_ELEVENLABS_API_KEY from backend/.env (Ayo's own key, so Sabi's backup voice quota is untouched).
"""
import json
import time
from pathlib import Path

import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
KEY = dotenv_values(ROOT / "backend/.env").get("AYO_ELEVENLABS_API_KEY")
BUKOLA = "oC2pCZZWEDRe6lmZpaaw"
OUT = ROOT / "eval/results/voices"
rows = {(r["clip"], r["variant"]): r["said"] for r in json.loads((ROOT / "eval/results/ayo_prompt_results.json").read_text())}
LINES = {"clip01": (" ".join(rows[("clip01", "prompt+listener")].split()), "[softly]"),
         "clip02": (" ".join(rows[("clip02", "prompt+listener")].split()), "[whispers]")}
# name, model, use tag?, voice_settings override
VARIANTS = [
    ("v3conv_natural", "eleven_v3_conversational", True, {"stability": 0.5}),
    ("v3conv_creative", "eleven_v3_conversational", True, {"stability": 0.0}),
    ("v4turbo_tags", "eleven_v4_turbo", True, None),
]


def main():
    if not KEY:
        raise SystemExit("Add AYO_ELEVENLABS_API_KEY=... to backend/.env first.")
    OUT.mkdir(parents=True, exist_ok=True)
    for clip, (text, tag) in LINES.items():
        for name, model, use_tag, settings in VARIANTS:
            body = {"text": f"{tag} {text}" if use_tag else text, "model_id": model}
            if settings:
                body["voice_settings"] = settings
            t0, first, audio = time.time(), None, bytearray()
            with httpx.stream("POST", f"https://api.elevenlabs.io/v1/text-to-speech/{BUKOLA}/stream?output_format=ulaw_8000",
                              headers={"xi-api-key": KEY}, json=body, timeout=90) as r:
                if r.status_code != 200:
                    print(clip, name, "HTTP", r.status_code, r.read()[:200]); continue
                for chunk in r.iter_bytes():
                    first = first or time.time() - t0
                    audio += chunk
            raw = OUT / f"bukola_{name}_{clip}.ulaw"
            raw.write_bytes(audio)
            import subprocess
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "mulaw", "-ar", "8000", "-ac", "1",
                            "-i", str(raw), str(raw.with_suffix(".phone.wav"))], check=True)
            raw.unlink()
            print(f"{clip} {name:16} first audio {first:.2f}s | full {time.time() - t0:.2f}s")


if __name__ == "__main__":
    main()
