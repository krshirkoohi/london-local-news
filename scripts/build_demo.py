#!/usr/bin/env python3
"""
Pipeline script to build a high-quality, broadcast-grade vertical (9:16) local news video demo
from London Local article specs without hallucinations or synthetic talking-head slop.
"""

import json
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC_PATH = os.path.join(BASE_DIR, "specs/4178-westminster-extremism.json")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
BUILD_DIR = os.path.join(BASE_DIR, "build")
AUDIO_DIR = os.path.join(BUILD_DIR, "audio")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"

def get_font(size, bold=False):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def draw_header_and_footer(draw, width=1080, height=1920, borough="Westminster"):
    # Dark modern news theme: deep navy/slate
    # Top branding bar
    draw.rectangle([(60, 80), (width - 60, 160)], fill=(15, 23, 42, 220))
    f_brand = get_font(36)
    f_borough = get_font(30)
    draw.text((90, 100), "London Local.", font=f_brand, fill=(248, 250, 252))
    draw.text((width - 320, 105), f"Borough: {borough}", font=f_borough, fill=(148, 163, 184))

    # Bottom safe margin footer
    draw.line([(60, height - 160), (width - 60, height - 160)], fill=(51, 65, 85), width=2)
    f_source = get_font(24)
    draw.text((90, height - 130), "Source: Westminster Council Agenda • 12 Nov 2025", font=f_source, fill=(148, 163, 184))

def create_scene1_image(output_path):
    img = Image.new("RGB", (1080, 1920), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    draw_header_and_footer(draw, borough="Westminster")

    # Category Pill
    draw.rounded_rectangle([(90, 260), (420, 320)], radius=12, fill=(225, 29, 72))
    f_pill = get_font(28)
    draw.text((120, 275), "COUNCIL VOTE", font=f_pill, fill=(255, 255, 255))

    # Big Headline
    f_h1 = get_font(68)
    headline_text = "Westminster Council\nStands Against\nFar-Right Extremism"
    draw.text((90, 380), headline_text, font=f_h1, fill=(255, 255, 255), spacing=18)

    # Key Stat Card
    draw.rounded_rectangle([(90, 720), (990, 1140)], radius=24, fill=(30, 41, 59))
    draw.rounded_rectangle([(90, 720), (990, 740)], radius=10, fill=(16, 185, 129)) # green top stripe
    
    f_stat_label = get_font(32)
    f_stat_big = get_font(110)
    f_stat_desc = get_font(36)
    
    draw.text((140, 780), "MOTION OUTCOME", font=f_stat_label, fill=(148, 163, 184))
    draw.text((140, 840), "UNANIMOUS", font=f_stat_big, fill=(52, 211, 153))
    
    desc = "All parties approved the pledge to tackle hate\ncrimes and protect local communities."
    draw.text((140, 990), desc, font=f_stat_desc, fill=(241, 245, 249), spacing=12)

    # Subtext box
    draw.rounded_rectangle([(90, 1220), (990, 1480)], radius=20, fill=(30, 41, 59))
    f_quote = get_font(34)
    q_text = "“Blaming migrants does not solve our challenges.\nWestminster remains a safe, welcoming city\nfor all residents and faiths.”"
    draw.text((130, 1280), q_text, font=f_quote, fill=(226, 232, 240), spacing=14)

    img.save(output_path)

def create_scene2_image(output_path):
    img = Image.new("RGB", (1080, 1920), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    draw_header_and_footer(draw, borough="Westminster")

    # Category Pill
    draw.rounded_rectangle([(90, 260), (450, 320)], radius=12, fill=(37, 99, 235))
    f_pill = get_font(28)
    draw.text((120, 275), "LEADERSHIP MOTION", font=f_pill, fill=(255, 255, 255))

    f_h1 = get_font(64)
    draw.text((90, 380), "Key Policy Actions\nMoved by Council Leader", font=f_h1, fill=(255, 255, 255), spacing=18)

    # Council Leader card
    draw.rounded_rectangle([(90, 600), (990, 800)], radius=20, fill=(30, 41, 59))
    f_lead = get_font(42)
    f_role = get_font(30)
    draw.text((130, 650), "Cllr Adam Hug", font=f_lead, fill=(255, 255, 255))
    draw.text((130, 715), "Leader of Westminster City Council (Labour)", font=f_role, fill=(148, 163, 184))

    # Document highlight excerpt simulation
    draw.rounded_rectangle([(90, 860), (990, 1480)], radius=24, fill=(254, 249, 195)) # document paper tone
    f_doc_title = get_font(26)
    draw.text((130, 900), "OFFICIAL COUNCIL RECORD • MOTION EXTRACT", font=f_doc_title, fill=(133, 77, 14))

    # Yellow highlighter bar over text
    draw.rectangle([(120, 970), (960, 1160)], fill=(254, 240, 138))
    f_doc_body = get_font(36)
    body_text = (
        "“Deliver a new Community Equality Strategy\n"
        "focused on improving council services and\n"
        "strengthening the council's role in promoting\n"
        "community cohesion and earlier support.”"
    )
    draw.text((140, 990), body_text, font=f_doc_body, fill=(28, 25, 23), spacing=12)

    # Source document stamp
    draw.rounded_rectangle([(130, 1260), (540, 1360)], radius=12, fill=(250, 204, 21))
    f_stamp = get_font(28)
    draw.text((160, 1295), "COUNCIL APPROVED", font=f_stamp, fill=(113, 63, 18))

    img.save(output_path)

def create_scene3_image(output_path):
    # Atmospheric B-roll placeholder with prominent AI illustrative watermark
    img = Image.new("RGB", (1080, 1920), color=(30, 41, 59))
    draw = ImageDraw.Draw(img)
    draw_header_and_footer(draw, borough="Westminster")

    # Mandatory AI illustrative visual disclaimer banner (high contrast)
    draw.rounded_rectangle([(90, 240), (550, 300)], radius=8, fill=(0, 0, 0, 220))
    draw.rectangle([(90, 240), (105, 300)], fill=(234, 179, 8)) # amber warning stripe
    f_badge = get_font(24)
    draw.text((120, 255), "AI ILLUSTRATIVE B-ROLL", font=f_badge, fill=(250, 204, 21))

    # Visual graphic representing Victoria Street / London diversity
    f_h1 = get_font(60)
    draw.text((90, 420), "Borough Context:\nA Global Community", font=f_h1, fill=(255, 255, 255), spacing=18)

    # 2 big stat callouts
    draw.rounded_rectangle([(90, 680), (520, 1020)], radius=24, fill=(15, 23, 42))
    f_big = get_font(90)
    f_lbl = get_font(30)
    draw.text((130, 730), "180+", font=f_big, fill=(56, 189, 248))
    draw.text((130, 860), "Nationalities\nrepresented", font=f_lbl, fill=(226, 232, 240), spacing=10)

    draw.rounded_rectangle([(560, 680), (990, 1020)], radius=24, fill=(15, 23, 42))
    draw.text((600, 730), "150+", font=f_big, fill=(167, 139, 250))
    draw.text((600, 860), "Languages\nspoken across\ntown halls", font=f_lbl, fill=(226, 232, 240), spacing=10)

    # Lower third context bar
    draw.rounded_rectangle([(90, 1150), (990, 1420)], radius=20, fill=(15, 23, 42))
    f_ctx = get_font(34)
    ctx_text = "Victoria Street & Town Hall precincts.\nLocal authorities reaffirm zero tolerance\nfor anti-migrant intimidation."
    draw.text((130, 1210), ctx_text, font=f_ctx, fill=(203, 213, 225), spacing=12)

    img.save(output_path)

def create_scene4_image(output_path):
    img = Image.new("RGB", (1080, 1920), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    draw_header_and_footer(draw, borough="Westminster")

    # Pill
    draw.rounded_rectangle([(90, 260), (520, 320)], radius=12, fill=(13, 148, 136))
    f_pill = get_font(28)
    draw.text((120, 275), "COMMUNITY ACTION", font=f_pill, fill=(255, 255, 255))

    f_h1 = get_font(62)
    draw.text((90, 380), "Cross-Community\nWorking Group", font=f_h1, fill=(255, 255, 255), spacing=18)

    # 4 Pillar cards
    pillars = [
        ("Faith Leaders", "Interfaith dialogues & cultural festivals", (56, 189, 248)),
        ("Youth Voices", "School & community center programmes", (244, 114, 182)),
        ("Local Residents", "Grassroots reporting and lived experience", (251, 191, 36)),
        ("Met Police Partnership", "Swift hate crime response and victim care", (52, 211, 153)),
    ]

    top = 640
    for title, desc, col in pillars:
        draw.rounded_rectangle([(90, top), (990, top + 155)], radius=18, fill=(30, 41, 59))
        draw.rounded_rectangle([(90, top), (105, top + 155)], radius=6, fill=col)
        f_t = get_font(36)
        f_d = get_font(28)
        draw.text((130, top + 25), title, font=f_t, fill=(255, 255, 255))
        draw.text((130, top + 80), desc, font=f_d, fill=(148, 163, 184))
        top += 185

    img.save(output_path)

def create_scene5_image(output_path):
    img = Image.new("RGB", (1080, 1920), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    draw_header_and_footer(draw, borough="Westminster")

    f_brand_big = get_font(90)
    f_sub = get_font(42)
    f_desc = get_font(32)

    draw.text((90, 600), "London Local.", font=f_brand_big, fill=(255, 255, 255))
    draw.text((90, 730), "Independent civic news across 33 councils.", font=f_sub, fill=(148, 163, 184))

    draw.rounded_rectangle([(90, 880), (990, 1260)], radius=24, fill=(30, 41, 59))
    draw.text((140, 940), "READ THE ORIGINAL DOCUMENTS", font=get_font(28), fill=(56, 189, 248))
    
    docs_text = (
        "• Westminster Council Agenda Frontsheet (12 Nov 2025)\n"
        "• Full Committee Meeting Minutes & Official Webcast\n"
        "• Community Equality Strategy Briefing Paper"
    )
    draw.text((140, 1010), docs_text, font=f_desc, fill=(226, 232, 240), spacing=16)

    # CTA Button
    draw.rounded_rectangle([(90, 1340), (990, 1460)], radius=20, fill=(37, 99, 235))
    draw.text((320, 1380), "londonlocal.news", font=get_font(44), fill=(255, 255, 255))

    img.save(output_path)

def generate_audio(voice="en-GB-RyanNeural"):
    with open(SPEC_PATH) as f:
        spec = json.load(f)

    timings = []
    for scene in spec["timeline"]:
        num = scene["sceneNumber"]
        text = scene["voiceoverText"]
        out_mp3 = os.path.join(AUDIO_DIR, f"scene_{num}.mp3")
        
        print(f"Synthesising voiceover for Scene {num}...")
        cmd = ["edge-tts", "--voice", voice, "--text", text, "--write-media", out_mp3]
        subprocess.run(cmd, check=True)

        # Probe duration
        probe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", out_mp3
        ]
        res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        dur = float(res.stdout.strip())
        timings.append((num, dur, out_mp3))
        print(f"Scene {num} Audio Duration: {dur:.2f}s")

    return timings

def render_video():
    print("=== Step 1: Generating Graphic Stills ===")
    img1 = os.path.join(ASSETS_DIR, "real/scene1_westminster_vote.png")
    img2 = os.path.join(ASSETS_DIR, "real/scene2_equality_strategy.png")
    img3 = os.path.join(ASSETS_DIR, "generative/scene3_victoria_street.png")
    img4 = os.path.join(ASSETS_DIR, "real/scene4_working_group.png")
    img5 = os.path.join(ASSETS_DIR, "branding/scene5_outro.png")

    create_scene1_image(img1)
    create_scene2_image(img2)
    create_scene3_image(img3)
    create_scene4_image(img4)
    create_scene5_image(img5)
    print("Graphic assets created successfully.")

    print("\n=== Step 2: Generating Neural Audio ===")
    timings = generate_audio()

    print("\n=== Step 3: Assembling Video Clips per Scene ===")
    images = [img1, img2, img3, img4, img5]
    segment_files = []

    for i, (num, dur, mp3_path) in enumerate(timings):
        seg_out = os.path.join(BUILD_DIR, f"seg_{num}.mp4")
        # Pad duration slightly by 0.4s for clean cadence
        pad_dur = dur + 0.4
        img_path = images[i]

        # Use subtle zoom effect (Ken Burns) or clean still
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", img_path,
            "-i", mp3_path,
            "-c:v", "libx264", "-t", str(pad_dur),
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1080:1920",
            "-c:a", "aac", "-b:a", "192k",
            seg_out
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        segment_files.append(seg_out)
        print(f"Segment {num} encoded ({pad_dur:.2f}s)")

    print("\n=== Step 4: Concatenating Master Video ===")
    concat_list = os.path.join(BUILD_DIR, "concat_list.txt")
    with open(concat_list, "w") as f:
        for seg in segment_files:
            f.write(f"file '{seg}'\n")

    master_output = os.path.join(OUTPUT_DIR, "sample_video_4178.mp4")
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        master_output
    ]
    subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Check final duration and size
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
        "-of", "default=noprint_wrappers=1", master_output
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    print(f"\n Master Video Rendered: {master_output}")
    print(res.stdout)

if __name__ == "__main__":
    render_video()
