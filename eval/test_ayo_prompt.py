"""Test the real Ayo prompt on gpt-realtime-2.1, with and without listener notes.
Usage: backend/.venv/bin/python eval/test_ayo_prompt.py
"""
import asyncio, base64, json, subprocess
from pathlib import Path
import websockets
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
KEY = dotenv_values(ROOT / "backend/.env")["OPENAI_API_KEY"]
MODEL = "gpt-realtime-2.1"
OUT = ROOT / "eval/results"
RUNTIME = ("Caller country: Nigeria (from phone number; may differ from current location). "
           "Network region: Lagos. Approved local numbers: Cece Yara Child Helpline 0800 800 8001; emergency 112. "
           "Safeguarding handoff: not yet available on this line.")
PROMPT = (ROOT / "eval/prompts/ayo_realtime_prompt.md").read_text().replace("{RUNTIME_CONTEXT}", RUNTIME)
# Listener notes = what the Gemini Flash listener said about each clip today.
NOTES = {
    "clip01": "[LISTENER: caller sounds like they are crying]",
    "clip02": "[LISTENER: caller is whispering; may be monitored]",
    "clip03": "[LISTENER: frightened, hesitant delivery]",
    "clip04": "[LISTENER: very quiet, hushed delivery; may be monitored]",
    "clip05": None,
}

def raw_mulaw(path):
    return subprocess.run(["ffmpeg","-loglevel","error","-i",str(path),"-f","mulaw","-ar","8000","-ac","1","-"],
                          capture_output=True, check=True).stdout

async def run(clip, note):
    audio_out, said = bytearray(), ""
    async with websockets.connect(f"wss://api.openai.com/v1/realtime?model={MODEL}",
                                  additional_headers={"Authorization": f"Bearer {KEY}"}, max_size=16*1024*1024) as ws:
        await ws.send(json.dumps({"type": "session.update", "session": {
            "type": "realtime", "output_modalities": ["audio"], "instructions": PROMPT,
            "audio": {"input": {"format": {"type": "audio/pcmu"}, "turn_detection": None},
                      "output": {"format": {"type": "audio/pcmu"}, "voice": "marin"}}}}))
        pcm = raw_mulaw(clip)
        for i in range(0, len(pcm), 160):
            await ws.send(json.dumps({"type": "input_audio_buffer.append", "audio": base64.b64encode(pcm[i:i+160]).decode()}))
            await asyncio.sleep(0.02)
        await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
        if note:
            await ws.send(json.dumps({"type": "conversation.item.create", "item": {
                "type": "message", "role": "system", "content": [{"type": "input_text", "text": note}]}}))
        await ws.send(json.dumps({"type": "response.create"}))
        while True:
            ev = json.loads(await asyncio.wait_for(ws.recv(), 40))
            t = ev.get("type", "")
            if t == "response.output_audio.delta": audio_out += base64.b64decode(ev["delta"])
            elif t == "response.output_audio_transcript.delta": said += ev["delta"]
            elif t == "error": said += f" [ERROR {ev.get('error',{}).get('message')}]"
            elif t == "response.done": break
    return said.strip(), bytes(audio_out)

async def main():
    rows = []
    for clip in sorted((ROOT / "eval/clips/phone").glob("clip*_mulaw.wav")):
        cid = clip.stem.split("_")[0]
        for variant, note in (("prompt", None), ("prompt+listener", NOTES[cid])):
            if variant == "prompt+listener" and not note:
                continue
            for attempt in range(3):
                try:
                    said, audio = await run(clip, note); break
                except Exception as exc:
                    said, audio = f"[failed: {type(exc).__name__}]", b""
                    await asyncio.sleep(2)
            if audio:
                raw = OUT / f"ayo_{variant}_{cid}.ulaw"; raw.write_bytes(audio)
                subprocess.run(["ffmpeg","-loglevel","error","-y","-f","mulaw","-ar","8000","-ac","1","-i",str(raw),str(raw.with_suffix(".wav"))]); raw.unlink()
            rows.append({"clip": cid, "variant": variant, "note": note, "said": said})
            print(f"{cid} | {variant:16} | {said}")
    (OUT / "ayo_prompt_results.json").write_text(json.dumps(rows, indent=2))

asyncio.run(main())
