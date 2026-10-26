#!/usr/bin/env python3
"""
Generate Westminster 35mm B-Roll Video using Gemini Omni 1.1 Flash via Interactions API.
"""

import os
import base64
import subprocess
from google import genai

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "generative")
os.makedirs(ASSETS_DIR, exist_ok=True)

# Load API key
with open(os.path.expanduser("~/.gemini/secrets.env")) as f:
    for line in f:
        if line.startswith("export GEMINI_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
            os.environ["GEMINI_API_KEY"] = key

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

prompt = (
    "Vertical 9:16 portrait video. Authentic 35mm documentary footage of Westminster City Hall on Victoria Street "
    "in central London. Neoclassical civic architecture, a classic red London double-decker bus moving through frame, "
    "pedestrians walking with umbrellas on a soft overcast British day, natural cinematic film grain, 24fps vertical video."
)

out_path = os.path.join(ASSETS_DIR, "westminster_civic_omni.mp4")
print(f"🎬 Generating Westminster B-roll via gemini-omni-1.1-flash...")
try:
    res = client.interactions.create(
        model="gemini-omni-1.1-flash",
        input=prompt
    )
    if hasattr(res, "output_video") and res.output_video:
        raw = base64.b64decode(res.output_video.data)
        with open(out_path, "wb") as f:
            f.write(raw)
        cmd = ["ffprobe", "-v", "error", "-show_entries", "stream=width,height,duration", "-of", "default=noprint_wrappers=1", out_path]
        probe = subprocess.run(cmd, capture_output=True, text=True)
        print(f"✅ Saved {out_path} ({len(raw)} bytes):")
        print(probe.stdout.strip())
    else:
        print("❌ No video in response:", res)
except Exception as e:
    print(f"❌ Error: {e}")
