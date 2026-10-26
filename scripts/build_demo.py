#!/usr/bin/env python3
"""
London Local News Video Assembly Pipeline (V4 - Split Broadsheet Mobile Edition)
Design Architecture:
- Top Half (y: 0 - 860): Black editorial / media window (generative B-roll, badges, header)
- Bottom Half (y: 860 - 1920): Crisp white newspaper broadsheet with large, high-contrast serif typography
- Mobile-optimised readability for TikTok, Reels, and Reddit feeds
- Neural TTS using en-GB-RyanNeural with millisecond audio synchronization
"""

import json
import os
import subprocess
import argparse
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC_PATH = os.path.join(BASE_DIR, "specs/4178-westminster-extremism.json")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
BRANDING_DIR = os.path.join(ASSETS_DIR, "branding")
GENERATIVE_DIR = os.path.join(ASSETS_DIR, "generative")
BUILD_DIR = os.path.join(BASE_DIR, "build")
AUDIO_DIR = os.path.join(BUILD_DIR, "audio")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

FONT_SERIF_BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
FONT_SERIF = "/System/Library/Fonts/Supplemental/Georgia.ttf"
FONT_SANS = "/System/Library/Fonts/Supplemental/Arial.ttf"

LOGO_WORDMARK = os.path.join(BRANDING_DIR, "london-local-wordmark.png")
GEN_STREET_BG = os.path.join(GENERATIVE_DIR, "westminster_street_bg.jpg")

CORAL_RED = (255, 82, 56)
TOP_BLACK = (12, 12, 14)
BOTTOM_WHITE = (255, 255, 255)
DIVIDER_LINE = (225, 225, 230)
TEXT_DARK = (15, 15, 18)
TEXT_MUTED_DARK = (90, 90, 95)
TEXT_WHITE = (255, 255, 255)
TEXT_MUTED_LIGHT = (160, 160, 165)
BORDER_DARK = (45, 45, 50)
BORDER_LIGHT = (230, 230, 235)

SPLIT_Y = 820 # Top media window boundary

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def draw_split_base_canvas(width=1080, height=1920):
    """Draws the split canvas: Top Black / Bottom White."""
    img = Image.new("RGB", (width, height), BOTTOM_WHITE)
    draw = ImageDraw.Draw(img)

    # Top dark window
    draw.rectangle([(0, 0), (width, SPLIT_Y)], fill=TOP_BLACK)
    # Crisp hairline divider
    draw.line([(0, SPLIT_Y), (width, SPLIT_Y)], fill=DIVIDER_LINE, width=2)

    return img

def draw_header_bar(draw, img, show_authorised_logo=True, width=1080):
    """Draws the top editorial bar in the dark window."""
    draw.line([(70, 160), (width - 70, 160)], fill=BORDER_DARK, width=1)

    if show_authorised_logo and os.path.exists(LOGO_WORDMARK):
        try:
            wm = Image.open(LOGO_WORDMARK).convert("RGBA")
            aspect = wm.width / wm.height
            wm = wm.resize((int(44 * aspect), 44), Image.Resampling.LANCZOS)
            img.paste(wm, (70, 90), wm)
        except Exception:
            draw.text((70, 90), "London Local.", font=get_font(FONT_SERIF_BOLD, 40), fill=TEXT_WHITE)
    else:
        draw.rounded_rectangle([(70, 85), (370, 145)], radius=6, outline=(100, 100, 105), width=1)
        draw.text((95, 102), "YOUR LOGO HERE", font=get_font(FONT_SANS, 22), fill=(180, 180, 185))

    # Right council badge
    f_meta = get_font(FONT_SANS, 22)
    draw.rounded_rectangle([(width - 340, 90), (width - 70, 142)], radius=6, fill=(24, 24, 28), outline=BORDER_DARK, width=1)
    draw.text((width - 315, 105), "WESTMINSTER • 12 NOV", font=f_meta, fill=TEXT_MUTED_LIGHT)

def draw_bottom_footer(draw, context_text, width=1080, height=1920):
    """Draws a clean journalistic source footer on the white bottom half."""
    draw.line([(70, height - 130), (width - 70, height - 130)], fill=BORDER_LIGHT, width=1)
    f_foot = get_font(FONT_SANS, 24)
    draw.text((70, height - 95), context_text, font=f_foot, fill=TEXT_MUTED_DARK)

def create_scene1_card(out_path, show_logo=True):
    img = draw_split_base_canvas()
    draw = ImageDraw.Draw(img)
    draw_header_bar(draw, img, show_authorised_logo=show_logo)

    # --- TOP BLACK SECTION: Large Visual Banner ---
    draw.rounded_rectangle([(70, 210), (1010, 750)], radius=16, fill=(20, 20, 24), outline=BORDER_DARK, width=1)
    draw.rectangle([(70, 210), (84, 750)], fill=TEXT_WHITE) # White accent bar

    draw.text((120, 260), "COUNCIL CHAMBER DECISION", font=get_font(FONT_SANS, 24), fill=TEXT_MUTED_LIGHT)
    draw.text((120, 310), "UNANIMOUS VOTE", font=get_font(FONT_SERIF_BOLD, 80), fill=TEXT_WHITE)

    # Badge in top half
    draw.rounded_rectangle([(120, 440), (460, 500)], radius=6, fill=(245, 158, 11))
    draw.text((145, 458), "CROSS-PARTY APPROVAL", font=get_font(FONT_SANS, 22), fill=TEXT_DARK)

    stats_preview = "All 54 Councillors • Conservative & Labour support"
    draw.text((120, 540), stats_preview, font=get_font(FONT_SERIF, 32), fill=(200, 200, 205))

    # --- BOTTOM WHITE SECTION: Broadsheet Mobile Typography ---
    draw_bottom_footer(draw, "Westminster City Council • Meeting of Wednesday 12 November 2025")

    # Mobile Headline
    f_h1 = get_font(FONT_SERIF_BOLD, 74)
    h_text = "Westminster Stands\nAgainst Far-Right\nExtremism"
    draw.text((70, 880), h_text, font=f_h1, fill=TEXT_DARK, spacing=16)

    # Red dot accent
    draw.ellipse([(770, 1050), (790, 1070)], fill=CORAL_RED)

    # Large readable story body
    f_body = get_font(FONT_SERIF, 40)
    body_text = (
        "Westminster City Council has unanimously passed\n"
        "a cross-party motion condemning all forms of hate,\n"
        "anti-migrant language, and far-right activity\n"
        "across the city."
    )
    draw.text((70, 1190), body_text, font=f_body, fill=(35, 35, 40), spacing=18)

    # Highlighted quote card
    draw.rounded_rectangle([(70, 1460), (1010, 1720)], radius=12, fill=(245, 245, 248), outline=BORDER_LIGHT, width=1)
    draw.rectangle([(70, 1460), (80, 1720)], fill=TEXT_DARK)
    f_quote = get_font(FONT_SERIF, 34)
    q = (
        "“Blaming migrants does not solve our challenges.\n"
        "Westminster remains a safe, welcoming city\n"
        "where everyone can feel proud.”"
    )
    draw.text((110, 1500), q, font=f_quote, fill=TEXT_DARK, spacing=14)

    img.save(out_path)

def create_scene2_card(out_path, show_logo=True):
    img = draw_split_base_canvas()
    draw = ImageDraw.Draw(img)
    draw_header_bar(draw, img, show_authorised_logo=show_logo)

    # --- TOP BLACK SECTION: Leadership Card ---
    draw.rounded_rectangle([(70, 210), (1010, 750)], radius=16, fill=(20, 20, 24), outline=BORDER_DARK, width=1)
    draw.text((120, 260), "MOTION MOVER & SECONDER", font=get_font(FONT_SANS, 24), fill=TEXT_MUTED_LIGHT)
    draw.text((120, 310), "Cllr Adam Hug", font=get_font(FONT_SERIF_BOLD, 68), fill=TEXT_WHITE)
    draw.text((120, 405), "Leader of Westminster City Council (Labour & Co-operative)", font=get_font(FONT_SANS, 26), fill=TEXT_MUTED_LIGHT)

    draw.line([(120, 470), (960, 470)], fill=BORDER_DARK, width=1)
    draw.text((120, 510), "Seconded by Cllr Ryan Jude (Cabinet Member for Culture & Air Quality)", font=get_font(FONT_SERIF, 30), fill=(210, 210, 215))

    # --- BOTTOM WHITE SECTION: Document Extract ---
    draw_bottom_footer(draw, "Source: Council Agenda Frontsheet Item 8 • Official Motion Extract")

    f_h1 = get_font(FONT_SERIF_BOLD, 66)
    draw.text((70, 880), "New Community\nEquality Strategy Approved", font=f_h1, fill=TEXT_DARK, spacing=14)

    # Yellow highlighter box on white background (newspaper clipping feel)
    draw.rounded_rectangle([(70, 1100), (1010, 1400)], radius=8, fill=(255, 248, 180), outline=(235, 220, 130), width=1)
    
    quote_text = (
        "“Deliver a new Community Equality Strategy\n"
        "focused on improving council services and\n"
        "promoting community cohesion, ensuring earlier\n"
        "support is given to affected groups.”"
    )
    draw.text((110, 1130), quote_text, font=get_font(FONT_SERIF_BOLD, 38), fill=(20, 20, 25), spacing=14)

    # Bulleted implementation steps
    f_list = get_font(FONT_SANS, 34)
    bullets = (
        "• Partner with police for rapid response to hate crime\n"
        "• Establish cross-community strategy with faith leaders\n"
        "• Expand youth anti-prejudice programmes in schools"
    )
    draw.text((70, 1460), bullets, font=f_list, fill=(45, 45, 50), spacing=22)

    img.save(out_path)

def create_scene3_card(out_path, show_logo=True):
    """Scene 3: Photorealistic Generative B-Roll in Top Half, Demographics in Bottom Half."""
    img = draw_split_base_canvas()
    
    # 1. Paste the Generative 35mm Victoria Street photo in the top half window
    if os.path.exists(GEN_STREET_BG):
        gen_img = Image.open(GEN_STREET_BG).convert("RGB")
        # Crop/scale to 1080x820
        aspect = gen_img.width / gen_img.height
        new_w = 1080
        new_h = int(new_w / aspect)
        gen_scaled = gen_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        # Crop center
        top_crop = int((new_h - SPLIT_Y) / 2)
        gen_crop = gen_scaled.crop((0, max(0, top_crop), 1080, max(0, top_crop) + SPLIT_Y))
        img.paste(gen_crop, (0, 0))

        # Top dark scrim for header readability
        overlay = Image.new("RGBA", (1080, SPLIT_Y), (0, 0, 0, 0))
        d_ov = ImageDraw.Draw(overlay)
        for y in range(0, 220):
            alpha = int(220 * (1 - (y / 220)))
            d_ov.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))
        img.paste(Image.alpha_composite(Image.new("RGBA", (1080, SPLIT_Y), (0, 0, 0, 0)), overlay).convert("RGB"), (0, 0), overlay)

    draw = ImageDraw.Draw(img)
    draw_header_bar(draw, img, show_authorised_logo=show_logo)

    # Amber AI Illustrative Badge in the top media window
    draw.rounded_rectangle([(70, 200), (450, 255)], radius=6, fill=(0, 0, 0, 230), outline=(245, 158, 11), width=1)
    draw.rectangle([(70, 200), (80, 255)], fill=(245, 158, 11))
    draw.text((95, 218), "AI ILLUSTRATIVE B-ROLL", font=get_font(FONT_SANS, 20), fill=(251, 191, 36))

    # --- BOTTOM WHITE SECTION: Big Demographic Numbers ---
    draw_bottom_footer(draw, "Location: Victoria Street & Town Hall Precincts • Met Police Area")

    f_h1 = get_font(FONT_SERIF_BOLD, 68)
    draw.text((70, 880), "Westminster Demographics:\nA Global Community", font=f_h1, fill=TEXT_DARK, spacing=14)

    # 2 Big Stat Cards on white broadsheet
    draw.rounded_rectangle([(70, 1100), (510, 1420)], radius=12, fill=(245, 245, 248), outline=BORDER_LIGHT, width=1)
    draw.text((110, 1140), "180+", font=get_font(FONT_SERIF_BOLD, 96), fill=TEXT_DARK)
    draw.text((110, 1270), "Nationalities\nrepresented", font=get_font(FONT_SANS, 32), fill=TEXT_MUTED_DARK, spacing=8)

    draw.rounded_rectangle([(550, 1100), (1000, 1420)], radius=12, fill=(245, 245, 248), outline=BORDER_LIGHT, width=1)
    draw.text((590, 1140), "150+", font=get_font(FONT_SERIF_BOLD, 96), fill=TEXT_DARK)
    draw.text((590, 1270), "Languages spoken\nacross borough", font=get_font(FONT_SANS, 32), fill=TEXT_MUTED_DARK, spacing=8)

    f_context = get_font(FONT_SERIF, 36)
    ctx_text = (
        "Council leaders emphasised that migrant and\n"
        "minority communities must not be scapegoated\n"
        "for wider economic pressures."
    )
    draw.text((70, 1490), ctx_text, font=f_context, fill=(40, 40, 45), spacing=14)

    img.save(out_path)

def create_scene4_card(out_path, show_logo=True):
    img = draw_split_base_canvas()
    draw = ImageDraw.Draw(img)
    draw_header_bar(draw, img, show_authorised_logo=show_logo)

    # --- TOP BLACK SECTION: Strategy Pillar Banner ---
    draw.rounded_rectangle([(70, 210), (1010, 750)], radius=16, fill=(20, 20, 24), outline=BORDER_DARK, width=1)
    draw.text((120, 260), "COUNCIL IMPLEMENTATION PLAN", font=get_font(FONT_SANS, 24), fill=TEXT_MUTED_LIGHT)
    f_h1 = get_font(FONT_SERIF_BOLD, 64)
    draw.text((120, 310), "Cross-Community\nWorking Group", font=f_h1, fill=TEXT_WHITE, spacing=14)
    draw.text((120, 520), "Established to unite community leaders, youth & police.", font=get_font(FONT_SERIF, 32), fill=(200, 200, 205))

    # --- BOTTOM WHITE SECTION: Clean 4 Pillars ---
    draw_bottom_footer(draw, "Implementation: Westminster Town Hall • Cross-Community Directorate")

    draw.text((70, 880), "Four Core Pillars", font=get_font(FONT_SERIF_BOLD, 64), fill=TEXT_DARK)

    pillars = [
        ("01 / FAITH LEADERS", "Interfaith gatherings, mutual protection and cultural festivals"),
        ("02 / YOUTH VOICES", "Civic school workshops countering online hate narratives"),
        ("03 / LOCAL RESIDENTS", "Grassroots reporting and direct council liaison channels"),
        ("04 / MET POLICE", "Swift investigation and dignifying care for hate crime victims")
    ]

    top = 990
    for title, desc in pillars:
        draw.rounded_rectangle([(70, top), (1000, top + 145)], radius=10, fill=(245, 245, 248), outline=BORDER_LIGHT, width=1)
        draw.text((110, top + 25), title, font=get_font(FONT_SANS, 24), fill=TEXT_DARK)
        draw.text((110, top + 75), desc, font=get_font(FONT_SERIF, 30), fill=(70, 70, 75))
        top += 170

    img.save(out_path)

def create_scene5_card(out_path, show_logo=True):
    img = draw_split_base_canvas()
    draw = ImageDraw.Draw(img)
    draw_header_bar(draw, img, show_authorised_logo=show_logo)

    # --- TOP BLACK SECTION: Full Masthead ---
    if show_logo and os.path.exists(LOGO_WORDMARK):
        try:
            wm = Image.open(LOGO_WORDMARK).convert("RGBA")
            aspect = wm.width / wm.height
            wm = wm.resize((int(72 * aspect), 72), Image.Resampling.LANCZOS)
            img.paste(wm, (70, 320), wm)
        except Exception:
            draw.text((70, 320), "London Local.", font=get_font(FONT_SERIF_BOLD, 76), fill=TEXT_WHITE)
    else:
        draw.text((70, 320), "London Local.", font=get_font(FONT_SERIF_BOLD, 76), fill=TEXT_WHITE)

    draw.text((70, 430), "AI-first civic reporting across Greater London's 33 councils.", font=get_font(FONT_SANS, 30), fill=TEXT_MUTED_LIGHT)

    # --- BOTTOM WHITE SECTION: Verification Archive & CTA ---
    draw_bottom_footer(draw, "Independent Civic Journalism Across Greater London's 33 Councils")

    draw.text((70, 880), "Verified Council Archive", font=get_font(FONT_SERIF_BOLD, 64), fill=TEXT_DARK)

    draw.rounded_rectangle([(70, 990), (1000, 1440)], radius=12, fill=(245, 245, 248), outline=BORDER_LIGHT, width=1)
    draw.text((110, 1040), "SOURCE DOCUMENTS ON RECORD", font=get_font(FONT_SANS, 22), fill=TEXT_MUTED_DARK)

    links = (
        "• Full Committee Meeting Minutes (12 November 2025)\n"
        "• Westminster Motion Frontsheet & Voting Tally\n"
        "• Draft Community Equality Strategy Briefing Paper\n"
        "• Public Webcast Recording"
    )
    draw.text((110, 1110), links, font=get_font(FONT_SERIF, 34), fill=(30, 30, 35), spacing=24)

    # Full Width CTA
    draw.rounded_rectangle([(70, 1530), (1000, 1660)], radius=10, fill=TEXT_DARK)
    draw.text((320, 1575), "londonlocal.news", font=get_font(FONT_SERIF_BOLD, 46), fill=TEXT_WHITE)

    img.save(out_path)

def generate_audio(voice="en-GB-RyanNeural"):
    with open(SPEC_PATH) as f:
        spec = json.load(f)

    timings = []
    for scene in spec["timeline"]:
        num = scene["sceneNumber"]
        text = scene["voiceoverText"]
        out_mp3 = os.path.join(AUDIO_DIR, f"scene_{num}.mp3")
        
        cmd = ["edge-tts", "--voice", voice, "--text", text, "--write-media", out_mp3]
        subprocess.run(cmd, check=True)

        probe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", out_mp3
        ]
        res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        dur = float(res.stdout.strip())
        timings.append((num, dur, out_mp3))

    return timings

def render_video(show_logo=True):
    print("=== 1. Generating Split Mobile Broadsheet Cards (V4) ===")
    img1 = os.path.join(ASSETS_DIR, "real/scene1_westminster_vote.png")
    img2 = os.path.join(ASSETS_DIR, "real/scene2_equality_strategy.png")
    img3 = os.path.join(ASSETS_DIR, "generative/scene3_victoria_street.png")
    img4 = os.path.join(ASSETS_DIR, "real/scene4_working_group.png")
    img5 = os.path.join(ASSETS_DIR, "branding/scene5_outro.png")

    create_scene1_card(img1, show_logo=show_logo)
    create_scene2_card(img2, show_logo=show_logo)
    create_scene3_card(img3, show_logo=show_logo)
    create_scene4_card(img4, show_logo=show_logo)
    create_scene5_card(img5, show_logo=show_logo)
    print("All 5 split mobile cards generated.")

    print("\n=== 2. Synthesising British Neural Audio ===")
    timings = generate_audio()

    print("\n=== 3. Encoding Video Clips with Motion & Safe Margins ===")
    images = [img1, img2, img3, img4, img5]
    segment_files = []

    for i, (num, dur, mp3_path) in enumerate(timings):
        seg_out = os.path.join(BUILD_DIR, f"seg_{num}.mp4")
        pad_dur = dur + 0.35
        img_path = images[i]

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

    print("\n=== 4. Assembling Master 9:16 Video ===")
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
    print(f"\n Master Video Rendered: {master_output}")
    print(res.stdout)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--show-authorised-logo", action="store_true", default=True,
                        help="Render with CleanShot authorised logo instead of placeholder")
    args = parser.parse_args()
    render_video(show_logo=args.show_authorised_logo)
