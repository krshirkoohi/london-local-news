#!/usr/bin/env python3
"""
OCN Multimodal Video Quality and Editorial Review Runner
========================================================
Implements Milestone 2 of docs/ocn-video-improvement-plan.md:
- Structured inspection of rendered video, audio, timeline, and claims.
- Evaluates against the 9 OCN rubric dimensions:
  1. Opening Hook
  2. Local Relevance
  3. Narrative Development
  4. Retention & Pacing
  5. Visual Credibility & Contrast
  6. Audio & Voice Cadence
  7. Subtitles & Typography
  8. Factual Accuracy
  9. Editorial Safety & AI Disclosure
- Produces machine-readable findings.json with severity, evidence, and proposed changes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from production_contract import scene_layout


def probe_media(video_path: Path) -> Dict[str, Any]:
    """Runs ffprobe and volume detection on the target video."""
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Video stream probe
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,codec_name,duration:format=duration",
        "-of", "json",
        str(video_path)
    ]
    raw_probe = subprocess.check_output(probe_cmd, text=True)
    probe_data = json.loads(raw_probe)
    stream = probe_data.get("streams", [{}])[0]
    fmt = probe_data.get("format", {})

    width = int(stream.get("width", 0))
    height = int(stream.get("height", 0))
    codec = stream.get("codec_name", "unknown")
    fps_parts = stream.get("r_frame_rate", "30/1").split("/")
    fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0
    duration = float(fmt.get("duration", stream.get("duration", 0.0)))

    # Audio volume detection
    vol_cmd = [
        "ffmpeg", "-i", str(video_path),
        "-af", "volumedetect",
        "-f", "null", "-"
    ]
    vol_res = subprocess.run(vol_cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
    mean_vol_match = re.search(r"mean_volume:\s*(-?[\d.]+)\s*dB", vol_res.stderr)
    mean_volume = float(mean_vol_match.group(1)) if mean_vol_match else -20.0

    return {
        "width": width,
        "height": height,
        "fps": fps,
        "codec": codec,
        "duration": duration,
        "mean_volume_db": mean_volume,
    }


def audit_spec_and_video(spec: Dict[str, Any], video_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluates the spec, media metrics, and timeline against the 9 OCN dimensions."""
    timeline = spec.get("timeline", [])
    claims = spec.get("claims", [])
    branding = spec.get("branding", {})
    editorial_gate = spec.get("editorialGate", {})

    findings: List[Dict[str, Any]] = []
    finding_counter = 1

    def add_finding(scene_id: str, category: str, severity: str, obs: str, ev: str, change: str, files: List[str] = None, regen: bool = False):
        nonlocal finding_counter
        findings.append({
            "id": f"R{finding_counter:03d}",
            "scene_id": scene_id,
            "category": category,
            "severity": severity,
            "observation": obs,
            "evidence": ev,
            "proposed_change": change,
            "affected_files": files or ["specs/" + spec.get("videoId", "story") + ".json"],
            "requires_regeneration": regen,
            "confidence": 0.95,
        })
        finding_counter += 1

    # 1. Technical Conformance
    tech_passed = True
    if video_meta["width"] != 1080 or video_meta["height"] != 1920:
        tech_passed = False
        add_finding("global", "technical", "high", "Video is not in 1080x1920 9:16 portrait resolution",
                    f"Measured {video_meta['width']}x{video_meta['height']}", "Re-render with standard 1080x1920 canvas")

    if not (25.0 <= video_meta["duration"] <= 45.0):
        add_finding("global", "retention", "medium", "Reel duration outside optimal mobile window (25-42s)",
                    f"Measured duration: {video_meta['duration']:.2f}s", "Adjust scene pacing or trim outro dwell")

    if not (-24.0 <= video_meta["mean_volume_db"] <= -14.0):
        add_finding("global", "audio", "medium", "Mean audio volume out of broadcast loudness bounds (-24 to -14 dB)",
                    f"Measured mean volume: {video_meta['mean_volume_db']:.1f} dB", "Normalize audio gain in build_demo.py")

    # 2. Subtitles & British Voice Standards
    show_captions = branding.get("showCaptions", False)
    if show_captions:
        add_finding("global", "subtitles", "high", "Burned-in subtitles are enabled in spec branding",
                    "showCaptions: true in spec", "Set branding.showCaptions to false (platforms provide native captions)")

    voice_profile = branding.get("voiceProfile", "")
    if voice_profile != "en-gb-advisor-1":
        add_finding("global", "audio", "medium", "Spec does not specify primary British Gemini 3.8 TTS voice (en-gb-advisor-1)",
                    f"voiceProfile: {voice_profile!r}", "Set branding.voiceProfile to 'en-gb-advisor-1'")

    # 3. Typography & Section Headings
    for scene in timeline:
        sc_num = scene.get("sceneNumber", 1)
        sc_layout = scene_layout(scene)
        sc_id = f"scene_{sc_num:02d}"

        if sc_layout == "key_points":
            heading = spec.get("keyPointsHeading", scene.get("onScreenGraphic", {}).get("headline", "Key points"))
            if heading.strip().lower() == "key points":
                add_finding(sc_id, "typography", "medium",
                            "Generic 'Key points' slide title makes broadcast look like a corporate presentation",
                            f"Header on scene {sc_num} is literal 'Key points'",
                            "Replace with narrative action headline (e.g. 'What would change for residents?')")

        if sc_layout == "facts_figures":
            heading = spec.get("factsFiguresHeading", scene.get("onScreenGraphic", {}).get("headline", "Facts and figures"))
            if heading.strip().lower() == "facts and figures":
                add_finding(sc_id, "typography", "medium",
                            "Generic 'Facts and figures' title lacks editorial urgency",
                            f"Header on scene {sc_num} is literal 'Facts and figures'",
                            "Replace with narrative angle (e.g. 'Opposing Arguments & Timeline')")

        # 4. AI Disclosure & Illustrative B-Roll Safety
        vis = scene.get("visualAsset", {})
        if sc_layout != "outro" and vis.get("type") != "video":
            add_finding(sc_id, "visual_comprehension", "high",
                        "Non-outro scene uses static image or solid instead of moving 9:16 video B-roll",
                        f"Asset: {vis.get('source')} (type={vis.get('type')})",
                        "Replace with 9:16 moving documentary clip generated via gemini-omni-1.1-flash")
        if vis.get("isIllustrative", False) and not vis.get("mandatoryDisclaimer"):
            add_finding(sc_id, "editorial_safety", "high",
                        "Illustrative synthetic asset missing mandatory AI disclaimer",
                        f"Asset: {vis.get('source')} marked illustrative with no disclaimer",
                        "Set mandatoryDisclaimer: 'AI-GENERATED MEDIA'")

    # 5. Factual Claims Coverage
    claim_ids = {c.get("claimId") for c in claims if "claimId" in c}
    timeline_claims = set()
    for s in timeline:
        for cid in s.get("claimIds", []):
            timeline_claims.add(cid)

    unmapped_claims = timeline_claims - claim_ids
    if unmapped_claims:
        add_finding("global", "factual_accuracy", "high",
                    "Timeline references claim IDs not present in verified claims register",
                    f"Unmapped claim IDs: {sorted(list(unmapped_claims))}",
                    "Add source citations for all claims in claims register")

    # 6. Editorial Gate Status
    gate_status = editorial_gate.get("status", "pending_review")
    editor_approved = editorial_gate.get("editorApproved", False)
    reviewer = editorial_gate.get("reviewedBy")

    # Score calculation
    def calc_score(dim: str) -> int:
        cat_findings = [f for f in findings if f["category"] == dim]
        highs = sum(1 for f in cat_findings if f["severity"] == "high")
        meds = sum(1 for f in cat_findings if f["severity"] == "medium")
        if highs > 0:
            return 2
        if meds > 0:
            return 3
        return 5

    has_hook = bool(spec.get("watchability", {}).get("hook") or
                    spec.get("watchability", {}).get("hookStyle") or
                    (timeline and timeline[0].get("onScreenGraphic", {}).get("headline")))
    rubric_scores = {
        "local_relevance": 5 if spec.get("borough") else 3,
        "opening_hook": 4 if has_hook else 2,
        "structure_payoff": 4 if len(timeline) >= 4 else 3,
        "retention_pacing": calc_score("retention"),
        "visual_comprehension": calc_score("visual_comprehension") if tech_passed else 2,
        "subtitles": 5 if not show_captions else 2,
        "audio_clarity": calc_score("audio"),
        "factual_accuracy": calc_score("factual_accuracy"),
        "editorial_safety": calc_score("editorial_safety"),
    }

    mean_score = sum(rubric_scores.values()) / len(rubric_scores)

    return {
        "spec_id": spec.get("videoId", "story"),
        "borough": spec.get("borough", "London"),
        "video_metrics": video_meta,
        "editorial_gate": {
            "status": gate_status,
            "editor_approved": editor_approved,
            "reviewed_by": reviewer,
        },
        "claims_audit": {
            "total_registered_claims": len(claims),
            "timeline_claims_used": len(timeline_claims),
            "unmapped_claims": list(unmapped_claims),
        },
        "rubric_scores": rubric_scores,
        "mean_rubric_score": round(mean_score, 2),
        "hard_release_gates_passed": len([f for f in findings if f["severity"] == "high"]) == 0 and editor_approved,
        "findings": findings,
    }


def find_default_video(spec_path: Path) -> Path:
    """Finds existing draft or demo video matching the spec."""
    spec_data = json.loads(spec_path.read_text(encoding="utf-8"))
    video_id = spec_data.get("videoId", "")
    story_id = str(spec_data.get("storyId", ""))

    candidates = [
        ROOT / "build/drafts" / f"{video_id}.mp4",
        ROOT / "output" / f"{video_id}_broadcast.mp4",
        ROOT / "demos" / f"westminster_{story_id}_broadcast.mp4",
        ROOT / "demos" / f"camden_{story_id}_broadcast.mp4",
        ROOT / "demos" / f"southwark_{story_id}_broadcast.mp4",
        ROOT / "demos" / f"d7_bus_{story_id}_broadcast.mp4",
    ]
    for c in candidates:
        if c.exists():
            return c
    # Fallback to any file in demos matching story_id
    matches = list((ROOT / "demos").glob(f"*{story_id}*.mp4"))
    if matches:
        return matches[0]

    raise FileNotFoundError(f"No rendered video found for spec {spec_path.name}")


def main():
    parser = argparse.ArgumentParser(description="OCN Multimodal Quality and Editorial Review Runner")
    parser.add_argument("--spec", required=True, help="Path to story specification JSON")
    parser.add_argument("--video", help="Path to rendered MP4 video (optional)")
    parser.add_argument("--run-id", default="audit-run-1", help="Unique run identifier")
    parser.add_argument("--out", help="Output JSON findings path")
    args = parser.parse_args()

    spec_path = Path(args.spec).resolve()
    spec_data = json.loads(spec_path.read_text(encoding="utf-8"))

    video_path = Path(args.video).resolve() if args.video else find_default_video(spec_path)
    video_meta = probe_media(video_path)

    report = audit_spec_and_video(spec_data, video_meta)
    report["run_id"] = args.run_id
    report["spec_file"] = str(spec_path.relative_to(ROOT))
    report["video_file"] = str(video_path.relative_to(ROOT))

    # Output path
    out_dir = ROOT / "production-runs" / args.run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = Path(args.out) if args.out else out_dir / "findings.json"
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Print summary
    print("=" * 68)
    print(f"📋 OCN MULTIMODAL REVIEW REPORT: {report['borough'].upper()} ({report['spec_id']})")
    print(f"   Video: {report['video_file']} ({video_meta['duration']:.2f}s, {video_meta['width']}x{video_meta['height']} @ {video_meta['fps']:.0f}fps)")
    print(f"   Loudness: {video_meta['mean_volume_db']:.1f} dB | Mean Rubric Score: {report['mean_rubric_score']} / 5.0")
    print("=" * 68)

    print("\n📊 Rubric Dimension Scores:")
    for dim, score in report["rubric_scores"].items():
        symbol = "✅" if score >= 4 else ("⚠️" if score == 3 else "❌")
        print(f"  {symbol} {dim.replace('_', ' ').title():<25}: {score} / 5")

    print(f"\n🔍 Findings ({len(report['findings'])} total):")
    if not report["findings"]:
        print("  🎉 Zero defects or advisory findings found!")
    else:
        for f in report["findings"]:
            sev_icon = "🚨" if f["severity"] == "high" else ("⚠️" if f["severity"] == "medium" else "ℹ️")
            print(f"  {sev_icon} [{f['id']}] {f['category'].upper()} ({f['severity']}): {f['observation']}")
            print(f"     Proposed: {f['proposed_change']}")

    print(f"\n📄 Full findings written to: {out_file.relative_to(ROOT)}")
    print("=" * 68)


if __name__ == "__main__":
    main()
