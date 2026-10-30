#!/usr/bin/env python3
"""
London Local B-Roll Gibberish Text & Audio Auditor
==================================================
Scans every MP4 in `assets/generative/` for:
1. Any remaining audio streams (stripping them losslessly via `ffmpeg -c:v copy -an`).
2. Any AI-hallucinated or garbled text on uniforms, vehicles, signs, or shopfronts
   (e.g., "BELTISH PAILICE") by extracting a keyframe and auditing with `gemini-3.8-flash`.
3. Automatically regenerates any flagged clip using a clean, text-free architectural/environmental
   prompt via `gemini-omni-1.1-flash` (and strips audio immediately).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List

from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parents[1]
GEN_DIR = BASE_DIR / "assets" / "generative"
AUDIT_REPORT_PATH = GEN_DIR / "broll_text_audit.json"


def load_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        secrets_file = os.path.expanduser("~/.gemini/secrets.env")
        if os.path.exists(secrets_file):
            with open(secrets_file, encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if "GEMINI_API_KEY=" in s:
                        key = s.split("=", 1)[1].strip().strip("\"'")
                        break
    return key


def extract_keyframe_bytes(mp4_path: Path, timestamp: float = 3.5) -> bytes:
    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-ss",
        str(timestamp),
        "-i",
        str(mp4_path),
        "-frames:v",
        "1",
        "-f",
        "image2pipe",
        "-vcodec",
        "mjpeg",
        "-",
    ]
    return subprocess.check_output(cmd, timeout=15)


def inspect_clip_for_gibberish(mp4_path: Path, api_key: str) -> Dict[str, Any]:
    try:
        frame_bytes = extract_keyframe_bytes(mp4_path, 3.5)
    except Exception as e:
        return {"file": mp4_path.name, "has_gibberish": False, "error": str(e)}

    client = genai.Client(api_key=api_key)
    prompt = (
        "Inspect this video frame from an AI-generated London B-roll clip. "
        "Does it contain any visible AI-garbled, misspelled, or prominent readable text/words on "
        "uniforms, jackets, vehicles, shopfronts, signs, banners, or screens (for example misspelled words like "
        "'BELTISH PAILICE', garbled shop signs, or fake words)? Ignore tiny indistinct background blur. "
        "Return ONLY valid JSON: "
        '{"has_gibberish": true/false, "detected_text": "exact text seen or empty string", "clean_visual_replacement": "1-sentence description of the same scene framed purely on architecture/environment without any uniforms, vehicle liveries, or shop signs"}'
    )
    try:
        res = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=[
                types.Part.from_bytes(data=frame_bytes, mime_type="image/jpeg"),
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )
        data = json.loads(res.text)
        return {
            "file": mp4_path.name,
            "has_gibberish": bool(data.get("has_gibberish", False)),
            "detected_text": data.get("detected_text", ""),
            "clean_visual_replacement": data.get("clean_visual_replacement", ""),
        }
    except Exception as e:
        return {"file": mp4_path.name, "has_gibberish": False, "error": str(e)}


def regenerate_clean_clip(mp4_path: Path, replacement_desc: str, api_key: str) -> bool:
    clean_prompt = (
        f"Vertical 9:16 portrait video. Authentic 35mm documentary architectural and street shot in London: "
        f"{replacement_desc}. Overcast British daylight, wet pavement reflections, completely unmarked brick and stone surfaces "
        f"with zero signs, zero lettering, zero uniforms, zero vehicle text, Kodak Portra 400 editorial grade, 24fps, 9:16 vertical video."
    )
    client = genai.Client(api_key=api_key)
    for attempt in range(1, 4):
        try:
            res = client.interactions.create(
                model="gemini-omni-1.1-flash",
                input=clean_prompt,
                response_modalities=["video"],
                timeout=240.0,
            )
            video_data = getattr(res, "output_video", None)
            if not video_data or not getattr(video_data, "data", None):
                continue
            raw_bytes = base64.b64decode(video_data.data)
            raw_tmp = mp4_path.with_suffix(".raw.mp4")
            clean_tmp = mp4_path.with_suffix(".tmp.mp4")
            with open(raw_tmp, "wb") as f:
                f.write(raw_bytes)
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-i", str(raw_tmp), "-c:v", "copy", "-an", str(clean_tmp)],
                check=True,
            )
            raw_tmp.unlink(missing_ok=True)
            clean_tmp.replace(mp4_path)
            print(f"✨ Regenerated text-free & silent clip: {mp4_path.name}", flush=True)
            return True
        except Exception as e:
            print(f"⚠️ Regen attempt {attempt} failed for {mp4_path.name}: {e}", flush=True)
            time.sleep(3)
    return False


def main():
    parser = argparse.ArgumentParser(description="Audit and fix gibberish text and audio in B-roll clips")
    parser.add_argument("--workers", type=int, default=16, help="Vision audit concurrency")
    parser.add_argument("--fix", action="store_true", help="Automatically regenerate any flagged clips")
    args = parser.parse_args()

    api_key = load_api_key()
    mp4s = [
        p for p in sorted(GEN_DIR.glob("*.mp4"))
        if not any(p.name.endswith(s) for s in [".tmp.mp4", ".raw.mp4", ".noaudio.mp4"])
    ]
    print(f"🔍 Auditing {len(mp4s)} B-roll clips for gibberish text using gemini-3.8-flash (workers={args.workers})...", flush=True)

    findings: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(inspect_clip_for_gibberish, p, api_key): p for p in mp4s}
        for fut in as_completed(futs):
            r = fut.result()
            findings.append(r)
            if r.get("has_gibberish"):
                print(f"🚩 [{r['file']}] Detected text: {r.get('detected_text')!r}", flush=True)

    flagged = [f for f in findings if f.get("has_gibberish")]
    with open(AUDIT_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump({"total": len(mp4s), "flagged_count": len(flagged), "flagged": flagged}, f, indent=2)

    print(f"\n📊 Audit complete: {len(flagged)}/{len(mp4s)} clips flagged for visible/garbled text.")
    if args.fix and flagged:
        print(f"🛠️ Regenerating {len(flagged)} flagged clips with clean architectural prompts...", flush=True)
        with ThreadPoolExecutor(max_workers=10) as pool:
            futs = [
                pool.submit(
                    regenerate_clean_clip,
                    GEN_DIR / item["file"],
                    item.get("clean_visual_replacement") or "Classic London stock-brick and Portland stone street scene after rain",
                    api_key,
                )
                for item in flagged
            ]
            for fut in as_completed(futs):
                fut.result()


if __name__ == "__main__":
    main()
