#!/usr/bin/env python3
"""
London Local Newsroom B-Roll Matcher & Quartet Selector
========================================================
Matches any London Local news story (by title, borough, storyType, and article text)
against `assets/generative/broll_catalog.json` to select 4 visually distinct,
non-repeating, topic-grounded 9:16 35mm documentary B-roll clips for Scenes 1-4:
  - Scene 1 (Hook): High-impact topic anchor (`cropMode: "full"`)
  - Scene 2 (Receipt / Quote): Institutional/civic/contextual backdrop (`cropMode: "pan_zoom"` or `"full"`)
  - Scene 3 (Key Points): Street-level / human / service impact (`cropMode: "full"`)
  - Scene 4 (Facts & Figures): Secondary context / infrastructure / B-cam (`cropMode: "architectural_upper"` or `"full"`)
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parents[1]
CATALOG_PATH = BASE_DIR / "assets" / "generative" / "broll_catalog.json"

STORY_TYPE_TO_CATEGORIES = {
    "transport": ["transport", "active_travel", "highways"],
    "housing": ["housing", "planning_parks"],
    "environment_schools": ["environment_waste", "schools_youth", "active_travel", "planning_parks"],
    "council_decision": ["civic", "finance_governance", "high_street", "health_care", "safety_justice"],
}

LONDON_BOROUGH_TERMS = {
    "barking", "dagenham", "barnet", "bexley", "brent", "bromley", "camden",
    "croydon", "ealing", "enfield", "greenwich", "hackney", "hammersmith",
    "fulham", "haringey", "harrow", "havering", "hillingdon", "hounslow",
    "islington", "kensington", "chelsea", "kingston", "lambeth", "lewisham",
    "merton", "newham", "redbridge", "richmond", "southwark", "sutton",
    "tower hamlets", "waltham forest", "wandsworth", "westminster",
}


def load_catalog() -> List[Dict[str, Any]]:
    if not CATALOG_PATH.exists():
        return []
    with open(CATALOG_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("clips", [])


def _kw_matches(kw_low: str, text_low: str) -> bool:
    """Word-boundary aware keyword matcher with plural/stem tolerance for longer words."""
    if not kw_low or not text_low:
        return False
    # Exact word/phrase boundary match first
    if re.search(rf"\b{re.escape(kw_low)}\b", text_low):
        return True
    # For single words >= 5 chars, allow singular/plural/stem prefix matching at word boundaries
    if " " not in kw_low and len(kw_low) >= 5:
        stem = kw_low.rstrip("s")
        if len(stem) >= 4 and re.search(rf"\b{re.escape(stem)}[a-z]*\b", text_low):
            return True
    return False


def score_clip_for_story(
    clip: Dict[str, Any],
    title: str,
    borough: str,
    story_type: str,
    body_text: str = "",
    target_scene: int = 1,
) -> float:
    score = 0.0
    t_low = title.lower()
    b_low = borough.lower()
    full_text = f"{t_low} {body_text.lower()}"
    subtopic_low = str(clip.get("subtopic", "")).lower()

    topical_matches = 0
    # 1. Keyword matches in title (high weight) and body (medium weight)
    for kw in clip.get("keywords", []):
        kw_low = kw.lower().strip()
        is_borough_kw = kw_low in LONDON_BOROUGH_TERMS
        if _kw_matches(kw_low, t_low):
            if is_borough_kw:
                score += 1.5
            else:
                score += 9.0
                topical_matches += 1
        elif _kw_matches(kw_low, full_text):
            if is_borough_kw:
                score += 1.0
            else:
                score += 3.5
                topical_matches += 1
        elif is_borough_kw and _kw_matches(kw_low, b_low):
            score += 1.0

    # Also check words in clip subtopic against title/body
    for w in re.findall(r"[a-z]{5,}", subtopic_low):
        if w not in LONDON_BOROUGH_TERMS and _kw_matches(w, t_low):
            score += 3.0
            topical_matches += 1

    # 2. Category alignment with story_type
    preferred_cats = STORY_TYPE_TO_CATEGORIES.get(story_type, ["civic"])
    clip_cat = clip.get("category", "")
    if clip_cat in preferred_cats:
        score += 4.0
    elif topical_matches == 0:
        # Penalise off-category clips that only matched a borough name
        score -= 4.0

    # 3. Scene suitability
    if target_scene in clip.get("recommendedScenes", [1, 2, 3, 4]):
        score += 3.0
    if target_scene == 2 and clip_cat in ("civic", "finance_governance"):
        score += 5.0

    # 4. Deterministic tie-breaker hash so different stories spread across the library
    tie_hash = int(hashlib.md5(f"{title}:{clip.get('id', '')}:{target_scene}".encode("utf-8")).hexdigest()[:6], 16)
    score += (tie_hash % 1000) / 1000.0

    return score


def score_clip_for_keypoint(
    clip: Dict[str, Any],
    kp_text: str,
    borough: str,
    story_title: str = "",
) -> float:
    """Scores a clip specifically against an individual Scene 3 key point (or pair of points)."""
    score = 0.0
    kp_low = kp_text.lower()
    t_low = story_title.lower()
    b_low = borough.lower()
    subtopic_low = str(clip.get("subtopic", "")).lower()
    path_low = str(clip.get("path", "")).lower()

    # Strongly avoid using another borough's named clip (e.g. camden_*, southwark_*, westminster_*)
    # unless this story is for that borough
    for b_name in ("camden", "southwark", "westminster", "d7_"):
        if b_name in path_low and b_name.rstrip("_") not in b_low:
            score -= 15.0

    kp_hits = 0
    for kw in clip.get("keywords", []):
        kw_low = kw.lower().strip()
        is_borough_kw = kw_low in LONDON_BOROUGH_TERMS
        if _kw_matches(kw_low, kp_low):
            if is_borough_kw:
                score += 1.5
            else:
                score += 12.0
                kp_hits += 1
        elif not is_borough_kw and _kw_matches(kw_low, t_low):
            score += 2.5

    for w in re.findall(r"[a-z]{5,}", subtopic_low):
        if w not in LONDON_BOROUGH_TERMS and _kw_matches(w, kp_low):
            score += 4.5
            kp_hits += 1

    if 3 in clip.get("recommendedScenes", [1, 2, 3, 4]):
        score += 2.0

    if kp_hits == 0:
        score -= 3.0

    tie_hash = int(hashlib.md5(f"{kp_text}:{clip.get('id', '')}".encode("utf-8")).hexdigest()[:6], 16)
    score += (tie_hash % 1000) / 1000.0
    return score


def select_scene3_cutaway_pair(
    spec: Dict[str, Any],
    catalog: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[str, str]:
    """
    Selects two distinct, topic-grounded 9:16 B-roll clips `(shot_a, shot_b)` for Scene 3:
      - `shot_a` visually illustrates Point 1 (`keyPoints[0]`) during the first beat (0..38%).
      - `shot_b` visually illustrates Points 2 & 3 (`keyPoints[1:]`) during the cutaway (38..100%).
    Avoids reusing clips already assigned to Scenes 1, 2, or 4 in `spec`.
    """
    clips = catalog if catalog is not None else load_catalog()
    borough = str(spec.get("borough", "London"))
    title = str(spec.get("storyTitle") or spec.get("headline") or "")
    kps = spec.get("keyPoints", [])

    p1_text = f"{kps[0][0]} {kps[0][1]}" if len(kps) >= 1 and len(kps[0]) >= 2 else title
    p23_parts = []
    for kp in kps[1:3]:
        if isinstance(kp, (list, tuple)) and len(kp) >= 2:
            p23_parts.append(f"{kp[0]} {kp[1]}")
    p23_text = " ".join(p23_parts) if p23_parts else title

    used_other_scenes = set()
    s3_current = ""
    for sc in spec.get("timeline", []):
        src = sc.get("visualAsset", {}).get("source", "")
        if not src:
            continue
        if sc.get("sceneNumber") == 3:
            s3_current = src
        else:
            used_other_scenes.add(src)

    avail = [c for c in clips if c.get("path") not in used_other_scenes and (BASE_DIR / c.get("path", "")).exists()]
    if not avail:
        avail = [c for c in clips if (BASE_DIR / c.get("path", "")).exists()]

    if not avail:
        fallback = s3_current or "assets/generative/westminster_street_bg_video.mp4"
        return fallback, fallback

    scored_a = sorted(
        avail,
        key=lambda c: score_clip_for_keypoint(c, p1_text, borough, title),
        reverse=True,
    )
    shot_a_clip = scored_a[0]
    shot_a = shot_a_clip["path"]

    # If the spec already has a bespoke batch_30 Scene 3 clip (`story_<id>_s3.mp4`) and Shot A didn't find a strong match,
    # keep the bespoke clip as Shot A and pick Shot B from the 140-clip library for Points 2 & 3
    if s3_current and "story_" in s3_current and (BASE_DIR / s3_current).exists():
        top_score_a = score_clip_for_keypoint(shot_a_clip, p1_text, borough, title)
        if top_score_a < 10.0:
            shot_a = s3_current

    avail_b = [c for c in avail if c.get("path") != shot_a]
    if not avail_b:
        avail_b = avail

    scored_b = sorted(
        avail_b,
        key=lambda c: score_clip_for_keypoint(c, p23_text, borough, title),
        reverse=True,
    )
    shot_b = scored_b[0]["path"]
    return shot_a, shot_b


def select_broll_quartet(
    title: str,
    borough: str = "London",
    story_type: str = "council_decision",
    body_text: str = "",
    catalog: Optional[List[Dict[str, Any]]] = None,
) -> List[str]:
    """Returns 4 distinct relative paths (`assets/generative/*.mp4`) for Scenes 1, 2, 3, 4."""
    clips = catalog if catalog is not None else load_catalog()
    if not clips:
        return [
            "assets/generative/westminster_street_bg_video.mp4",
            "assets/generative/westminster_civic_omni.mp4",
            "assets/generative/d7_bus_omni.mp4",
            "assets/generative/southwark_civic_omni.mp4",
        ]

    used_paths = set()
    chosen: List[str] = []

    for scene_num in (1, 2, 3, 4):
        candidates = [c for c in clips if c["path"] not in used_paths]
        if not candidates:
            candidates = list(clips)

        # For Scene 2, strongly prefer civic or institutional backdrops unless a specific receipt match exists
        scored = sorted(
            candidates,
            key=lambda c: score_clip_for_story(c, title, borough, story_type, body_text, target_scene=scene_num),
            reverse=True,
        )
        best = scored[0]
        chosen.append(best["path"])
        used_paths.add(best["path"])

    return chosen


if __name__ == "__main__":
    cat = load_catalog()
    print(f"Loaded {len(cat)} clips from {CATALOG_PATH}")
    sample_stories = [
        ("Hillingdon Council approves 15% rise in most fees and charges, including parking", "Hillingdon", "council_decision"),
        ("Tower Hamlets Council to acquire Marsh Wall properties for 180 new temporary homes", "Tower Hamlets", "housing"),
        ("Central Line noise pollution angers Kensington and Chelsea residents", "Kensington and Chelsea", "transport"),
        ("Barnet Council declares gambling harms emergency and pledges action", "Barnet", "council_decision"),
        ("Croydon Youth Justice Plan lacks detailed Stop and Search data for children", "Croydon", "council_decision"),
    ]
    for title, bor, st in sample_stories:
        q = select_broll_quartet(title, bor, st, catalog=cat)
        print(f"\n[{bor}] {title}:")
        for idx, p in enumerate(q, 1):
            print(f"  Scene {idx}: {p}")
