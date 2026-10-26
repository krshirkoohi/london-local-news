#!/usr/bin/env python3
"""
London Local Editorial & Technical Preflight Validator
======================================================
Implements Sections 12, 13, and 16A of the London Local News architecture specification:
1. Schema & Provenance Audit:
   - Verifies structured claims, claim IDs, source quotes, and source document URLs.
   - Ensures every scene maps to at least one verified claim ID.
   - Verifies watchability suitability ('approved_for_video') and editorial gate metadata.
   - Enforces mandatory AI disclaimer on all illustrative/synthetic scenes.
2. Technical Media Inspection (FFprobe / FFmpeg):
   - Verifies 1080x1920 (9:16 vertical) resolution and 30fps frame rate.
   - Verifies duration falls within the short-form target window (25.0s - 42.0s).
   - Verifies H.264 video + AAC audio streams and checks mean/max audio volume (dBFS).
3. Outputs machine-readable report to `output/validation_report.json`.
"""

import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPECS_DIR = os.path.join(BASE_DIR, "specs")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DEMOS_DIR = os.path.join(BASE_DIR, "demos")


def probe_video(mp4_path):
    if not os.path.exists(mp4_path):
        return {"exists": False, "error": "File not found"}

    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size:stream=codec_name,codec_type,width,height,r_frame_rate",
        "-of", "json", mp4_path,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return {"exists": True, "error": res.stderr.strip()}

    info = json.loads(res.stdout)
    streams = info.get("streams", [])
    fmt = info.get("format", {})

    v_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})

    # Check audio levels via volumedetect
    vol_cmd = ["ffmpeg", "-i", mp4_path, "-af", "volumedetect", "-f", "null", "-"]
    vol_res = subprocess.run(vol_cmd, capture_output=True, text=True)
    mean_vol = None
    max_vol = None
    m_mean = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", vol_res.stderr)
    m_max = re.search(r"max_volume:\s*([-\d.]+)\s*dB", vol_res.stderr)
    if m_mean:
        mean_vol = float(m_mean.group(1))
    if m_max:
        max_vol = float(m_max.group(1))

    dur = float(fmt.get("duration", 0.0))
    size_mb = round(int(fmt.get("size", 0)) / (1024 * 1024), 2)
    width = v_stream.get("width")
    height = v_stream.get("height")
    fps = v_stream.get("r_frame_rate")

    checks = {
        "aspect_9_16_1080x1920": (width == 1080 and height == 1920),
        "fps_30": (fps == "30/1"),
        "duration_in_target_25_to_42s": (25.0 <= dur <= 42.0),
        "valid_h264_aac": (v_stream.get("codec_name") == "h264" and a_stream.get("codec_name") == "aac"),
        "non_silent_audio": (mean_vol is not None and mean_vol > -45.0),
    }

    return {
        "exists": True,
        "path": os.path.relpath(mp4_path, BASE_DIR),
        "width": width,
        "height": height,
        "fps": fps,
        "durationSeconds": round(dur, 2),
        "sizeMB": size_mb,
        "videoCodec": v_stream.get("codec_name"),
        "audioCodec": a_stream.get("codec_name"),
        "meanVolumeDb": mean_vol,
        "maxVolumeDb": max_vol,
        "checks": checks,
        "passed": all(checks.values()),
    }


def validate_spec(spec_path):
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    video_id = spec.get("videoId", "unknown")
    story_id = str(spec.get("storyId", ""))
    claims = spec.get("claims", [])
    claim_map = {c.get("claimId"): c for c in claims if c.get("claimId")}

    errors = []
    warnings = []

    if not spec.get("sourceArticleUrl", "").startswith("https://londonlocal.news/stories/"):
        errors.append("Missing or invalid sourceArticleUrl")

    suitability = spec.get("watchability", {}).get("suitability")
    if suitability in ("not_video_worthy", "needs_editorial_input"):
        errors.append(f"Story marked {suitability} by watchability preflight")
    elif suitability != "approved_for_video":
        warnings.append("watchability.suitability not explicitly set to approved_for_video")

    if not claims:
        errors.append("No verified factual claims array found in spec")

    for c in claims:
        cid = c.get("claimId", "?")
        if not c.get("verified"):
            errors.append(f"Claim {cid} is not marked verified=true")
        if not c.get("sourceQuote") or not c.get("sourceDocumentUrl"):
            errors.append(f"Claim {cid} is missing sourceQuote or sourceDocumentUrl")

    for scene in spec.get("timeline", []):
        snum = scene.get("sceneNumber")
        s_claims = scene.get("claimIds", [])
        if not s_claims:
            errors.append(f"Scene {snum} does not reference any verified claimIds")
        for cid in s_claims:
            if cid not in claim_map:
                errors.append(f"Scene {snum} references unknown claimId {cid}")

        vis = scene.get("visualAsset", {})
        if vis.get("isIllustrative") and not vis.get("mandatoryDisclaimer"):
            errors.append(f"Scene {snum} uses illustrative AI media without mandatoryDisclaimer")

    demo_map = {
        "4178": os.path.join(DEMOS_DIR, "westminster_4178_broadcast.mp4"),
        "4182": os.path.join(DEMOS_DIR, "camden_4182_broadcast.mp4"),
        "4185": os.path.join(DEMOS_DIR, "southwark_4185_broadcast.mp4"),
    }
    master_mp4 = os.path.join(OUTPUT_DIR, f"{video_id}.mp4")
    demo_mp4 = demo_map.get(story_id)

    master_probe = probe_video(master_mp4)
    demo_probe = probe_video(demo_mp4) if demo_mp4 else None

    if not master_probe.get("passed"):
        errors.append(f"Master MP4 failed technical checks: {master_probe}")

    return {
        "specFile": os.path.relpath(spec_path, BASE_DIR),
        "videoId": video_id,
        "storyId": story_id,
        "displayStoryId": spec.get("displayStoryId", story_id),
        "sourceArticleUrl": spec.get("sourceArticleUrl"),
        "borough": spec.get("borough"),
        "storyType": spec.get("storyType"),
        "claimsVerifiedCount": len(claims),
        "editorialGate": spec.get("editorialGate"),
        "editorialPreflightPassed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "masterRender": master_probe,
        "demoRender": demo_probe,
        "estimatedGenerationCostGBP": 0.0,
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    spec_files = sorted(glob.glob(os.path.join(SPECS_DIR, "*.json")))
    results = [validate_spec(sp) for sp in spec_files]
    overall_passed = all(r["editorialPreflightPassed"] for r in results)

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "overallPassed": overall_passed,
        "videosValidated": len(results),
        "results": results,
    }

    out_path = os.path.join(OUTPUT_DIR, "validation_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"=== LONDON LOCAL VALIDATION REPORT ({'PASSED' if overall_passed else 'FAILED'}) ===")
    for r in results:
        m = r["masterRender"]
        status = "✅ PASS" if r["editorialPreflightPassed"] else "❌ FAIL"
        print(
            f"  {status} | {r['videoId']} ({r['borough']} -> #{r['displayStoryId']}) | "
            f"Claims: {r['claimsVerifiedCount']} | "
            f"Master: {m.get('durationSeconds')}s, {m.get('width')}x{m.get('height')} @ {m.get('fps')}, "
            f"mean_vol={m.get('meanVolumeDb')}dB"
        )
        for err in r["errors"]:
            print(f"     ! ERROR: {err}")
    print(f"Report written to: {out_path}")
    sys.exit(0 if overall_passed else 1)


if __name__ == "__main__":
    main()
