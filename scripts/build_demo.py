#!/usr/bin/env python3
"""
London Local News Video Assembly Pipeline (V7 - Full-Screen Broadcast Edition)
Design Architecture:
- True Full-Screen 9:16 Moving Video Footage (1080x1920) across documentary scenes
- Elegant broadcast lower-thirds with subtle cinematic gradient vignette
- Zero opaque blocking cards, zero overlapping borders or conflicting boxes
- Full visibility of live generated footage (Council steps & London double-decker bus)
- BBC Radio 4 style broadcast voiceover (en-GB-SoniaNeural)
"""

import json
import os
import subprocess
import argparse
import time
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC_PATH = os.path.join(BASE_DIR, "specs/4178-westminster-extremism.json")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
BRANDING_DIR = os.path.join(ASSETS_DIR, "branding")
GENERATIVE_DIR = os.path.join(ASSETS_DIR, "generative")
BUILD_DIR = os.path.join(BASE_DIR, "build")
AUDIO_DIR = os.path.join(ASSETS_DIR, "audio")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Moving Video Assets
VIDEO_STEPS = os.path.join(GENERATIVE_DIR, "gemini_generated_video_535e3482.mp4")
VIDEO_BUS = os.path.join(GENERATIVE_DIR, "gemini_generated_video_d308c8b8.mp4")
LOGO_WORDMARK = os.path.join(BRANDING_DIR, "london-local-wordmark.png")

SERIF_BOLD_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "/Library/Fonts/Georgia Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
]
SERIF_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/Library/Fonts/Georgia.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
]
SANS_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

def resolve_font_path(candidates):
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

FONT_SERIF_BOLD = resolve_font_path(SERIF_BOLD_CANDIDATES)
FONT_SERIF = resolve_font_path(SERIF_CANDIDATES)
FONT_SANS = resolve_font_path(SANS_CANDIDATES)

def get_font(path, size):
    if path and os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    try:
        return ImageFont.truetype("LiberationSans-Regular.ttf", size)
    except Exception:
        return ImageFont.load_default()

def wrap_text_to_width(draw, text, font, max_width):
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            if draw.textlength(test_line, font=font) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
    return lines

def create_broadcast_overlay(out_path, kicker, headline, body_text, citation, show_ai_badge=True, show_logo=True):
    """Generates a broadcast-grade transparent PNG overlay with zero opaque blocking cards."""
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. Subtle top gradient vignette for brand legibility
    for y in range(0, 240):
        alpha = int(180 * (1 - (y / 240)))
        draw.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))

    # Top brand header
    if show_logo and os.path.exists(LOGO_WORDMARK):
        try:
            wm = Image.open(LOGO_WORDMARK).convert("RGBA")
            aspect = wm.width / wm.height
            wm = wm.resize((int(38 * aspect), 38), Image.Resampling.LANCZOS)
            overlay.paste(wm, (70, 75), wm)
        except Exception:
            draw.text((70, 75), "London Local.", font=get_font(FONT_SERIF_BOLD, 36), fill=(255, 255, 255, 255))
    else:
        draw.text((70, 75), "London Local.", font=get_font(FONT_SERIF_BOLD, 36), fill=(255, 255, 255, 255))

    # Top right borough tag
    f_tag = get_font(FONT_SANS, 20)
    draw.rounded_rectangle([(1080 - 70 - 240, 70), (1080 - 70, 118)], radius=20, fill=(0, 0, 0, 160), outline=(255, 255, 255, 50), width=1)
    draw.text((1080 - 70 - 220, 84), "WESTMINSTER • 12 NOV", font=f_tag, fill=(230, 230, 235))

    # AI illustrative badge
    if show_ai_badge:
        draw.rounded_rectangle([(70, 130), (70 + 260, 168)], radius=15, fill=(0, 0, 0, 180), outline=(245, 158, 11, 200), width=1)
        draw.text((88, 142), "AI ILLUSTRATIVE FOOTAGE", font=get_font(FONT_SANS, 16), fill=(251, 191, 36))

    # 2. Bottom deep cinematic gradient (y: 1100 to 1920)
    for y in range(1100, 1920):
        factor = (y - 1100) / (1920 - 1100)
        alpha = int(240 * (factor ** 1.3))
        draw.line([(0, y), (1080, y)], fill=(10, 10, 12, alpha))

    # 3. Clean broadcast lower-third typography (940px safe width)
    f_kicker = get_font(FONT_SANS, 22)
    f_h1 = get_font(FONT_SERIF_BOLD, 58)
    f_body = get_font(FONT_SANS, 28)
    f_meta = get_font(FONT_SANS, 20)

    # Kicker
    draw.text((70, 1360), kicker.upper(), font=f_kicker, fill=(245, 158, 11))

    # Headline
    h1_lines = wrap_text_to_width(draw, headline, f_h1, 940)
    hy = 1410
    for hl in h1_lines:
        draw.text((70, hy), hl, font=f_h1, fill=(255, 255, 255))
        hy += 68

    # Body
    by = hy + 20
    b_lines = wrap_text_to_width(draw, body_text, f_body, 940)
    for bl in b_lines:
        draw.text((70, by), bl, font=f_body, fill=(220, 220, 225))
        by += 40

    # Separator line
    draw.line([(70, 1700), (1080 - 70, 1700)], fill=(255, 255, 255, 45), width=1)

    # Citation footer
    draw.text((70, 1730), citation, font=f_meta, fill=(160, 160, 165))

    overlay.save(out_path)

def create_outro_card(out_path, show_logo=True):
    """Full-screen broadsheet outro card."""
    img = Image.new("RGB", (1080, 1920), (10, 10, 12))
    draw = ImageDraw.Draw(img)

    for y in range(0, 1920):
        val = int(10 + (y / 1920) * 15)
        draw.line([(0, y), (1080, y)], fill=(val, val, val + 2))

    if show_logo and os.path.exists(LOGO_WORDMARK):
        wm = Image.open(LOGO_WORDMARK).convert("RGBA")
        aspect = wm.width / wm.height
        wm = wm.resize((int(70 * aspect), 70), Image.Resampling.LANCZOS)
        img.paste(wm, (120, 680), wm)
    else:
        draw.text((120, 680), "London Local.", font=get_font(FONT_SERIF_BOLD, 74), fill=(255, 255, 255))

    draw.text((120, 780), "Independent civic intelligence across London's 33 councils.", font=get_font(FONT_SANS, 30), fill=(180, 180, 185))

    draw.line([(120, 860), (1080 - 120, 860)], fill=(255, 255, 255, 40), width=1)

    draw.text((120, 930), "SOURCE DOCUMENTS ON RECORD", font=get_font(FONT_SANS, 24), fill=(245, 158, 11))
    
    docs = [
        "• Westminster City Council Motion: Standing Against Hate (12 Nov 2025)",
        "• Leader's Declaration: Cllr Adam Hug & Jessica Toale MP",
        "• Community Equality Strategy: Verified Implementation Minutes"
    ]
    dy = 1000
    for d in docs:
        draw.text((120, dy), d, font=get_font(FONT_SERIF, 32), fill=(230, 230, 235))
        dy += 60

    draw.rounded_rectangle([(120, 1400), (1080 - 120, 1520)], radius=12, fill=(255, 255, 255))
    draw.text((360, 1445), "londonlocal.news", font=get_font(FONT_SERIF_BOLD, 46), fill=(12, 12, 14))

    img.save(out_path)

def generate_audio(voice="en-GB-SoniaNeural", force_refresh=False):
    os.makedirs(AUDIO_DIR, exist_ok=True)
    with open(SPEC_PATH) as f:
        spec = json.load(f)

    timings = []
    for scene in spec["timeline"]:
        num = scene["sceneNumber"]
        text = scene["voiceoverText"]
        out_mp3 = os.path.join(AUDIO_DIR, f"scene_{num}.mp3")
        
        if not force_refresh and os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 1000:
            success = True
        else:
            success = False
            for attempt in range(3):
                try:
                    cmd = ["edge-tts", "--voice", voice, "--text", text, "--write-media", out_mp3]
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    success = True
                    break
                except Exception:
                    time.sleep(1.5)
            
            if not success:
                try:
                    cmd = ["edge-tts", "--voice", "en-GB-LibbyNeural", "--text", text, "--write-media", out_mp3]
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    success = True
                except Exception:
                    pass

            if not success and (not os.path.exists(out_mp3) or os.path.getsize(out_mp3) < 1000):
                dur_target = str(scene.get("durationSeconds", 7.0))
                cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", dur_target, "-c:a", "libmp3lame", "-b:a", "48k", out_mp3]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        probe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", out_mp3
        ]
        res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        dur = float(res.stdout.strip())
        timings.append((num, dur, out_mp3))

    return timings

def render_video(show_logo=True):
    os.makedirs(BUILD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)

    print("=== 1. Synthesising / Verifying BBC Broadcast Audio ===")
    timings = generate_audio()

    print("\n=== 2. Creating Clean Broadcast Overlays (Zero Obscuring Cards) ===")
    
    # Scene 1: Council Steps Moving Video + Overlay
    ov1 = os.path.join(BUILD_DIR, "ov_scene1.png")
    create_broadcast_overlay(
        ov1,
        kicker="Council Chamber Decision",
        headline="Unanimous Vote Against\nFar-Right Extremism",
        body_text="Westminster City Council has formally passed a cross-party motion committing to protect targeted communities.",
        citation="SOURCE: Full Council Meeting · 12 Nov 2025 · Verified Minutes",
        show_ai_badge=True,
        show_logo=show_logo
    )

    # Scene 2: Council Steps Moving Video + Leader Quote Overlay
    ov2 = os.path.join(BUILD_DIR, "ov_scene2.png")
    create_broadcast_overlay(
        ov2,
        kicker="Council Leadership",
        headline="\"We Will Not Allow Division\nTo Take Root in Westminster\"",
        body_text="Leader Cllr Adam Hug commits the authority to deliver a brand new Community Equality Strategy.",
        citation="SOURCE: Agenda Item 7 · Cllr Adam Hug (Labour) & Cllr Jessica Toale MP",
        show_ai_badge=True,
        show_logo=show_logo
    )

    # Scene 3: Red London Bus Moving Video + Demographics Overlay
    ov3 = os.path.join(BUILD_DIR, "ov_scene3.png")
    create_broadcast_overlay(
        ov3,
        kicker="Westminster Demographics",
        headline="180+ Nationalities\n150+ Languages Spoken",
        body_text="Council leaders emphasised that migrant and minority communities must not be scapegoated for wider economic pressures.",
        citation="SOURCE: Victoria Street & Westminster Area · Official Equality Statistics",
        show_ai_badge=True,
        show_logo=show_logo
    )

    # Scene 4: Working Group Implementation (Action Plan)
    ov4 = os.path.join(BUILD_DIR, "ov_scene4.png")
    create_broadcast_overlay(
        ov4,
        kicker="Community Action Plan",
        headline="Cross-Community\nWorking Group Established",
        body_text="Residents, faith leaders, youth voices, and police unite to support victims and protect community cohesion.",
        citation="SOURCE: Westminster City Hall · Cross-Community Directorate",
        show_ai_badge=True,
        show_logo=show_logo
    )

    # Scene 5: Outro Card
    outro_img = os.path.join(BUILD_DIR, "outro_card.png")
    create_outro_card(outro_img, show_logo=show_logo)

    print("All broadcast overlays created.")

    print("\n=== 3. Encoding Full-Screen Moving Video Segments ===")
    segment_files = []

    # Map scenes to live moving videos
    scene_video_map = {
        1: (VIDEO_STEPS, ov1),
        2: (VIDEO_STEPS, ov2),
        3: (VIDEO_BUS, ov3),
        4: (VIDEO_STEPS, ov4),
    }

    for i, (num, dur, mp3_path) in enumerate(timings):
        seg_out = os.path.join(BUILD_DIR, f"seg_{num}.mp4")
        pad_dur = dur + 0.35

        if num in scene_video_map and os.path.exists(scene_video_map[num][0]):
            video_src, overlay_png = scene_video_map[num]
            # Real moving video footage running full-screen with clean broadcast lower third!
            cmd = [
                "ffmpeg", "-y",
                "-stream_loop", "-1", "-i", video_src,
                "-i", overlay_png,
                "-i", mp3_path,
                "-filter_complex", "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[vid];[vid][1:v]overlay=0:0[outv]",
                "-map", "[outv]", "-map", "2:a",
                "-c:v", "libx264", "-t", str(pad_dur),
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                seg_out
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            segment_files.append(seg_out)
            print(f"Segment {num} (Full-Screen Live Video) encoded ({pad_dur:.2f}s)")
        else:
            # Outro card with subtle Ken Burns drift
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", outro_img,
                "-i", mp3_path,
                "-filter_complex", "scale=1080:1920,zoompan=z='min(zoom+0.0003,1.03)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30",
                "-c:v", "libx264", "-t", str(pad_dur),
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                seg_out
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            segment_files.append(seg_out)
            print(f"Segment {num} (Outro Broadsheet) encoded ({pad_dur:.2f}s)")

    print("\n=== 4. Assembling Master Broadcast 9:16 Video ===")
    concat_list = os.path.join(BUILD_DIR, "concat_list.txt")
    with open(concat_list, "w") as f:
        for seg in segment_files:
            f.write(f"file '{seg}'\n")

    master_output = os.path.join(OUTPUT_DIR, "sample_video_4178_editorial.mp4")
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        master_output
    ]
    subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
        "-of", "default=noprint_wrappers=1", master_output
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    print(f"\n Master Broadcast Video Rendered: {master_output}")
    print(res.stdout)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--show-authorised-logo", action="store_true", default=True)
    args = parser.parse_args()
    render_video(show_logo=args.show_authorised_logo)
