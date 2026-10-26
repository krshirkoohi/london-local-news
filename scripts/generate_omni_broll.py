#!/usr/bin/env python3
"""
Generate Borough-Tailored 35mm B-Roll Video Clips using Gemini Omni 1.1 Flash via Interactions API.
"""

import os
import base64
import subprocess
from google import genai

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "generative")

# Load API key
with open(os.path.expanduser("~/.gemini/secrets.env")) as f:
    for line in f:
        if line.startswith("export GEMINI_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('\"').strip('\'')
            os.environ["GEMINI_API_KEY"] = key

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

JOBS = [
    {
        "filename": "camden_estate_omni.mp4",
        "prompt": "Vertical 9:16 portrait video. Documentary 35mm shot of a post-war red-brick council housing estate in Camden, London, mature autumn trees, scaffolding on one corner indicating refurbishment work, overcast British morning daylight, pedestrians in coats walking past, 24fps, 9:16 vertical video."
    },
    {
        "filename": "southwark_civic_omni.mp4",
        "prompt": "Vertical 9:16 portrait video. Cinematic 35mm documentary shot looking up the modern glass and stone facade of Southwark Council Civic Centre on Tooley Street near London Bridge. Pedestrians and cyclists commuting in autumn daylight, overcast London weather, natural muted palette, 24fps, 9:16 vertical video."
    },
    {
        "filename": "southwark_school_street_omni.mp4",
        "prompt": "Vertical 9:16 portrait video. Authentic 35mm documentary shot of a residential tree-lined Victorian street in Southwark, London, during morning school run. Cyclists riding smoothly along a clean pedestrian school street, parents and children walking, wet autumn leaves, soft overcast daylight, 24fps, 9:16 vertical video."
    }
]

for job in JOBS:
    out_path = os.path.join(ASSETS_DIR, job["filename"])
    print(f"\n🎬 Generating {job['filename']} via gemini-omni-1.1-flash...")
    print(f"   Prompt: {job['prompt'][:80]}...")
    try:
        res = client.interactions.create(
            model="gemini-omni-1.1-flash",
            input=job["prompt"]
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
        print(f"❌ Error generating {job['filename']}: {e}")

print("\n🎉 ALL GENERATIVE B-ROLL VIDEO SLOTS COMPLETED!")
