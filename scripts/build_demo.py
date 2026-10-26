#!/usr/bin/env python3
"""
London Local News Video Assembly Pipeline (V8 - Broadcast Figures Edition)
Design Architecture:
- True Full-Screen 9:16 Moving Video Footage (1080x1920) across documentary scenes
- Superimposed intelligent data visualisations & figures:
  * Scene 1: 54-0 Unanimous Vote Tally HUD (Labour & Conservative cross-party figure)
  * Scene 2: Motion Mover & Seconder Leadership Quote Card
  * Scene 3: Dual Floating Demographic Figures (180+ Nationalities / 150+ Languages)
  * Scene 4: 2x2 Community Implementation Action Matrix
  * Scene 5: Clean Broadsheet Outro with strict text-wrapping & mobile safe margins
- Mathematically measured pill tags (zero text spillage on borders)
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

MARGIN_X = 70
SAFE_WIDTH = 1080 - (2 * MARGIN_X) # 940px

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

def draw_top_bar(overlay, draw, borough="WESTMINSTER", date_str="12 NOV", show_ai_badge=True, show_logo=True):
    # Top gradient vignette
    for y in range(0, 260):
        alpha = int(190 * (1 - (y / 260)))
        draw.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))

    # Clean brand wordmark
    if show_logo and os.path.exists(LOGO_WORDMARK):
        try:
            wm = Image.open(LOGO_WORDMARK).convert("RGBA")
            aspect = wm.width / wm.height
            wm = wm.resize((int(38 * aspect), 38), Image.Resampling.LANCZOS)
            overlay.paste(wm, (MARGIN_X, 75), wm)
        except Exception:
            draw.text((MARGIN_X, 75), "London Local.", font=get_font(FONT_SERIF_BOLD, 36), fill=(255, 255, 255, 255))
    else:
        draw.text((MARGIN_X, 75), "London Local.", font=get_font(FONT_SERIF_BOLD, 36), fill=(255, 255, 255, 255))

    # Dynamically measured borough tag pill (mathematically impossible to spill over)
    f_tag = get_font(FONT_SANS, 20)
    tag_text = f"{borough} • {date_str}"
    tag_text_w = draw.textlength(tag_text, font=f_tag)
    pill_w = int(tag_text_w + 44)
    pill_x2 = 1080 - MARGIN_X
    pill_x1 = pill_x2 - pill_w
    draw.rounded_rectangle([(pill_x1, 70), (pill_x2, 118)], radius=24, fill=(0, 0, 0, 180), outline=(255, 255, 255, 60), width=1)
    draw.text((pill_x1 + 22, 84), tag_text, font=f_tag, fill=(240, 240, 245))

    # AI illustrative footage badge
    if show_ai_badge:
        f_ai = get_font(FONT_SANS, 16)
        ai_text = "AI ILLUSTRATIVE FOOTAGE"
        ai_w = draw.textlength(ai_text, font=f_ai)
        draw.rounded_rectangle([(MARGIN_X, 130), (MARGIN_X + int(ai_w + 32), 168)], radius=15, fill=(0, 0, 0, 180), outline=(245, 158, 11, 200), width=1)
        draw.text((MARGIN_X + 16, 142), ai_text, font=f_ai, fill=(251, 191, 36))

def draw_bottom_vignette(draw, start_y=1050):
    for y in range(start_y, 1920):
        factor = (y - start_y) / (1920 - start_y)
        alpha = int(245 * (factor ** 1.3))
        draw.line([(0, y), (1080, y)], fill=(10, 10, 12, alpha))

# --- SCENE 1: Intelligent Vote Breakdown Figure ---
def create_scene1_overlay(out_path, show_logo=True):
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw_top_bar(overlay, draw, borough="WESTMINSTER", date_str="12 NOV", show_ai_badge=True, show_logo=show_logo)
    draw_bottom_vignette(draw, start_y=1000)

    # Superimposed Vote Figure Card (HUD)
    fig_y1 = 1120
    fig_y2 = 1290
    draw.rounded_rectangle([(MARGIN_X, fig_y1), (1080 - MARGIN_X, fig_y2)], radius=14, fill=(20, 20, 24, 210), outline=(255, 255, 255, 50), width=1)
    
    # Figure Header
    draw.text((MARGIN_X + 25, fig_y1 + 18), "COUNCIL VOTE RESULT: MOTION CARRIED", font=get_font(FONT_SANS, 19), fill=(245, 158, 11))
    draw.text((1080 - MARGIN_X - 180, fig_y1 + 18), "100% UNANIMOUS", font=get_font(FONT_SANS, 19), fill=(52, 211, 153))

    # Tally Graphic Bar
    draw.rounded_rectangle([(MARGIN_X + 25, fig_y1 + 54), (1080 - MARGIN_X - 25, fig_y1 + 64)], radius=5, fill=(45, 45, 50))
    draw.rounded_rectangle([(MARGIN_X + 25, fig_y1 + 54), (1080 - MARGIN_X - 25, fig_y1 + 64)], radius=5, fill=(52, 211, 153))

    # Dual Party Breakdown Pills
    p_w = (SAFE_WIDTH - 70) // 2
    # Labour Pill
    draw.rounded_rectangle([(MARGIN_X + 25, fig_y1 + 84), (MARGIN_X + 25 + p_w, fig_y1 + 144)], radius=8, fill=(35, 35, 42))
    draw.text((MARGIN_X + 45, fig_y1 + 94), "LABOUR", font=get_font(FONT_SANS, 18), fill=(225, 29, 72))
    draw.text((MARGIN_X + 45, fig_y1 + 118), "31 Councillors (Aye)", font=get_font(FONT_SANS, 20), fill=(230, 230, 235))

    # Conservative Pill
    cx = MARGIN_X + 25 + p_w + 20
    draw.rounded_rectangle([(cx, fig_y1 + 84), (cx + p_w, fig_y1 + 144)], radius=8, fill=(35, 35, 42))
    draw.text((cx + 20, fig_y1 + 94), "CONSERVATIVE", font=get_font(FONT_SANS, 18), fill=(37, 99, 235))
    draw.text((cx + 20, fig_y1 + 118), "23 Councillors (Aye)", font=get_font(FONT_SANS, 20), fill=(230, 230, 235))

    # Lower Third Typography
    f_h1 = get_font(FONT_SERIF_BOLD, 54)
    f_body = get_font(FONT_SANS, 28)
    draw.text((MARGIN_X, 1340), "Unanimous Vote Against\nFar-Right Extremism", font=f_h1, fill=(255, 255, 255), spacing=12)
    draw.text((MARGIN_X, 1490), "Westminster City Council has formally united across party lines\nto condemn rising anti-migrant rhetoric and protect residents.", font=f_body, fill=(215, 215, 220), spacing=8)

    draw.line([(MARGIN_X, 1680), (1080 - MARGIN_X, 1680)], fill=(255, 255, 255, 40), width=1)
    draw.text((MARGIN_X, 1715), "SOURCE: Westminster Full Council Meeting · 12 Nov 2025 · Verified Minutes", font=get_font(FONT_SANS, 20), fill=(160, 160, 165))
    overlay.save(out_path)

# --- SCENE 2: Leadership Motion & Document Figure ---
def create_scene2_overlay(out_path, show_logo=True):
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw_top_bar(overlay, draw, borough="WESTMINSTER", date_str="12 NOV", show_ai_badge=True, show_logo=show_logo)
    draw_bottom_vignette(draw, start_y=1000)

    # Superimposed Quote Figure HUD
    fig_y1 = 1120
    fig_y2 = 1350
    draw.rounded_rectangle([(MARGIN_X, fig_y1), (1080 - MARGIN_X, fig_y2)], radius=14, fill=(20, 20, 24, 215), outline=(255, 255, 255, 50), width=1)
    draw.text((MARGIN_X + 25, fig_y1 + 18), "LEADERSHIP MOTION DECLARATION", font=get_font(FONT_SANS, 19), fill=(245, 158, 11))
    
    quote_text = "\"We will not allow division or hatred to take root in Westminster. Our authority stands firmly with every targeted community.\""
    q_lines = wrap_text_to_width(draw, quote_text, get_font(FONT_SERIF, 28), SAFE_WIDTH - 50)
    qy = fig_y1 + 54
    for ql in qlines if 'qlines' in locals() else q_lines:
        draw.text((MARGIN_X + 25, qy), ql, font=get_font(FONT_SERIF, 28), fill=(245, 245, 250))
        qy += 38

    # Leader Attribution Pill
    draw.rounded_rectangle([(MARGIN_X + 25, fig_y2 - 64), (1080 - MARGIN_X - 25, fig_y2 - 18)], radius=8, fill=(35, 35, 42))
    draw.text((MARGIN_X + 45, fig_y2 - 52), "MOVED BY: Cllr Adam Hug (Council Leader) • SECONDED: Cllr Jessica Toale MP", font=get_font(FONT_SANS, 18), fill=(210, 210, 215))

    # Lower Third Typography
    f_h1 = get_font(FONT_SERIF_BOLD, 52)
    f_body = get_font(FONT_SANS, 28)
    draw.text((MARGIN_X, 1390), "New Community Equality\nStrategy Mandated", font=f_h1, fill=(255, 255, 255), spacing=12)
    draw.text((MARGIN_X, 1525), "Motion commits authority to establish rapid civic protections\nand reinforce multi-faith community cohesion programs.", font=f_body, fill=(215, 215, 220), spacing=8)

    draw.line([(MARGIN_X, 1680), (1080 - MARGIN_X, 1680)], fill=(255, 255, 255, 40), width=1)
    draw.text((MARGIN_X, 1715), "SOURCE: Agenda Item 7 · Council Leader & Cabinet Records", font=get_font(FONT_SANS, 20), fill=(160, 160, 165))
    overlay.save(out_path)

# --- SCENE 3: Dual Floating Demographic Figures ---
def create_scene3_overlay(out_path, show_logo=True):
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw_top_bar(overlay, draw, borough="WESTMINSTER", date_str="12 NOV", show_ai_badge=True, show_logo=show_logo)
    draw_bottom_vignette(draw, start_y=1000)

    # Superimposed Dual Demographic Figure HUD
    fig_y1 = 1120
    fig_y2 = 1320
    card_w = (SAFE_WIDTH - 24) // 2
    
    # Figure Card 1: Nationalities
    draw.rounded_rectangle([(MARGIN_X, fig_y1), (MARGIN_X + card_w, fig_y2)], radius=14, fill=(18, 18, 22, 225), outline=(255, 255, 255, 50), width=1)
    draw.text((MARGIN_X + 28, fig_y1 + 18), "180+", font=get_font(FONT_SERIF_BOLD, 74), fill=(255, 255, 255))
    draw.text((MARGIN_X + 28, fig_y1 + 105), "Nationalities\nRepresented", font=get_font(FONT_SANS, 24), fill=(200, 200, 205), spacing=6)

    # Figure Card 2: Languages
    c2_x = MARGIN_X + card_w + 24
    draw.rounded_rectangle([(c2_x, fig_y1), (c2_x + card_w, fig_y2)], radius=14, fill=(18, 18, 22, 225), outline=(255, 255, 255, 50), width=1)
    draw.text((c2_x + 28, fig_y1 + 18), "150+", font=get_font(FONT_SERIF_BOLD, 74), fill=(255, 255, 255))
    draw.text((c2_x + 28, fig_y1 + 105), "Languages Spoken\nAcross Borough", font=get_font(FONT_SANS, 24), fill=(200, 200, 205), spacing=6)

    # Lower Third Typography
    f_h1 = get_font(FONT_SERIF_BOLD, 52)
    f_body = get_font(FONT_SANS, 28)
    draw.text((MARGIN_X, 1370), "A Diverse Global Community\nStanding Together", font=f_h1, fill=(255, 255, 255), spacing=12)
    draw.text((MARGIN_X, 1515), "Council leadership emphasised that minority communities\nmust not be scapegoated for wider economic pressures.", font=f_body, fill=(215, 215, 220), spacing=8)

    draw.line([(MARGIN_X, 1680), (1080 - MARGIN_X, 1680)], fill=(255, 255, 255, 40), width=1)
    draw.text((MARGIN_X, 1715), "SOURCE: Victoria Street & Westminster Area · Census Demographic Records", font=get_font(FONT_SANS, 20), fill=(160, 160, 165))
    overlay.save(out_path)

# --- SCENE 4: 2x2 Implementation Action Matrix ---
def create_scene4_overlay(out_path, show_logo=True):
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw_top_bar(overlay, draw, borough="WESTMINSTER", date_str="12 NOV", show_ai_badge=True, show_logo=show_logo)
    draw_bottom_vignette(draw, start_y=950)

    # Superimposed 2x2 Action Matrix Figure
    grid_y = 1060
    gw = (SAFE_WIDTH - 20) // 2
    gh = 110

    pillars = [
        ("01 / FAITH LEADERS", "Interfaith cultural unity & mutual security", MARGIN_X, grid_y),
        ("02 / YOUTH VOICES", "Civic education countering online hate", MARGIN_X + gw + 20, grid_y),
        ("03 / LOCAL RESIDENTS", "Grassroots reporting and council liaison", MARGIN_X, grid_y + gh + 16),
        ("04 / MET POLICE", "Swift investigation & victim care support", MARGIN_X + gw + 20, grid_y + gh + 16),
    ]

    for title, desc, px, py in pillars:
        draw.rounded_rectangle([(px, py), (px + gw, py + gh)], radius=12, fill=(20, 20, 24, 220), outline=(255, 255, 255, 45), width=1)
        draw.text((px + 18, py + 16), title, font=get_font(FONT_SANS, 18), fill=(245, 158, 11))
        d_lines = wrap_text_to_width(draw, desc, get_font(FONT_SANS, 20), gw - 36)
        dy = py + 46
        for dl in d_lines:
            draw.text((px + 18, dy), dl, font=get_font(FONT_SANS, 20), fill=(225, 225, 230))
            dy += 26

    # Lower Third Typography
    f_h1 = get_font(FONT_SERIF_BOLD, 52)
    f_body = get_font(FONT_SANS, 28)
    draw.text((MARGIN_X, 1340), "Cross-Community\nWorking Group Mobilised", font=f_h1, fill=(255, 255, 255), spacing=12)
    draw.text((MARGIN_X, 1480), "Grassroots coalition established to track incidents in real time\nand coordinate direct safety interventions across the borough.", font=f_body, fill=(215, 215, 220), spacing=8)

    draw.line([(MARGIN_X, 1680), (1080 - MARGIN_X, 1680)], fill=(255, 255, 255, 40), width=1)
    draw.text((MARGIN_X, 1715), "SOURCE: Westminster City Hall · Cross-Community Directorate Commitments", font=get_font(FONT_SANS, 20), fill=(160, 160, 165))
    overlay.save(out_path)

# --- SCENE 5: Clean Broadsheet Outro (Guaranteed Zero Spillage) ---
def create_outro_card(out_path, show_logo=True):
    img = Image.new("RGB", (1080, 1920), (10, 10, 12))
    draw = ImageDraw.Draw(img)

    # Subtle gradient background
    for y in range(0, 1920):
        val = int(12 + (y / 1920) * 16)
        draw.line([(0, y), (1080, y)], fill=(val, val, val + 2))

    # Top brand wordmark
    ox = MARGIN_X + 20
    if show_logo and os.path.exists(LOGO_WORDMARK):
        try:
            wm = Image.open(LOGO_WORDMARK).convert("RGBA")
            aspect = wm.width / wm.height
            wm = wm.resize((int(64 * aspect), 64), Image.Resampling.LANCZOS)
            img.paste(wm, (ox, 480), wm)
        except Exception:
            draw.text((ox, 480), "London Local.", font=get_font(FONT_SERIF_BOLD, 68), fill=(255, 255, 255))
    else:
        draw.text((ox, 480), "London Local.", font=get_font(FONT_SERIF_BOLD, 68), fill=(255, 255, 255))

    draw.text((ox, 580), "Independent civic intelligence across London's 33 councils.", font=get_font(FONT_SANS, 28), fill=(185, 185, 190))
    draw.line([(ox, 650), (1080 - ox, 650)], fill=(255, 255, 255, 40), width=1)

    draw.text((ox, 710), "VERIFIED SOURCE DOCUMENTS ON RECORD", font=get_font(FONT_SANS, 22), fill=(245, 158, 11))
    
    docs = [
        "Westminster City Council Motion: Standing Against Hate (12 Nov 2025)",
        "Leader's Official Declaration: Cllr Adam Hug & Cllr Jessica Toale MP",
        "Community Equality Strategy: Verified Full Council Minutes & Order Paper"
    ]
    
    dy = 780
    f_doc = get_font(FONT_SERIF, 30)
    for d in docs:
        d_lines = wrap_text_to_width(draw, f"• {d}", f_doc, 1080 - (2 * ox))
        for dl in d_lines:
            draw.text((ox, dy), dl, font=f_doc, fill=(235, 235, 240))
            dy += 44
        dy += 22

    # Clean action button safely elevated above mobile player controls
    by = 1200
    pill_h = 130
    draw.rounded_rectangle([(ox, by), (1080 - ox, by + pill_h)], radius=16, fill=(255, 255, 255))
    f_kicker = get_font(FONT_SANS, 20)
    f_url = get_font(FONT_SERIF_BOLD, 42)
    
    kicker_txt = "READ THE FULL VERIFIED RECORD"
    k_w = draw.textlength(kicker_txt, font=f_kicker)
    draw.text(((1080 - k_w) // 2, by + 28), kicker_txt, font=f_kicker, fill=(110, 110, 115))
    
    url_txt = "londonlocal.news"
    u_w = draw.textlength(url_txt, font=f_url)
    draw.text(((1080 - u_w) // 2, by + 62), url_txt, font=f_url, fill=(12, 12, 14))

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

    print("=== 1. Synthesising / Loading BBC Broadcast Audio ===")
    timings = generate_audio()

    print("\n=== 2. Creating Intelligent Figures & Broadcast Overlays ===")
    ov1 = os.path.join(BUILD_DIR, "ov_scene1.png")
    ov2 = os.path.join(BUILD_DIR, "ov_scene2.png")
    ov3 = os.path.join(BUILD_DIR, "ov_scene3.png")
    ov4 = os.path.join(BUILD_DIR, "ov_scene4.png")
    outro_img = os.path.join(BUILD_DIR, "outro_card.png")

    create_scene1_overlay(ov1, show_logo=show_logo)
    create_scene2_overlay(ov2, show_logo=show_logo)
    create_scene3_overlay(ov3, show_logo=show_logo)
    create_scene4_overlay(ov4, show_logo=show_logo)
    create_outro_card(outro_img, show_logo=show_logo)
    print("All broadcast overlays & figures generated.")

    print("\n=== 3. Encoding Full-Screen Moving Video Segments ===")
    segment_files = []

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
            print(f"Segment {num} (Full-Screen Live Video + Figure) encoded ({pad_dur:.2f}s)")
        else:
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
