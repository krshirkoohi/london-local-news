#!/usr/bin/env python3
"""
Generate 9:16 documentary B-roll videos using Google Gemini Omni (Interactions API).
Model: models/gemini-omni-1.1-flash
"""

import argparse
import base64
import os
import sys
from google import genai
from google.genai import types

DEFAULT_NEGATIVE_PROMPT = (
    " Negative prompt: no readable signage text, no gibberish lettering, no speaking faces, "
    "no lip-syncing, no politicians, no council chamber interiors, no protest placards, "
    "no neon lighting, no oversaturated HDR, no warped hands."
)


def load_api_key(api_key: str = None) -> str:
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        secrets_file = os.path.expanduser("~/.gemini/secrets.env")
        if os.path.exists(secrets_file):
            with open(secrets_file, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        key = line.strip().split("=", 1)[1].strip("\"'")
                        break
    return key


def generate_video(prompt: str, output_path: str, ref_image_path: str = None, api_key: str = None):
    key = load_api_key(api_key)
    if not key:
        print("Error: No GEMINI_API_KEY found in environment or ~/.gemini/secrets.env", file=sys.stderr)
        sys.exit(1)

    full_prompt = prompt if "Negative prompt:" in prompt else (prompt + DEFAULT_NEGATIVE_PROMPT)
    print(f"🎬 Sending prompt to Gemini Omni (models/gemini-omni-1.1-flash): {output_path}")
    client = genai.Client(api_key=key)

    inputs = full_prompt
    if ref_image_path and os.path.exists(ref_image_path):
        with open(ref_image_path, "rb") as img_f:
            img_bytes = img_f.read()
        mime = "image/png" if ref_image_path.lower().endswith(".png") else "image/jpeg"
        inputs = [types.Part.from_bytes(data=img_bytes, mime_type=mime), full_prompt]

    res = client.interactions.create(
        model="gemini-omni-1.1-flash",
        input=inputs,
        response_modalities=["video"],
        timeout=180.0,
    )

    video_data = getattr(res, "output_video", None)
    if not video_data or not getattr(video_data, "data", None):
        raise RuntimeError(f"No video returned in response: {res}")

    raw_bytes = base64.b64decode(video_data.data)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(raw_bytes)

    print(f"✅ Video generated ({len(raw_bytes):,} bytes): {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate 9:16 B-roll video using Google Gemini Omni")
    parser.add_argument("--prompt", "-p", required=True, help="Documentary 35mm B-roll prompt")
    parser.add_argument("--output", "-o", default="generated_video.mp4", help="Output MP4 file path")
    parser.add_argument("--image", "-i", default=None, help="Optional reference image plate")
    args = parser.parse_args()

    generate_video(prompt=args.prompt, output_path=args.output, ref_image_path=args.image)
