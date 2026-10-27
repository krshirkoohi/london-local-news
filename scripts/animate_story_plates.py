#!/usr/bin/env python3
"""
Generate True 9:16 Cinematic Video Clips from Verified Editorial Story Plates using Gemini Omni 1.1 Flash.
Enforces locked-off tripod framing and subtle ambient realism to eliminate nausea and looping.
"""

import os
import sys
import base64
import subprocess
from google import genai
from google.genai._gaos.types.interactions.imagecontent import ImageContent
from google.genai._gaos.types.interactions.textcontent import TextContent

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
    # Camden Housing & Retrofit Story (#4182)
    {
        "input_image": "camden_damp_flat.jpg",
        "output_video": "camden_damp_flat_video.mp4",
        "prompt": (
            "Static tripod 35mm documentary camera. Animate this cold London council flat living room with subtle, "
            "natural realism. Condensation water droplets slowly trickle down the single-glazed window pane, subtle cold drafts "
            "in the curtain fabric, soft overcast British morning daylight, completely static locked camera, no camera movement, no zooming."
        )
    },
    {
        "input_image": "camden_town_hall.jpg",
        "output_video": "camden_town_hall_video.mp4",
        "prompt": (
            "Static tripod architectural shot of Camden Town Hall civic centre. London plane tree branches gently sway in the "
            "autumn breeze, subtle traffic and pedestrian movement along the distant Euston Road pavement, soft overcast London light, "
            "completely locked camera, no zooming, no camera pan."
        )
    },
    {
        "input_image": "camden_retrofit_workers.jpg",
        "output_video": "camden_retrofit_workers_video.mp4",
        "prompt": (
            "Static documentary shot. Retrofit workers in high-vis jackets and hard hats actively measuring and fitting external "
            "wall insulation panels on scaffolding against the brick council building. Natural realistic work motion, subtle autumn breeze, "
            "completely locked tripod camera, no zooming."
        )
    },
    {
        "input_image": "camden_warm_home.jpg",
        "output_video": "camden_warm_home_video.mp4",
        "prompt": (
            "Static tripod shot of a warm, newly retrofitted council flat living room. Warm ambient lamp light illuminating clean insulated walls, "
            "digital thermostat glowing softly, subtle movement outside the double-glazed window of distant London clouds, "
            "peaceful and comfortable atmosphere, locked camera, no zooming."
        )
    },

    # Southwark School Streets & Clean Air Story (#4185)
    {
        "input_image": "southwark_school_traffic.jpg",
        "output_video": "southwark_school_traffic_video.mp4",
        "prompt": (
            "Static documentary shot outside a Southwark primary school. Exhaust vapour drifts in the crisp cold autumn air from "
            "idling delivery vans and cars queueing at the junction, brake lights glowing in the morning traffic, parents holding children's hands "
            "waiting on the pavement, locked camera, no camera movement."
        )
    },
    {
        "input_image": "southwark_school_sign.jpg",
        "output_video": "southwark_school_sign_video.mp4",
        "prompt": (
            "Static locked camera shot of the School Street road sign and ANPR camera on the lamppost. Tree leaves blow gently in "
            "the breeze behind the sign, calm residential London street background, locked tripod camera, no zooming."
        )
    },
    {
        "input_image": "southwark_car_free_school.jpg",
        "output_video": "southwark_car_free_school_video.mp4",
        "prompt": (
            "Calm, steady forward tracking shot of a quiet, car-free residential school street. School children glide forward smoothly "
            "on kick scooters away from the camera towards the primary school gates, crisp autumn leaves on the pavement, smooth flowing motion "
            "in one direction, no walking back and forth, peaceful morning atmosphere."
        )
    },
    {
        "input_image": "southwark_clean_air_sensor.jpg",
        "output_video": "southwark_clean_air_sensor_video.mp4",
        "prompt": (
            "Static close-up macro shot of the air monitoring sensor box on the Victorian school railings. Small digital LED blinks softly, "
            "children playing in the soft-focus blurred background playground, morning sunlight glinting on the cast iron railing, locked camera."
        )
    },

    # Tower Hamlets D7 Bus Story (#10441)
    {
        "input_image": "d7_bus_isle_of_dogs.png",
        "output_video": "d7_bus_isle_of_dogs_video.mp4",
        "prompt": (
            "Static eye-level documentary shot of a red London double-decker bus on route D7. The bus idles gently at the roadside on "
            "an Isle of Dogs street in East London, subtle rain droplets on the windscreen, wet reflections on asphalt, distant Canary Wharf towers, "
            "locked tripod camera, no camera movement, no zooming."
        )
    }
]

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    for job in JOBS:
        if target and target not in job["output_video"]:
            continue

        in_path = os.path.join(ASSETS_DIR, job["input_image"])
        out_path = os.path.join(ASSETS_DIR, job["output_video"])

        if not os.path.exists(in_path):
            print(f"⚠️ Input image not found: {in_path}, skipping...")
            continue

        print(f"\n🎬 Animating {job['input_image']} -> {job['output_video']}...")
        print(f"   Prompt: {job['prompt'][:80]}...")

        with open(in_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")

        mime_type = "image/png" if in_path.endswith(".png") else "image/jpeg"

        try:
            res = client.interactions.create(
                model="gemini-omni-1.1-flash",
                input=[
                    ImageContent(data=b64_data, mime_type=mime_type),
                    TextContent(text=job["prompt"])
                ]
            )

            if hasattr(res, "output_video") and res.output_video:
                raw_bytes = base64.b64decode(res.output_video.data)
                with open(out_path, "wb") as vf:
                    vf.write(raw_bytes)

                probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "stream=width,height,duration", "-of", "default=noprint_wrappers=1", out_path]
                probe = subprocess.run(probe_cmd, capture_output=True, text=True)
                print(f"  ✅ Saved {out_path} ({len(raw_bytes)} bytes): {probe.stdout.strip()}")
            else:
                print(f"  ❌ No output_video in response for {job['output_video']}")
        except Exception as e:
            print(f"  ❌ Error animating {job['output_video']}: {e}")

if __name__ == "__main__":
    main()
