#!/usr/bin/env python3
"""
London Local News Video Assembly Pipeline (V2 - Black & White Editorial Edition)
Implements:
- High-contrast black & white broadsheet aesthetic matching londonlocal.news
- Outlined cartographic map background textures with Thames river curves & grid lines
- Photorealistic generative B-roll backdrop for atmospheric depth
- Configurable '[ YOUR LOGO HERE ]' header slot with CleanShot brand logo integration
- Broadcast-grade serif typography (Georgia Bold) and signature coral red dot accents
"""

import json
import os
import subprocess
import argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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
LOGO_ICON = os.path.join(BRANDING_DIR, "london-local-icon.png")
GEN_STREET_BG = os.path.join(GENERATIVE_DIR, "westminster_street_bg.jpg")

CORAL_RED = (255, 82, 56) # London Local brand red dot
PURE_BLACK = (10, 10, 10)
DEEP_CHARCOAL = (20, 20, 22)
BORDER_GRAY = (55, 55, 60)
GRID_LINE = (35, 35, 40)
TEXT_WHITE = (255, 255, 255)
TEXT_MUTED = (160, 160, 165)

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def draw_cartographic_map_bg(width=1080, height=1920):
    """Draws an authentic, subtle vector cartographic map background."""
    img = Image.new("RGBA", (width, height), (*PURE_BLACK, 255))
    draw = ImageDraw.Draw(img)

    # 1. Coordinate Grid
    for x in range(0, width, 72):
        draw.line([(x, 0), (x, height)], fill=(*GRID_LINE, 255), width=1)
    for y in range(0, height, 72):
        draw.line([(0, y), (width, y)], fill=(*GRID_LINE, 255), width=1)

    # 2. Thames River Curve (stylized vector broadsheet line)
    thames_curve = [
        (-40, 1380), (180, 1320), (380, 1370), (580, 1420),
        (780, 1360), (950, 1260), (1120, 1290)
    ]
    for w in range(32, 0, -6):
        opacity = int(45 - w)
        draw.line(thames_curve, fill=(35 + opacity, 38 + opacity, 45 + opacity, 255), width=w)

    # 3. Contour rings (Westminster Borough boundary lines)
    center_x, center_y = 520, 880
    for r in range(160, 920, 90):
        draw.arc([center_x - r, center_y - r, center_x + r, center_y + r],
                 start=15, end=210, fill=(45, 45, 52, 255), width=1)
        draw.arc([center_x - r - 40, center_y - r - 60, center_x + r - 40, center_y + r - 60],
                 start=240, end=330, fill=(38, 38, 44, 255), width=1)

    return img.convert("RGB")

def draw_header_bar(draw, img, show_authorised_logo=True, width=1080):
    """Draws the top editorial bar with the logo slot or authorised brand logo."""
    # Top separator rule
    draw.line([(60, 170), (width - 60, 170)], fill=BORDER_GRAY, width=1)

    if show_authorised_logo and os.path.exists(LOGO_WORDMARK):
        # Embed the authorised London Local wordmark
        try:
            wm = Image.open(LOGO_WORDMARK).convert("RGBA")
            # Target height 48px
            aspect = wm.width / wm.height
            wm = wm.resize((int(48 * aspect), 48), Image.Resampling.LANCZOS)
            img.paste(wm, (70, 90), wm)
        except Exception:
            draw.text((70, 90), "London Local.", font=get_font(FONT_SERIF_BOLD, 42), fill=TEXT_WHITE)
    else:
        # Editorial placeholder box: [ YOUR LOGO HERE ]
        draw.rounded_rectangle([(70, 80), (380, 150)], radius=6, outline=(120, 120, 125), width=2)
        draw.text((95, 102), "YOUR LOGO HERE", font=get_font(FONT_SANS, 24), fill=(200, 200, 205))

    # Right badge: Borough marker
    f_meta = get_font(FONT_SANS, 24)
    draw.rounded_rectangle([(width - 320, 92), (width - 70, 142)], radius=6, fill=DEEP_CHARCOAL, outline=BORDER_GRAY)
    draw.text((width - 300, 105), "WESTMINSTER • 12 NOV", font=f_meta, fill=TEXT_MUTED)

def draw_footer_bar(draw, width=1080, height=1920):
    draw.line([(60, height - 140), (width - 60, height - 140)], fill=BORDER_GRAY, width=1)
    f_foot = get_font(FONT_SANS, 22)
    draw.text((70, height - 110), "PUBLIC RECORD • COUNCIL REPORT • CIVIC INVESTIGATION", font=f_foot, fill=(110, 110, 115))

def create_scene1_card(out_path, show_logo=True):
    img = draw_cartographic_map_bg()
    draw = ImageDraw.Draw(img)
    draw_header_bar(draw, img, show_authorised_logo=show_logo)
    draw_footer_bar(draw)

    # Pill badge
    draw.rounded_rectangle([(70, 230), (320, 280)], radius=4, fill=TEXT_WHITE)
    draw.text((95, 245), "COUNCIL VOTE", font=get_font(FONT_SANS, 22), fill=PURE_BLACK)

    # Editorial Serif Headline
    f_h1 = get_font(FONT_SERIF_BOLD, 72)
    h_text = "Westminster Stands\nAgainst Far-Right\nExtremism"
    draw.text((70, 320), h_text, font=f_h1, fill=TEXT_WHITE, spacing=16)

    # Red dot punctuation
    draw.ellipse([(730, 480), (748, 498)], fill=CORAL_RED)

    # High-contrast broadsheet data card
    draw.rounded_rectangle([(70, 680), (1010, 1120)], radius=12, fill=(18, 18, 20), outline=BORDER_GRAY, width=2)
    
    # Left accent bar
    draw.rectangle([(70, 680), (82, 1120)], fill=TEXT_WHITE)

    draw.text((120, 730), "VOTE RESULT", font=get_font(FONT_SANS, 26), fill=TEXT_MUTED)
    draw.text((120, 780), "UNANIMOUS", font=get_font(FONT_SERIF_BOLD, 100), fill=TEXT_WHITE)
    
    desc = (
        "Council passes cross-party motion condemning all\n"
        "forms of hate crime, anti-migrant rhetoric, and\n"
        "far-right extremism across the borough."
    )
    draw.text((120, 930), desc, font=get_font(FONT_SERIF, 34), fill=(220, 220, 225), spacing=12)

    # Source quote callout
    draw.rounded_rectangle([(70, 1180), (1010, 1460)], radius=12, fill=(18, 18, 20), outline=BORDER_GRAY, width=1)
    q = (
        "“Blaming migrants does not solve our challenges.\n"
        "Westminster has always been, and must remain,\n"
        "a safe and welcoming city for all residents.”"
    )
    draw.text((110, 1230), q, font=get_font(FONT_SERIF, 34), fill=(200, 200, 205), spacing=14)

    img.save(out_path)

def create_scene2_card(out_path, show_logo=True):
    img = draw_cartographic_map_bg()
    draw = ImageDraw.Draw(img)
    draw_header_bar(draw, img, show_authorised_logo=show_logo)
    draw_footer_bar(draw)

    draw.rounded_rectangle([(70, 230), (360, 280)], radius=4, fill=TEXT_WHITE)
    draw.text((95, 245), "POLICY MANDATE", font=get_font(FONT_SANS, 22), fill=PURE_BLACK)

    f_h1 = get_font(FONT_SERIF_BOLD, 64)
    draw.text((70, 320), "New Community\nEquality Strategy", font=f_h1, fill=TEXT_WHITE, spacing=16)

    # Leader card
    draw.rounded_rectangle([(70, 560), (1010, 740)], radius=12, fill=(18, 18, 20), outline=BORDER_GRAY, width=2)
    draw.text((110, 600), "Cllr Adam Hug", font=get_font(FONT_SERIF_BOLD, 46), fill=TEXT_WHITE)
    draw.text((110, 665), "Leader of Westminster City Council • Labour & Co-operative", font=get_font(FONT_SANS, 26), fill=TEXT_MUTED)

    # Official Council Record Broadsheet Clipping
    draw.rounded_rectangle([(70, 790), (1010, 1460)], radius=12, fill=(245, 245, 248)) # crisp off-white paper
    draw.text((110, 830), "AGENDA PACK EXTRACT • WEDNESDAY 12 NOV 2025", font=get_font(FONT_SANS, 24), fill=(90, 90, 95))

    # Yellow highlighter box over core commitment
    draw.rectangle([(100, 900), (980, 1160)], fill=(255, 245, 157)) # highlight yellow
    
    quote_text = (
        "“Deliver a new Community Equality Strategy\n"
        "focused on improving council services and\n"
        "promoting community cohesion, ensuring\n"
        "earlier support is given to affected groups.”"
    )
    draw.text((120, 915), quote_text, font=get_font(FONT_SERIF_BOLD, 35), fill=(15, 15, 18), spacing=12)

    sub_commitments = (
        "• Establish cross-community working group with faith leaders\n"
        "• Partner with police for rapid response to hate incidents\n"
        "• Champion cultural festivals and youth programmes"
    )
    draw.text((110, 1180), sub_commitments, font=get_font(FONT_SANS, 30), fill=(40, 40, 45), spacing=16)

    img.save(out_path)

def create_scene3_card(out_path, show_logo=True):
    """Scene 3 uses the photorealistic generative B-roll image of Victoria Street."""
    if os.path.exists(GEN_STREET_BG):
        base = Image.open(GEN_STREET_BG).convert("RGB")
        base = base.resize((1080, 1920), Image.Resampling.LANCZOS)
    else:
        base = draw_cartographic_map_bg()

    # Dark gradient overlays for high-contrast readability
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d_ov = ImageDraw.Draw(overlay)
    
    # Top and bottom dark scrims
    for y in range(0, 360):
        alpha = int(220 * (1 - (y / 360)))
        d_ov.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))
    for y in range(1200, 1920):
        alpha = int(240 * ((y - 1200) / 720))
        d_ov.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))

    img = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw_header_bar(draw, img, show_authorised_logo=show_logo)
    draw_footer_bar(draw)

    # Mandatory AI illustrative disclaimer banner (High-contrast amber)
    draw.rounded_rectangle([(70, 200), (460, 255)], radius=6, fill=(0, 0, 0, 230), outline=(245, 158, 11), width=1)
    draw.rectangle([(70, 200), (80, 255)], fill=(245, 158, 11))
    draw.text((95, 217), "AI ILLUSTRATIVE B-ROLL", font=get_font(FONT_SANS, 22), fill=(251, 191, 36))

    # Lower glass card with statistics
    draw.rounded_rectangle([(70, 1260), (1010, 1680)], radius=16, fill=(10, 10, 12, 235), outline=BORDER_GRAY, width=1)
    draw.text((110, 1310), "WESTMINSTER DEMOGRAPHICS", font=get_font(FONT_SANS, 24), fill=TEXT_MUTED)

    # 2 big stat columns
    draw.text((110, 1370), "180+", font=get_font(FONT_SERIF_BOLD, 84), fill=TEXT_WHITE)
    draw.text((110, 1480), "Nationalities\nrepresented", font=get_font(FONT_SANS, 28), fill=(200, 200, 205), spacing=8)

    draw.line([(530, 1370), (530, 1580)], fill=BORDER_GRAY, width=1)

    draw.text((580, 1370), "150+", font=get_font(FONT_SERIF_BOLD, 84), fill=TEXT_WHITE)
    draw.text((580, 1480), "Languages spoken\nacross borough", font=get_font(FONT_SANS, 28), fill=(200, 200, 205), spacing=8)

    img.save(out_path)

def create_scene4_card(out_path, show_logo=True):
    img = draw_cartographic_map_bg()
    draw = ImageDraw.Draw(img)
    draw_header_bar(draw, img, show_authorised_logo=show_logo)
    draw_footer_bar(draw)

    draw.rounded_rectangle([(70, 230), (420, 280)], radius=4, fill=TEXT_WHITE)
    draw.text((95, 245), "COMMUNITY ACTION", font=get_font(FONT_SANS, 22), fill=PURE_BLACK)

    f_h1 = get_font(FONT_SERIF_BOLD, 64)
    draw.text((70, 320), "Cross-Community\nWorking Group", font=f_h1, fill=TEXT_WHITE, spacing=16)

    pillars = [
        ("01 / FAITH LEADERS", "Interfaith dialogues, mutual support & cultural festivals"),
        ("02 / YOUTH VOICES", "Civic education and school anti-prejudice initiatives"),
        ("03 / LOCAL RESIDENTS", "Community-led monitoring of local tensions and safety"),
        ("04 / MET POLICE", "Swift investigation and dignifying care for hate crime victims")
    ]

    top = 580
    for title, desc in pillars:
        draw.rounded_rectangle([(70, top), (1010, top + 170)], radius=12, fill=(18, 18, 20), outline=BORDER_GRAY, width=1)
        draw.text((110, top + 35), title, font=get_font(FONT_SANS, 24), fill=TEXT_WHITE)
        draw.text((110, top + 85), desc, font=get_font(FONT_SERIF, 32), fill=(210, 210, 215))
        top += 205

    img.save(out_path)

def create_scene5_card(out_path, show_logo=True):
    img = draw_cartographic_map_bg()
    draw = ImageDraw.Draw(img)
    draw_header_bar(draw, img, show_authorised_logo=show_logo)
    draw_footer_bar(draw)

    # Prominent London Local wordmark at centre
    if show_logo and os.path.exists(LOGO_WORDMARK):
        try:
            wm = Image.open(LOGO_WORDMARK).convert("RGBA")
            aspect = wm.width / wm.height
            wm = wm.resize((int(90 * aspect), 90), Image.Resampling.LANCZOS)
            img.paste(wm, (70, 520), wm)
        except Exception:
            draw.text((70, 520), "London Local.", font=get_font(FONT_SERIF_BOLD, 84), fill=TEXT_WHITE)
    else:
        draw.text((70, 520), "London Local.", font=get_font(FONT_SERIF_BOLD, 84), fill=TEXT_WHITE)

    draw.text((70, 650), "AI-first civic news across Greater London's 33 councils.", font=get_font(FONT_SANS, 34), fill=TEXT_MUTED)

    # Document Verification Box
    draw.rounded_rectangle([(70, 780), (1010, 1260)], radius=12, fill=(18, 18, 20), outline=BORDER_GRAY, width=2)
    draw.text((110, 830), "VERIFIED SOURCE ARCHIVE", font=get_font(FONT_SANS, 24), fill=TEXT_MUTED)

    links = (
        "• Council Meeting Minutes (Wednesday 12 November 2025)\n"
        "• Westminster Motion Frontsheet & Full Voting Tally\n"
        "• Draft Community Equality Strategy Framework\n"
        "• Public Webcast Archive"
    )
    draw.text((110, 900), links, font=get_font(FONT_SERIF, 32), fill=(230, 230, 235), spacing=22)

    # Full CTA Button
    draw.rounded_rectangle([(70, 1340), (1010, 1460)], radius=8, fill=TEXT_WHITE)
    draw.text((310, 1380), "londonlocal.news", font=get_font(FONT_SERIF_BOLD, 44), fill=PURE_BLACK)

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
    print("=== 1. Building Editorial Broad-sheet Assets (B&W Edition) ===")
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
    print("All 5 editorial cards generated.")

    print("\n=== 2. Generating British Neural Audio ===")
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

    print("\n=== 4. Assembling Master 9:16 News Video ===")
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
    print(f"\n Master Editorial Video Rendered: {master_output}")
    print(res.stdout)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--show-authorised-logo", action="store_true", default=True,
                        help="Render with CleanShot authorised logo instead of placeholder")
    args = parser.parse_args()
    render_video(show_logo=args.show_authorised_logo)
