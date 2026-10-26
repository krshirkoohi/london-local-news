#!/usr/bin/env python3
"""
London Local News - Gemini Video Ingestion Utility
Quickly imports newly downloaded 'gemini_generated_video_*.mp4' files from ~/Downloads,
renames them to the canonical slot, updates the story spec, and triggers build_demo.py.
"""

import os
import glob
import shutil
import argparse
import subprocess
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "generative")
SPECS_DIR = os.path.join(BASE_DIR, "specs")

DOWNLOADS_DIRS = [
    os.path.expanduser("~/Downloads"),
    "/Users/krshirkoohi/Library/Mobile Documents/com~apple~CloudDocs/Downloads"
]

SLOT_MAP = {
    "camden_town_hall": {
        "target": "camden_town_hall_video.mp4",
        "spec": "4182-camden-housing-retrofit.json",
        "scenes": [1]
    },
    "camden_estate": {
        "target": "camden_estate_video.mp4",
        "spec": "4182-camden-housing-retrofit.json",
        "scenes": [4]
    },
    "southwark_civic": {
        "target": "southwark_civic_video.mp4",
        "spec": "4185-southwark-clean-air-schools.json",
        "scenes": [1]
    },
    "southwark_school_street": {
        "target": "southwark_school_street_video.mp4",
        "spec": "4185-southwark-clean-air-schools.json",
        "scenes": [4]
    }
}

def find_latest_gemini_download():
    candidates = []
    for d in DOWNLOADS_DIRS:
        if os.path.exists(d):
            files = glob.glob(os.path.join(d, "gemini_generated_video_*.mp4"))
            candidates.extend(files)
    if not candidates:
        return None
    # Sort by modification time descending
    candidates.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return candidates[0]

def main():
    parser = argparse.ArgumentParser(description="Ingest latest Gemini generated video into London Local pipeline")
    parser.add_argument("--slot", type=str, required=True, choices=list(SLOT_MAP.keys()), help="Target generative slot")
    parser.add_argument("--file", type=str, default=None, help="Explicit MP4 file path (optional)")
    parser.add_argument("--build", action="store_true", default=True, help="Automatically build the updated reel")
    args = parser.parse_args()

    cfg = SLOT_MAP[args.slot]
    src_file = args.file or find_latest_gemini_download()

    if not src_file or not os.path.exists(src_file):
        print(f"❌ Error: No Gemini generated video found in Downloads. (Checked {DOWNLOADS_DIRS})")
        return

    dest_path = os.path.join(ASSETS_DIR, cfg["target"])
    shutil.copy2(src_file, dest_path)
    print(f"✓ Ingested: {src_file} -> {os.path.relpath(dest_path, BASE_DIR)}")

    # Update spec
    spec_path = os.path.join(SPECS_DIR, cfg["spec"])
    if os.path.exists(spec_path):
        with open(spec_path, "r", encoding="utf-8") as f:
            spec = json.load(f)

        for scene in spec.get("timeline", []):
            if scene.get("sceneNumber") in cfg["scenes"]:
                scene["visualAsset"]["type"] = "video"
                scene["visualAsset"]["source"] = f"assets/generative/{cfg['target']}"
                scene["visualAsset"]["cropMode"] = "full"
                print(f"  ✓ Updated Scene {scene['sceneNumber']} in {cfg['spec']} to use {cfg['target']}")

        with open(spec_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2)

    if args.build:
        print("\n🎬 Rebuilding broadcast reel with new video...")
        cmd = ["python3", os.path.join(BASE_DIR, "scripts", "build_demo.py"), "--spec", spec_path]
        subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()
