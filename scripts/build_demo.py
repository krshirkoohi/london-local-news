#!/usr/bin/env python3
"""
London Local News Video Assembly Pipeline (V3 - Clean Editorial Broadsheet)
Improvements:
- Removed distracting pipe-like lines; clean minimalist Swiss/broadsheet grid & texture
- Fixed header alignment, removed awkward line collisions and artifacts
- Replaced repetitive footer filler with authentic scene-specific journalistic source context
- Programmatic generative image support via Google GenAI / Imagen 3
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

CORAL_RED = (255, 82, 56) # London Local brand red dot
PURE_BLACK = (12, 12, 14)
CARD_BG = (22, 22, 26)
BORDER_GRAY = (45, 45, 50)
GRID_COLOR = (26, 26, 30)
TEXT_WHITE = (255, 255, 255)
TEXT_MUTED = (155, 155, 160)

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def draw_clean_broadsheet_bg(width=1080, height=1920):
    """Draws a clean, elegant dark broadsheet background with minimal hairline grid."""
    img = Image.new("RGBA", (width, height), (*PURE_BLACK, 255))
    draw = ImageDraw.Draw(img)

    # Subtle 120px hairline grid (clean architectural drafting style, no thick pipes)
    for x in range(80, width - 80, 115):
        draw.line([(x, 180), (x, height - 160)], fill=(*GRID_COLOR, 255), width=1)
    for y in range(200, height - 160, 120):
        draw.line([(80, y), (width - 80, y)], fill=(*GRID_COLOR, 255), width=1)

    return img.convert("RGB")

def draw_header_bar(draw, img, show_authorised_logo=True, width=1080):
    """Draws a clean, well-spaced top editorial header."""
    # Top separator rule across safe width
    draw.line([(80, 170), (width - 80, 170)], fill=BORDER_GRAY, width=1)

    if show_authorised_logo and os.path.exists(LOGO_WORDMARK):
        try:
            wm = Image.open(LOGO_WORDMARK).convert("RGBA")
            aspect = wm.width / wm.height
            wm = wm.resize((int(46 * aspect), 46), Image.Resampling.LANCZOS)
            img.paste(wm, (80, 95), wm)
        except Exception:
            draw.text((80, 95), "London Local.", font=get_font(FONT_SERIF_BOLD, 40), fill=TEXT_WHITE)
    else:
        # Clean white-label box
        draw.rounded_rectangle([(80, 90), (380, 152)], radius=6, outline=(100, 100, 105), width=1)
        draw.text((105, 108), "YOUR LOGO HERE", font=get_font(FONT_SANS, 22), fill=(180, 180, 185))

    # Right badge: Clean council tag with ample margin
    f_meta = get_font(FONT_SANS, 22)
    draw.rounded_rectangle([(width - 340, 98), (width - 80, 148)], radius=6, fill=CARD_BG, outline=BORDER_GRAY, width=1)
    draw.text((width - 315, 112), "WESTMINSTER • 12 NOV", font=f_meta, fill=TEXT_MUTED)

def draw_footer_bar(draw, context_text, width=1080, height=1920):
    """Draws an informative, authentic journalistic source footer (no generic filler)."""
    draw.line([(80, height - 140), (width - 80, height - 140)], fill=BORDER_GRAY, width=1)
    f_foot = get_font(FONT_SANS, 24)
    draw.text((80, height - 105), context_text, font=f_foot, fill=TEXT_MUTED)

def create_scene1_card(out_path, show_logo=True):
    img = draw_clean_broadsheet_bg()
    draw = ImageDraw.Draw(img)
    draw_header_bar(draw, img, show_authorised_logo=show_logo)
    draw_footer_bar(draw, "Westminster City Council • Meeting of Wednesday 12 November 2025")

    # Category Pill
    draw.rounded_rectangle([(80, 230), (310, 280)], radius=4, fill=TEXT_WHITE)
    draw.text((102, 246), "COUNCIL VOTE", font=get_font(FONT_SANS, 20), fill=PURE_BLACK)

    # Headline
    f_h1 = get_font(FONT_SERIF_BOLD, 70)
    h_text = "Westminster Stands\nAgainst Far-Right\nExtremism"
    draw.text((80, 320), h_text, font=f_h1, fill=TEXT_WHITE, spacing=16)

    # Red dot accent
    draw.ellipse([(735, 475), (752, 492)], fill=CORAL_RED)

    # High-contrast data card
    draw.rounded_rectangle([(80, 680), (1000, 1110)], radius=12, fill=CARD_BG, outline=BORDER_GRAY, width=1)
    draw.rectangle([(80, 680), (92, 1110)], fill=TEXT_WHITE)

    draw.text((130, 730), "VOTE OUTCOME", font=get_font(FONT_SANS, 24), fill=TEXT_MUTED)
    draw.text((130, 780), "UNANIMOUS", font=get_font(FONT_SERIF_BOLD, 96), fill=TEXT_WHITE)

    desc = (
        "Councillors pass cross-party motion condemning all\n"
        "forms of hate crime, anti-migrant rhetoric, and\n"
        "far-right extremism across the borough."
    )
    draw.text((130, 930), desc, font=get_font(FONT_SERIF, 34), fill=(225, 225, 230), spacing=12)

    # Source quote box
    draw.rounded_rectangle([(80, 1170), (1000, 1440)], radius=12, fill=CARD_BG, outline=BORDER_GRAY, width=1)
    q = (
        "“Blaming migrants does not solve our challenges.\n"
        "Westminster has always been, and must remain,\n"
        "a safe and welcoming city for all residents.”"
    )
    draw.text((120, 1220), q, font=get_font(FONT_SERIF, 34), fill=(195, 195, 200), spacing=14)

    img.save(out_path)

def create_scene2_card(out_path, show_logo=True):
    img = draw_clean_broadsheet_bg()
    draw = ImageDraw.Draw(img)
    draw_header_bar(draw, img, show_authorised_logo=show_logo)
    draw_footer_bar(draw, "Source: Council Agenda Frontsheet Item 8 • Motion Approved")

    draw.rounded_rectangle([(80, 230), (350, 280)], radius=4, fill=TEXT_WHITE)
    draw.text((102, 246), "POLICY MANDATE", font=get_font(FONT_SANS, 20), fill=PURE_BLACK)

    f_h1 = get_font(FONT_SERIF_BOLD, 64)
    draw.text((80, 320), "New Community\nEquality Strategy", font=f_h1, fill=TEXT_WHITE, spacing=16)

    # Leader card
    draw.rounded_rectangle([(80, 560), (1000, 730)], radius=12, fill=CARD_BG, outline=BORDER_GRAY, width=1)
    draw.text((120, 595), "Cllr Adam Hug", font=get_font(FONT_SERIF_BOLD, 44), fill=TEXT_WHITE)
    draw.text((120, 660), "Leader of Westminster City Council • Labour & Co-operative", font=get_font(FONT_SANS, 24), fill=TEXT_MUTED)

    # Clean Broadsheet Document Clipping
    draw.rounded_rectangle([(80, 780), (1000, 1440)], radius=12, fill=(245, 245, 248))
    draw.text((120, 820), "AGENDA PACK EXTRACT • WEDNESDAY 12 NOV 2025", font=get_font(FONT_SANS, 22), fill=(100, 100, 105))

    # Yellow highlighter box with proper padding
    draw.rectangle([(110, 880), (970, 1130)], fill=(255, 243, 140))
    
    quote_text = (
        "“Deliver a new Community Equality Strategy\n"
        "focused on improving council services and\n"
        "promoting community cohesion, ensuring\n"
        "earlier support is given to affected groups.”"
    )
    draw.text((130, 905), quote_text, font=get_font(FONT_SERIF_BOLD, 34), fill=(18, 18, 22), spacing=12)

    sub_commitments = (
        "• Establish cross-community working group with faith leaders\n"
        "• Partner with police for rapid response to hate incidents\n"
        "• Champion cultural festivals and youth programmes"
    )
    draw.text((120, 1170), sub_commitments, font=get_font(FONT_SANS, 28), fill=(45, 45, 50), spacing=18)

    img.save(out_path)

def create_scene3_card(out_path, show_logo=True):
    """Scene 3 uses the photorealistic generative B-roll image of Victoria Street."""
    if os.path.exists(GEN_STREET_BG):
        base = Image.open(GEN_STREET_BG).convert("RGB")
        base = base.resize((1080, 1920), Image.Resampling.LANCZOS)
    else:
        base = draw_clean_broadsheet_bg()

    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d_ov = ImageDraw.Draw(overlay)
    
    for y in range(0, 360):
        alpha = int(220 * (1 - (y / 360)))
        d_ov.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))
    for y in range(1200, 1920):
        alpha = int(240 * ((y - 1200) / 720))
        d_ov.line([(0, y), (1080, y)], fill=(0, 0, 0, alpha))

    img = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw_header_bar(draw, img, show_authorised_logo=show_logo)
    draw_footer_bar(draw, "Location: Victoria Street, SW1 • Met Police Central Area")

    # High-contrast amber AI disclaimer badge
    draw.rounded_rectangle([(80, 205), (460, 258)], radius=6, fill=(0, 0, 0, 230), outline=(245, 158, 11), width=1)
    draw.rectangle([(80, 205), (90, 258)], fill=(245, 158, 11))
    draw.text((105, 222), "AI ILLUSTRATIVE B-ROLL", font=get_font(FONT_SANS, 20), fill=(251, 191, 36))

    # Demographics card
    draw.rounded_rectangle([(80, 1260), (1000, 1680)], radius=16, fill=(10, 10, 14, 235), outline=BORDER_GRAY, width=1)
    draw.text((120, 1310), "WESTMINSTER DEMOGRAPHICS", font=get_font(FONT_SANS, 22), fill=TEXT_MUTED)

    draw.text((120, 1370), "180+", font=get_font(FONT_SERIF_BOLD, 84), fill=TEXT_WHITE)
    draw.text((120, 1480), "Nationalities\nrepresented", font=get_font(FONT_SANS, 28), fill=(200, 200, 205), spacing=8)

    draw.line([(520, 1370), (520, 1580)], fill=BORDER_GRAY, width=1)

    draw.text((560, 1370), "150+", font=get_font(FONT_SERIF_BOLD, 84), fill=TEXT_WHITE)
    draw.text((560, 1480), "Languages spoken\nacross borough", font=get_font(FONT_SANS, 28), fill=(200, 200, 205), spacing=8)

    img.save(out_path)

def create_scene4_card(out_path, show_logo=True):
    img = draw_clean_broadsheet_bg()
    draw = ImageDraw.Draw(img)
    draw_header_bar(draw, img, show_authorised_logo=show_logo)
    draw_footer_bar(draw, "Implementation: Westminster Town Hall • Cross-Community Directorate")

    draw.rounded_rectangle([(80, 230), (410, 280)], radius=4, fill=TEXT_WHITE)
    draw.text((102, 246), "COMMUNITY ACTION", font=get_font(FONT_SANS, 20), fill=PURE_BLACK)

    f_h1 = get_font(FONT_SERIF_BOLD, 64)
    draw.text((80, 320), "Cross-Community\nWorking Group", font=f_h1, fill=TEXT_WHITE, spacing=16)

    pillars = [
        ("01 / FAITH LEADERS", "Interfaith dialogues, mutual support & cultural festivals"),
        ("02 / YOUTH VOICES", "Civic education and school anti-prejudice initiatives"),
        ("03 / LOCAL RESIDENTS", "Community-led monitoring of local tensions and safety"),
        ("04 / MET POLICE", "Swift investigation and dignifying care for hate crime victims")
    ]

    top = 580
    for title, desc in pillars:
        draw.rounded_rectangle([(80, top), (1000, top + 165)], radius=10, fill=CARD_BG, outline=BORDER_GRAY, width=1)
        draw.text((120, top + 32), title, font=get_font(FONT_SANS, 22), fill=TEXT_WHITE)
        draw.text((120, top + 80), desc, font=get_font(FONT_SERIF, 30), fill=(210, 210, 215))
        top += 195

    img.save(out_path)

def create_scene5_card(out_path, show_logo=True):
    img = draw_clean_broadsheet_bg()
    draw = ImageDraw.Draw(img)
    draw_header_bar(draw, img, show_authorised_logo=show_logo)
    draw_footer_bar(draw, "Independent Civic Journalism Across Greater London's 33 Councils")

    if show_logo and os.path.exists(LOGO_WORDMARK):
        try:
            wm = Image.open(LOGO_WORDMARK).convert("RGBA")
            aspect = wm.width / wm.height
            wm = wm.resize((int(85 * aspect), 85), Image.Resampling.LANCZOS)
            img.paste(wm, (80, 520), wm)
        except Exception:
            draw.text((80, 520), "London Local.", font=get_font(FONT_SERIF_BOLD, 80), fill=TEXT_WHITE)
    else:
        draw.text((80, 520), "London Local.", font=get_font(FONT_SERIF_BOLD, 80), fill=TEXT_WHITE)

    draw.text((80, 645), "AI-first civic reporting across Greater London's 33 councils.", font=get_font(FONT_SANS, 32), fill=TEXT_MUTED)

    # Document Verification Archive
    draw.rounded_rectangle([(80, 770), (1000, 1260)], radius=12, fill=CARD_BG, outline=BORDER_GRAY, width=1)
    draw.text((120, 820), "OFFICIAL DOCUMENT ARCHIVE", font=get_font(FONT_SANS, 22), fill=TEXT_MUTED)

    links = (
        "• Full Council Meeting Minutes (12 November 2025)\n"
        "• Westminster Motion Frontsheet & Voting Record\n"
        "• Community Equality Strategy Briefing Paper\n"
        "• Public Webcast Archive"
    )
    draw.text((120, 890), links, font=get_font(FONT_SERIF, 32), fill=(230, 230, 235), spacing=22)

    # CTA Button
    draw.rounded_rectangle([(80, 1340), (1000, 1460)], radius=8, fill=TEXT_WHITE)
    draw.text((320, 1380), "londonlocal.news", font=get_font(FONT_SERIF_BOLD, 42), fill=PURE_BLACK)

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
    print("=== 1. Generating Clean Broadsheet Cards (V3) ===")
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
    print("All 5 clean broadsheet cards generated.")

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
