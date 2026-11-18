"""Play the phone-quality test clips to OpenAI realtime models (the family behind ChatGPT voice).

Usage: backend/.venv/bin/python eval/test_openai_realtime.py
Needs OPENAI_API_KEY in backend/.env. Writes eval/results/openai_<model>_<prompt>_<clip>.wav
and eval/results/openai_realtime_results.json. Prompts match eval/test_gemini_live.py.
"""
import asyncio
import base64
import json
import subprocess
from pathlib import Path

import websockets
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
KEY = dotenv_values(ROOT / "backend/.env").get("OPENAI_API_KEY")
MODELS = ["gpt-realtime-2.1", "gpt-realtime-2"]
CLIPS = sorted((ROOT / "eval/clips/phone").glob("clip*_mulaw.wav"))
OUT = ROOT / "eval/results"

BASE_PROMPT = (
    "You are Ayo, a warm, calm voice on a free phone line that children can call. "
    "Children may call to chat or because something is wrong. Speak in one to three short sentences."
)
TONE_PROMPT = BASE_PROMPT + (
    " Pay close attention to HOW the child sounds, not only their words. If they sound like they are "
    "crying, scared, whispering, or flat and numb, respond to that feeling first, even if their words say "
    "they are fine. If they whisper, keep your answers very short and ask if they are safe."
)


def raw_mulaw(path: Path) -> bytes:
    """Strip the WAV header: return raw 8 kHz G.711 mu-law bytes."""
    return subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "mulaw", "-ar", "8000", "-ac", "1", "-"],
                          capture_output=True, check=True).stdout


async def run(model, prompt, clip):
    url = f"wss://api.openai.com/v1/realtime?model={model}"
    audio_out, said, heard, events = bytearray(), "", "", []
    async with websockets.connect(url, additional_headers={"Authorization": f"Bearer {KEY}"},
                                  max_size=16 * 1024 * 1024, open_timeout=15) as ws:
        await ws.send(json.dumps({"type": "session.update", "session": {
            "type": "realtime", "output_modalities": ["audio"], "instructions": prompt,
            "audio": {
                "input": {"format": {"type": "audio/pcmu"},
                          "transcription": {"model": "gpt-4o-mini-transcribe"},
                          "turn_detection": None},
                "output": {"format": {"type": "audio/pcmu"}, "voice": "marin"},
            }}}))
        pcm = raw_mulaw(clip)  # whole clip = one caller turn (pauses in crying must not split it)
        for i in range(0, len(pcm), 160):  # 20 ms frames, real-time pace, like a phone call
            await ws.send(json.dumps({"type": "input_audio_buffer.append",
                                      "audio": base64.b64encode(pcm[i:i + 160]).decode()}))
            await asyncio.sleep(0.02)
        await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
        await ws.send(json.dumps({"type": "response.create"}))
        done_at = None
        try:
            while True:
                ev = json.loads(await asyncio.wait_for(ws.recv(), 6 if done_at else 30))
                t = ev.get("type", "")
                if t in ("response.output_audio.delta", "response.audio.delta"):
                    audio_out += base64.b64decode(ev["delta"])
                elif t in ("response.output_audio_transcript.delta", "response.audio_transcript.delta"):
                    said += ev.get("delta", "")
                elif t == "conversation.item.input_audio_transcription.completed":
                    heard += ev.get("transcript", "")
                elif t == "error":
                    events.append(ev.get("error"))
                    if not audio_out:
                        break
                elif t == "response.done":
                    events.append({"status": ev.get("response", {}).get("status")})
                    done_at = asyncio.get_running_loop().time()
                if done_at and heard:
                    break
        except asyncio.TimeoutError:
            events.append("timeout")
    return {"heard": heard.strip(), "said": said.strip(), "errors": events, "audio": bytes(audio_out)}


async def main():
    if not KEY:
        raise SystemExit("Add OPENAI_API_KEY=... to backend/.env first.")
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for clip in CLIPS:
        row = {"clip": clip.name}
        for model in MODELS:
            for pname, prompt in (("plain", BASE_PROMPT), ("tone", TONE_PROMPT)):
                try:
                    res = await run(model, prompt, clip)
                except Exception as exc:
                    res = {"error": f"{type(exc).__name__}: {str(exc)[:300]}"}
                audio = res.pop("audio", b"")
                if audio:
                    stem = OUT / f"openai_{model}_{pname}_{clip.stem.replace('_mulaw', '')}"
                    stem.with_suffix(".ulaw").write_bytes(audio)
                    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "mulaw", "-ar", "8000", "-ac", "1",
                                    "-i", str(stem.with_suffix(".ulaw")), str(stem.with_suffix(".wav"))], check=True)
                    stem.with_suffix(".ulaw").unlink()
                row[f"{model}|{pname}"] = res
                print(clip.name, model, pname, "->", res.get("said") or res.get("errors") or res.get("error"))
        results.append(row)
    (OUT / "openai_realtime_results.json").write_text(json.dumps(results, indent=2))


asyncio.run(main())
