#!/usr/bin/env python3
"""
London Local News Video Assembly Pipeline (V9 - Modular Multi-Story Broadcast Engine)
Architecture:
- 100% Declarative & Spec-Driven: Zero hardcoded story strings; renders any `specs/*.json` contract
- Five Reusable Broadcast Figure Components:
  1. `vote_tally`: Proportional parliamentary division bar & party breakdown cards
  2. `motion_document`: "Paper-on-Glass" official council order paper with inline yellow marker highlight
  3. `stat_comparison`: Dual glassmorphic metric cards with benchmark progress bars
  4. `action_matrix`: 2x2 connected operational governance grid
  5. `outro_archive`: Structured Public Record Audit Trail table with verification badges & CTA
- Multi-Angle Camera Framing (`full`, `architectural_upper` B-cam punch-in, `pan_zoom` 35mm Ken Burns)
- Alpha-keyed brand masthead (eliminates rectangular background artifacts)
- Frame-accurate 30fps CFR + 24kHz audio normalization across all segments
- Supports single-story (`--spec`) and multi-story simultaneous deployment (`--batch`)
"""

import argparse
import glob
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SPEC = os.path.join(BASE_DIR, "specs/4178-westminster-extremism.json")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
BRANDING_DIR = os.path.join(ASSETS_DIR, "branding")
BUILD_DIR = os.path.join(BASE_DIR, "build")
AUDIO_BASE_DIR = os.path.join(ASSETS_DIR, "audio")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

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
SANS_BOLD_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
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
FONT_SANS_BOLD = resolve_font_path(SANS_BOLD_CANDIDATES) or resolve_font_path(SANS_CANDIDATES)
FONT_SANS = resolve_font_path(SANS_CANDIDATES)

MARGIN_X = 70
SAFE_WIDTH = 1080 - (2 * MARGIN_X)  # 940px


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


def load_transparent_wordmark(target_height=34):
    """Loads london-local-wordmark.png and keys out the dark background to true RGBA alpha."""
    if not os.path.exists(LOGO_WORDMARK):
        return None
    try:
        wm = Image.open(LOGO_WORDMARK).convert("RGBA")
        pixels = wm.load()
        for y in range(wm.height):
            for x in range(wm.width):
                r, g, b, a = pixels[x, y]
                m = max(r, g, b)
                if m <= 24:
                    pixels[x, y] = (r, g, b, 0)
                else:
                    new_a = min(255, int((m - 24) * 255 / 175))
                    pixels[x, y] = (r, g, b, new_a)
        aspect = wm.width / wm.height
        return wm.resize((int(target_height * aspect), target_height), Image.Resampling.LANCZOS)
    except Exception:
        return None


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


def draw_top_bar(
    overlay,
    draw,
    borough="WESTMINSTER",
    date_str="12 NOV 2025",
    scene_num=1,
    total_scenes=5,
    disclaimer=None,
    show_logo=True,
):
    # Top subtle vignette
    for y in range(0, 260):
        alpha = int(195 * (1 - (y / 260)))
        draw.line([(0, y), (1080, y)], fill=(6, 6, 8, alpha))

    # Top progress bar (4px height at y=0..4)
    draw.rectangle([(0, 0), (1080, 5)], fill=(255, 255, 255, 35))
    prog_w = int(1080 * (scene_num / max(1, total_scenes)))
    draw.rectangle([(0, 0), (prog_w, 5)], fill=(255, 82, 56, 230))

    # Left Brand Pill (Unified glass container so wordmark never floats awkwardly)
    wm = load_transparent_wordmark(target_height=34) if show_logo else None
    if wm:
        brand_pill_w = wm.width + 36
        draw.rounded_rectangle(
            [(MARGIN_X, 66), (MARGIN_X + brand_pill_w, 120)],
            radius=27,
            fill=(10, 10, 14, 195),
            outline=(255, 255, 255, 60),
            width=1,
        )
        overlay.paste(wm, (MARGIN_X + 18, 76), wm)
    else:
        f_placeholder = get_font(FONT_SANS_BOLD, 19)
        p_txt = "YOUR LOGO HERE"
        pw = int(draw.textlength(p_txt, font=f_placeholder) + 44)
        draw.rounded_rectangle(
            [(MARGIN_X, 66), (MARGIN_X + pw, 120)],
            radius=27,
            fill=(10, 10, 14, 195),
            outline=(255, 255, 255, 80),
            width=1,
        )
        draw.text((MARGIN_X + 22, 82), p_txt, font=f_placeholder, fill=(220, 220, 225, 255))

    # Right Borough & Date Pill (Mathematically measured)
    f_tag = get_font(FONT_SANS_BOLD, 19)
    tag_text = f"{borough.upper()} • {date_str.upper()}"
    tag_w = draw.textlength(tag_text, font=f_tag)
    pill_w = int(tag_w + 46)
    pill_x2 = 1080 - MARGIN_X
    pill_x1 = pill_x2 - pill_w
    draw.rounded_rectangle(
        [(pill_x1, 66), (pill_x2, 120)],
        radius=27,
        fill=(10, 10, 14, 195),
        outline=(255, 255, 255, 60),
        width=1,
    )
    draw.text((pill_x1 + 23, 83), tag_text, font=f_tag, fill=(240, 240, 245, 255))

    # Optional AI Illustrative Disclaimer Pill (Top-Left Second Row)
    if disclaimer:
        f_ai = get_font(FONT_SANS_BOLD, 15)
        ai_text = disclaimer.upper()
        ai_w = draw.textlength(ai_text, font=f_ai)
        draw.rounded_rectangle(
            [(MARGIN_X, 132), (MARGIN_X + int(ai_w + 52), 168)],
            radius=18,
            fill=(12, 12, 16, 195),
            outline=(245, 158, 11, 210),
            width=1,
        )
        draw.ellipse([(MARGIN_X + 16, 146), (MARGIN_X + 24, 154)], fill=(251, 191, 36, 255))
        draw.text((MARGIN_X + 33, 142), ai_text, font=f_ai, fill=(251, 191, 36, 255))

    # Scene Counter Pill (Top-Right Second Row)
    f_sc = get_font(FONT_SANS_BOLD, 15)
    sc_text = f"SCENE 0{scene_num} / 0{total_scenes}"
    sc_w = draw.textlength(sc_text, font=f_sc)
    sc_x2 = 1080 - MARGIN_X
    sc_x1 = sc_x2 - int(sc_w + 32)
    draw.rounded_rectangle(
        [(sc_x1, 132), (sc_x2, 168)],
        radius=18,
        fill=(12, 12, 16, 175),
        outline=(255, 255, 255, 40),
        width=1,
    )
    draw.text((sc_x1 + 16, 142), sc_text, font=f_sc, fill=(185, 185, 195, 255))


def draw_spatial_postcode_hud(draw, spec, scene_num=1, t=10.0):
    """Renders Frame-1 OCR Postcode Geo-Routing Banner & Scene-1 Spatial Lock-On Reticle."""
    postcode_tag = spec.get("postcodeTag", "")
    coords = spec.get("coordinates", "")
    if not postcode_tag:
        return

    # Top Frame-1 OCR Geo-Routing Bar (y=182..230) so platform vision models route to local postcodes
    bar_y1, bar_y2 = 182, 230
    draw.rounded_rectangle(
        [(MARGIN_X, bar_y1), (1080 - MARGIN_X, bar_y2)],
        radius=12,
        fill=(14, 14, 20, 215),
        outline=(255, 82, 56, 160),
        width=1,
    )

    # Pulsing live location reticle on left
    cx, cy = MARGIN_X + 26, (bar_y1 + bar_y2) // 2
    pulse = (t * 2.2) % 1.0
    p_rad = int(5 + 7 * pulse)
    p_alpha = int(210 * (1.0 - pulse))
    draw.ellipse([(cx - p_rad, cy - p_rad), (cx + p_rad, cy + p_rad)], outline=(255, 82, 56, p_alpha), width=2)
    draw.ellipse([(cx - 5, cy - 5), (cx + 5, cy + 5)], fill=(255, 82, 56, 255))

    f_pc = get_font(FONT_SANS_BOLD, 18)
    draw.text((MARGIN_X + 46, bar_y1 + 13), postcode_tag.upper(), font=f_pc, fill=(255, 255, 255, 255))

    # Right coordinate / citizen brief tag
    f_rt = get_font(FONT_SANS_BOLD, 15)
    rt_txt = "CITIZEN IMPACT BRIEF"
    rw = draw.textlength(rt_txt, font=f_rt)
    draw.text((1080 - MARGIN_X - 20 - rw, bar_y1 + 15), rt_txt, font=f_rt, fill=(251, 191, 36, 255))

    # Scene 1 Spatial Lock-On Reticle in the first 1.8 seconds ("Wait, I know that place!" hook)
    if scene_num == 1 and t <= 1.85 and coords:
        fade = 1.0 if t < 1.35 else max(0.0, (1.85 - t) / 0.5)
        al = int(235 * fade)
        if al > 15:
            rx1, ry1, rx2, ry2 = 180, 440, 900, 535
            draw.rounded_rectangle([(rx1, ry1), (rx2, ry2)], radius=14, fill=(10, 10, 15, int(185 * fade)), outline=(251, 191, 36, al), width=2)
            f_lock = get_font(FONT_SANS_BOLD, 16)
            f_coord = get_font(FONT_SANS_BOLD, 21)
            l_txt = "SPATIAL LOCK · VERIFIED BOROUGH LOCATION"
            lw = draw.textlength(l_txt, font=f_lock)
            draw.text(((1080 - lw) // 2, ry1 + 18), l_txt, font=f_lock, fill=(251, 191, 36, al))
            cw = draw.textlength(coords, font=f_coord)
            draw.text(((1080 - cw) // 2, ry1 + 48), coords, font=f_coord, fill=(255, 255, 255, al))


def draw_bottom_vignette(draw, start_y=940):
    for y in range(start_y, 1920):
        factor = (y - start_y) / (1920 - start_y)
        alpha = int(248 * (factor ** 1.25))
        draw.line([(0, y), (1080, y)], fill=(8, 8, 11, alpha))


def draw_lower_third_text(draw, graphic, citation_footer, top_y=1350):
    f_kicker = get_font(FONT_SANS_BOLD, 21)
    f_h1 = get_font(FONT_SERIF_BOLD, 56)
    f_body = get_font(FONT_SANS, 29)
    f_meta = get_font(FONT_SANS, 19)

    kicker = graphic.get("kicker", "")
    headline = graphic.get("headline", "")
    body = graphic.get("body", "")

    curr_y = top_y
    if kicker:
        clean_kicker = kicker.replace("📍", "").strip()
        draw.text((MARGIN_X, curr_y), clean_kicker.upper(), font=f_kicker, fill=(251, 191, 36, 255))
        curr_y += 34

    h1_lines = wrap_text_to_width(draw, headline, f_h1, SAFE_WIDTH)
    for hl in h1_lines[:2]:
        draw.text((MARGIN_X, curr_y), hl, font=f_h1, fill=(255, 255, 255, 255))
        curr_y += 64

    curr_y += 12
    b_lines = wrap_text_to_width(draw, body, f_body, SAFE_WIDTH)
    for bl in b_lines[:3]:
        draw.text((MARGIN_X, curr_y), bl, font=f_body, fill=(225, 225, 232, 255))
        curr_y += 39

    # Citation Rule & Footer
    rule_y = 1700
    draw.line([(MARGIN_X, rule_y), (1080 - MARGIN_X, rule_y)], fill=(255, 255, 255, 45), width=1)
    cite_lines = wrap_text_to_width(draw, citation_footer, f_meta, SAFE_WIDTH)
    if cite_lines:
        draw.text((MARGIN_X, rule_y + 22), cite_lines[0], font=f_meta, fill=(165, 165, 175, 255))


# ==============================================================================
# MODULAR INTELLIGENT FIGURE RENDERERS
# ==============================================================================


def ease_out_cubic(t):
    t_clamped = max(0.0, min(1.0, float(t)))
    return 1.0 - ((1.0 - t_clamped) ** 3)


def draw_vector_check(draw, x, y, color, size=14):
    """Draws a crisp anti-aliased vector checkmark so fonts never render missing glyph boxes."""
    p1 = (x, y + int(size * 0.55))
    p2 = (x + int(size * 0.36), y + int(size * 0.90))
    p3 = (x + size, y + int(size * 0.12))
    draw.line([p1, p2, p3], fill=color, width=3)


def render_figure_vote_tally(draw, fig_data, t=10.0):
    """Renders proportional parliamentary division bar & party breakdown HUD with counting animation."""
    fig_y1, fig_y2 = 1090, 1315
    draw.rounded_rectangle(
        [(MARGIN_X, fig_y1), (1080 - MARGIN_X, fig_y2)],
        radius=16,
        fill=(16, 16, 22, 228),
        outline=(255, 255, 255, 65),
        width=1,
    )

    f_hdr = get_font(FONT_SANS_BOLD, 18)
    hdr_left = fig_data.get("headerLeft", "CHAMBER DIVISION TALLY")
    raw_right = fig_data.get("headerRight", "MOTION CARRIED").replace("✓", "").strip()
    draw.text((MARGIN_X + 26, fig_y1 + 20), hdr_left, font=f_hdr, fill=(245, 158, 11, 255))

    # Badge pops in with scale/opacity after vote bar fills (t >= 0.75s)
    if t >= 0.75:
        rw = draw.textlength(raw_right, font=f_hdr)
        rx = int(1080 - MARGIN_X - 26 - rw)
        chk_col = (52, 211, 153, 255)
        draw_vector_check(draw, rx - 22, fig_y1 + 22, chk_col, size=14)
        draw.text((rx, fig_y1 + 20), raw_right, font=f_hdr, fill=chk_col)

    parties = fig_data.get("parties", [])
    total_seats = sum(max(1, p.get("seats", 1)) for p in parties) or 1
    bar_x1 = MARGIN_X + 26
    bar_x2 = 1080 - MARGIN_X - 26
    bar_total_w = bar_x2 - bar_x1
    bar_y1, bar_y2 = fig_y1 + 56, fig_y1 + 72

    # Animated bar fill (0.0s -> 0.85s)
    bar_anim = ease_out_cubic(t / 0.85)
    anim_total_w = int(bar_total_w * bar_anim)

    # Proportional segmented bar
    curr_x = bar_x1
    for idx, p in enumerate(parties):
        seats = max(1, p.get("seats", 1))
        col = tuple(p.get("color", [52, 211, 153])) + (255,)
        seg_w = int(anim_total_w * (seats / total_seats))
        if idx == len(parties) - 1:
            seg_end = bar_x1 + anim_total_w
        else:
            seg_end = curr_x + seg_w - 4
        if seg_end > curr_x + 4:
            draw.rounded_rectangle([(curr_x, bar_y1), (seg_end, bar_y2)], radius=6, fill=col)
        curr_x = seg_end + 6

    # Party breakdown cards (count up seats in sync with bar)
    card_w = (bar_total_w - 20) // 2
    for idx, p in enumerate(parties[:2]):
        px = bar_x1 + idx * (card_w + 20)
        py1, py2 = fig_y1 + 90, fig_y2 - 20
        col = tuple(p.get("color", [52, 211, 153])) + (255,)
        draw.rounded_rectangle(
            [(px, py1), (px + card_w, py2)],
            radius=10,
            fill=(28, 28, 36, 240),
            outline=(255, 255, 255, 35),
            width=1,
        )
        draw.rounded_rectangle([(px, py1), (px + 8, py2)], radius=4, fill=col)
        draw.text((px + 22, py1 + 14), p.get("name", ""), font=get_font(FONT_SANS_BOLD, 17), fill=col)
        
        # Counting numbers
        final_seats = p.get("seats", 0)
        display_seats = int(final_seats * bar_anim)
        status_txt = p.get("status", "")
        if "AYE" in status_txt:
            status_display = f"{display_seats} AYE · {status_txt.split('·')[-1].strip()}"
        else:
            status_display = status_txt
            
        draw.text(
            (px + 22, py1 + 42),
            f"{display_seats} Seats  •  {status_display}",
            font=get_font(FONT_SANS_BOLD, 21),
            fill=(240, 240, 245, 255),
        )


def render_figure_motion_document(draw, fig_data, t=10.0):
    """Renders an authentic 'Paper-on-Glass' municipal order paper card with live-drawing yellow highlight."""
    # Smooth subtle entrance slide (0.0s -> 0.4s)
    slide_p = ease_out_cubic(t / 0.4)
    y_offset = int((1.0 - slide_p) * 40)
    fig_y1, fig_y2 = 1040 + y_offset, 1325 + y_offset

    # Subtle drop shadow
    draw.rounded_rectangle(
        [(MARGIN_X + 6, fig_y1 + 8), (1080 - MARGIN_X + 6, fig_y2 + 8)],
        radius=14,
        fill=(0, 0, 0, 160),
    )
    # Warm archival broadsheet paper card
    paper_bg = (248, 246, 240, 250)
    ink_dark = (18, 18, 22, 255)
    ink_muted = (85, 85, 95, 255)
    draw.rounded_rectangle(
        [(MARGIN_X, fig_y1), (1080 - MARGIN_X, fig_y2)],
        radius=14,
        fill=paper_bg,
        outline=(200, 195, 185, 255),
        width=2,
    )

    # Top Order Paper Masthead
    f_doc_hdr = get_font(FONT_SANS_BOLD, 17)
    left_hdr = fig_data.get("docHeaderLeft", "COUNCIL ORDER PAPER")
    right_hdr = fig_data.get("docHeaderRight", "OFFICIAL RECORD")
    draw.text((MARGIN_X + 28, fig_y1 + 18), left_hdr, font=f_doc_hdr, fill=ink_muted)
    rw = draw.textlength(right_hdr, font=f_doc_hdr)
    draw.text((1080 - MARGIN_X - 28 - rw, fig_y1 + 18), right_hdr, font=f_doc_hdr, fill=(180, 83, 9, 255))

    # Double parliamentary rule
    draw.line([(MARGIN_X + 28, fig_y1 + 46), (1080 - MARGIN_X - 28, fig_y1 + 46)], fill=(40, 40, 45, 220), width=2)
    draw.line([(MARGIN_X + 28, fig_y1 + 51), (1080 - MARGIN_X - 28, fig_y1 + 51)], fill=(40, 40, 45, 120), width=1)

    # Excerpt with live-drawing highlighted phrase (starts at t=1.0s, sweeps across over 1.6s)
    prefix = fig_data.get("excerptPrefix", "")
    highlight = fig_data.get("highlightPhrase", "")
    suffix = fig_data.get("excerptSuffix", "")
    full_quote = f"{prefix}{highlight}{suffix}"

    f_quote = get_font(FONT_SERIF_BOLD, 27)
    max_qw = SAFE_WIDTH - 56
    q_lines = wrap_text_to_width(draw, full_quote, f_quote, max_qw)

    # Calculate live highlight sweep progress
    hl_progress = ease_out_cubic(max(0.0, min(1.0, (t - 0.9) / 1.7))) if t >= 0.9 else 0.0

    # Red-Pen Audit Bracket on the left margin of the excerpt
    if hl_progress > 0.1:
        bracket_h = int(105 * hl_progress)
        draw.line([(MARGIN_X + 16, fig_y1 + 64), (MARGIN_X + 16, fig_y1 + 64 + bracket_h)], fill=(220, 38, 38, 240), width=4)
        draw.line([(MARGIN_X + 16, fig_y1 + 64), (MARGIN_X + 24, fig_y1 + 64)], fill=(220, 38, 38, 240), width=3)

    qy = fig_y1 + 66
    for ql in q_lines[:3]:
        hl_words = [w for w in highlight.split(" ") if len(w) > 3]
        if any(hw in ql for hw in hl_words):
            lw = draw.textlength(ql, font=f_quote)
            # Sweeping highlight rectangle
            current_hl_w = int(lw * hl_progress)
            if current_hl_w > 4:
                draw.rounded_rectangle(
                    [(MARGIN_X + 24, qy - 2), (MARGIN_X + 28 + current_hl_w, qy + 32)],
                    radius=4,
                    fill=(253, 224, 71, 235),
                )
        draw.text((MARGIN_X + 28, qy), ql, font=f_quote, fill=ink_dark)
        qy += 38

    # Signatories Footer Bar inside paper card
    sig_y = fig_y2 - 52
    draw.line([(MARGIN_X + 28, sig_y - 8), (1080 - MARGIN_X - 28, sig_y - 8)], fill=(200, 195, 185, 255), width=1)
    f_sig = get_font(FONT_SANS_BOLD, 18)
    mover = fig_data.get("mover", "")
    seconder = fig_data.get("seconder", "")
    sig_line = f"{mover}   •   {seconder}"
    draw.text((MARGIN_X + 28, sig_y + 4), sig_line, font=f_sig, fill=(45, 45, 55, 255))

    # Receipts Journalism Stamp Badge (pops onto bottom-right of order paper at t >= 1.6s)
    receipt_stamp = fig_data.get("receiptStamp", "")
    if receipt_stamp and t >= 1.6:
        f_stamp = get_font(FONT_SANS_BOLD, 16)
        st_w = draw.textlength(receipt_stamp, font=f_stamp)
        st_box_w = int(st_w + 32)
        st_x2 = 1080 - MARGIN_X - 24
        st_x1 = st_x2 - st_box_w
        st_y = sig_y - 4
        draw.rounded_rectangle([(st_x1, st_y), (st_x2, st_y + 36)], radius=6, fill=(254, 242, 242, 245), outline=(220, 38, 38, 240), width=2)
        draw.text((st_x1 + 16, st_y + 9), receipt_stamp, font=f_stamp, fill=(220, 38, 38, 255))


def render_figure_stat_comparison(draw, fig_data, t=10.0):
    """Renders dual floating glassmorphic metric cards with staggered entry and progressive bar fills."""
    fig_y1, fig_y2 = 1055, 1320
    cards = fig_data.get("cards", [])
    card_w = (SAFE_WIDTH - 24) // 2

    for idx, c in enumerate(cards[:2]):
        # Staggered slide in: card 0 at t=0.0..0.4s, card 1 at t=0.3..0.7s
        card_t = t - (idx * 0.28)
        card_p = ease_out_cubic(card_t / 0.45) if card_t > 0 else 0.0
        if card_p <= 0.01:
            continue

        cx = MARGIN_X + idx * (card_w + 24)
        y_slide = int((1.0 - card_p) * 60)
        py1, py2 = fig_y1 + y_slide, fig_y2 + y_slide

        draw.rounded_rectangle(
            [(cx, py1), (cx + card_w, py2)],
            radius=16,
            fill=(14, 14, 20, 232),
            outline=(255, 255, 255, 65),
            width=1,
        )
        bar_col = tuple(c.get("barColor", [245, 158, 11])) + (255,)
        draw.text((cx + 26, py1 + 20), c.get("kicker", ""), font=get_font(FONT_SANS_BOLD, 16), fill=bar_col)
        draw.text((cx + 26, py1 + 44), c.get("value", ""), font=get_font(FONT_SERIF_BOLD, 70), fill=(255, 255, 255, 255))
        draw.text((cx + 26, py1 + 132), c.get("label", ""), font=get_font(FONT_SANS_BOLD, 22), fill=(235, 235, 240, 255))

        # Benchmark bar fills progressively
        bar_p = ease_out_cubic((card_t - 0.2) / 0.7) if card_t > 0.2 else 0.0
        bx1, bx2 = cx + 26, cx + card_w - 26
        by1, by2 = py1 + 174, py1 + 184
        draw.rounded_rectangle([(bx1, by1), (bx2, by2)], radius=5, fill=(45, 45, 55, 255))
        ratio = max(0.1, min(1.0, float(c.get("barRatio", 0.85)))) * bar_p
        fill_w = int((bx2 - bx1) * ratio)
        if fill_w > 4:
            draw.rounded_rectangle([(bx1, by1), (bx1 + fill_w, by2)], radius=5, fill=bar_col)

        draw.text((cx + 26, py1 + 198), c.get("subtext", ""), font=get_font(FONT_SANS, 17), fill=(175, 175, 185, 255))


def render_figure_action_matrix(draw, fig_data, t=10.0):
    """Renders a 2x2 connected civic governance grid with staggered pillar entrances."""
    hdr_p = ease_out_cubic(t / 0.35)
    hdr_y1, hdr_y2 = 1005, 1052
    draw.rounded_rectangle(
        [(MARGIN_X, hdr_y1), (MARGIN_X + int((SAFE_WIDTH) * hdr_p), hdr_y2)],
        radius=10,
        fill=(245, 158, 11, 230),
    )
    if hdr_p > 0.6:
        f_mhdr = get_font(FONT_SANS_BOLD, 18)
        m_title = fig_data.get("matrixHeader", "MANDATED COALITION · 4 OPERATIONAL PILLARS")
        mw = draw.textlength(m_title, font=f_mhdr)
        draw.text(((1080 - mw) // 2, hdr_y1 + 13), m_title, font=f_mhdr, fill=(12, 12, 16, 255))

    grid_y = 1066
    gw = (SAFE_WIDTH - 20) // 2
    gh = 118
    pillars = fig_data.get("pillars", [])

    for idx, p in enumerate(pillars[:4]):
        # Staggered entry every 0.18s
        pil_t = t - (0.2 + idx * 0.18)
        pil_p = ease_out_cubic(pil_t / 0.35) if pil_t > 0 else 0.0
        if pil_p <= 0.01:
            continue

        col_idx = idx % 2
        row_idx = idx // 2
        px = MARGIN_X + col_idx * (gw + 20)
        y_slide = int((1.0 - pil_p) * 35)
        py = grid_y + row_idx * (gh + 14) + y_slide

        draw.rounded_rectangle(
            [(px, py), (px + gw, py + gh)],
            radius=12,
            fill=(16, 16, 22, 228),
            outline=(255, 255, 255, 55),
            width=1,
        )
        draw.text((px + 20, py + 16), p.get("code", ""), font=get_font(FONT_SANS_BOLD, 18), fill=(245, 158, 11, 255))
        d_lines = wrap_text_to_width(draw, p.get("desc", ""), get_font(FONT_SANS, 20), gw - 40)
        dy = py + 46
        for dl in d_lines[:2]:
            draw.text((px + 20, dy), dl, font=get_font(FONT_SANS, 20), fill=(230, 230, 235, 255))
            dy += 26


def create_scene_overlay_image(spec, scene, total_scenes=5, show_logo=True, t=10.0):
    """Generates a complete broadcast overlay PIL Image for a timeline scene at time t."""
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    borough = spec.get("borough", "Westminster")
    date_str = spec.get("meetingDateDisplay", spec.get("meetingDate", "12 NOV 2025"))
    scene_num = scene.get("sceneNumber", 1)
    vis = scene.get("visualAsset", {})
    disclaimer = vis.get("mandatoryDisclaimer") if vis.get("isIllustrative") else None

    draw_top_bar(
        overlay,
        draw,
        borough=borough,
        date_str=date_str,
        scene_num=scene_num,
        total_scenes=total_scenes,
        disclaimer=disclaimer,
        show_logo=show_logo,
    )
    draw_spatial_postcode_hud(draw, spec, scene_num=scene_num, t=t)
    draw_bottom_vignette(draw, start_y=920)

    fig = scene.get("figure", {})
    fig_type = fig.get("type", "")
    fig_data = fig.get("data", {})

    if fig_type == "vote_tally":
        render_figure_vote_tally(draw, fig_data, t=t)
    elif fig_type == "motion_document":
        render_figure_motion_document(draw, fig_data, t=t)
    elif fig_type == "stat_comparison":
        render_figure_stat_comparison(draw, fig_data, t=t)
    elif fig_type == "action_matrix":
        render_figure_action_matrix(draw, fig_data, t=t)

    draw_lower_third_text(
        draw,
        scene.get("onScreenGraphic", {}),
        scene.get("citationFooter", ""),
        top_y=1350,
    )
    return overlay


def create_scene_overlay(out_path, spec, scene, total_scenes=5, show_logo=True):
    """Generates the static broadcast overlay PNG for fallback / testing."""
    img = create_scene_overlay_image(spec, scene, total_scenes=total_scenes, show_logo=show_logo, t=10.0)
    img.save(out_path)


def create_outro_archive_card_image(spec, scene, total_scenes=5, show_logo=True, t=10.0):
    """Renders the Scene 5 Broadsheet Audit Trail & Endplate card with sequential row entrances."""
    img = Image.new("RGBA", (1080, 1920), (10, 10, 14, 255))
    draw = ImageDraw.Draw(img)

    # Subtle vertical editorial gradient + fine grid lines
    for y in range(0, 1920):
        val = int(10 + (y / 1920) * 14)
        draw.line([(0, y), (1080, y)], fill=(val, val, val + 3, 255))

    borough = spec.get("borough", "Westminster")
    date_str = spec.get("meetingDateDisplay", spec.get("meetingDate", "12 NOV 2025"))
    draw_top_bar(
        img,
        draw,
        borough=borough,
        date_str=date_str,
        scene_num=total_scenes,
        total_scenes=total_scenes,
        disclaimer=None,
        show_logo=show_logo,
    )

    fig_data = scene.get("figure", {}).get("data", {})
    ox = MARGIN_X

    # Large Alpha-Keyed Wordmark Masthead
    wm_large = load_transparent_wordmark(target_height=64) if show_logo else None
    if wm_large:
        img.paste(wm_large, (ox, 340), wm_large)
    else:
        draw.text((ox, 340), "London Local.", font=get_font(FONT_SERIF_BOLD, 68), fill=(255, 255, 255, 255))

    tagline = fig_data.get("tagline", "Independent civic intelligence across London's 33 councils.")
    draw.text((ox, 435), tagline, font=get_font(FONT_SANS, 27), fill=(190, 190, 200, 255))
    draw.line([(ox, 500), (1080 - ox, 500)], fill=(255, 255, 255, 45), width=1)

    # Audit Table Header
    audit_hdr = fig_data.get("auditHeader", "PUBLIC RECORD AUDIT TRAIL")
    draw.text((ox, 530), audit_hdr, font=get_font(FONT_SANS_BOLD, 21), fill=(245, 158, 11, 255))

    records = fig_data.get("records", [])
    ry = 568
    for idx, rec in enumerate(records[:3]):
        row_t = t - (0.15 + idx * 0.22)
        row_p = ease_out_cubic(row_t / 0.35) if row_t > 0 else 0.0
        if row_p <= 0.01:
            continue

        card_h = 132
        y_slide = int((1.0 - row_p) * 40)
        cy1, cy2 = ry + y_slide, ry + card_h + y_slide

        draw.rounded_rectangle(
            [(ox, cy1), (1080 - ox, cy2)],
            radius=14,
            fill=(20, 20, 28, 255),
            outline=(255, 255, 255, 50),
            width=1,
        )
        # Code pill
        code_txt = rec.get("code", "DOC")
        draw.text((ox + 26, cy1 + 18), code_txt, font=get_font(FONT_SANS_BOLD, 17), fill=(160, 160, 175, 255))

        # Status badge on right (with vector checkmark so fonts never render missing glyph boxes)
        badge_label = rec.get("badge", "VERIFIED").replace("✓", "").strip()
        b_col = tuple(rec.get("badgeColor", [52, 211, 153])) + (255,)
        f_badge = get_font(FONT_SANS_BOLD, 16)
        bw = int(draw.textlength(badge_label, font=f_badge) + 52)
        bx2 = 1080 - ox - 24
        bx1 = bx2 - bw
        draw.rounded_rectangle([(bx1, cy1 + 14), (bx2, cy1 + 46)], radius=16, fill=(12, 12, 16, 255), outline=b_col, width=1)
        draw_vector_check(draw, bx1 + 15, cy1 + 23, b_col, size=12)
        draw.text((bx1 + 33, cy1 + 21), badge_label, font=f_badge, fill=b_col)

        # Document Title (Wrapped cleanly inside card)
        f_title = get_font(FONT_SERIF, 26)
        t_lines = wrap_text_to_width(draw, rec.get("title", ""), f_title, SAFE_WIDTH - 52)
        ty = cy1 + 54
        for tl in t_lines[:2]:
            draw.text((ox + 26, ty), tl, font=f_title, fill=(240, 240, 245, 255))
            ty += 34

        ry += card_h + 16

    # Community Debate & Stakeholder Ping Box (y=1015..1175)
    stakeholders = spec.get("stakeholderTags", [])
    debate_prompt = spec.get("debatePrompt", "")
    if stakeholders or debate_prompt:
        box_y1, box_y2 = 1015, 1175
        draw.rounded_rectangle([(ox, box_y1), (1080 - ox, box_y2)], radius=14, fill=(18, 18, 26, 255), outline=(251, 191, 36, 120), width=1)
        
        # Header / Label
        f_deb_hdr = get_font(FONT_SANS_BOLD, 15)
        draw.text((ox + 24, box_y1 + 16), "COMMUNITY DEBATE · REPOST & TAG YOUR COUNCILLORS", font=f_deb_hdr, fill=(251, 191, 36, 255))
        
        # Debate prompt question
        if debate_prompt:
            f_deb_q = get_font(FONT_SERIF_BOLD, 26)
            q_lines = wrap_text_to_width(draw, debate_prompt, f_deb_q, SAFE_WIDTH - 48)
            qy = box_y1 + 44
            for ql in q_lines[:2]:
                draw.text((ox + 24, qy), ql, font=f_deb_q, fill=(255, 255, 255, 255))
                qy += 34
                
        # Stakeholder pills
        if stakeholders:
            px = ox + 24
            pill_y = box_y2 - 42
            f_pill = get_font(FONT_SANS_BOLD, 15)
            for st in stakeholders[:3]:
                pw = int(draw.textlength(st, font=f_pill) + 24)
                if px + pw > 1080 - ox - 20:
                    break
                draw.rounded_rectangle([(px, pill_y), (px + pw, pill_y + 28)], radius=14, fill=(35, 35, 48, 255), outline=(255, 255, 255, 40), width=1)
                draw.text((px + 12, pill_y + 6), st, font=f_pill, fill=(210, 210, 225, 255))
                px += pw + 12

    # Elevated CTA Pill Button (slides in at t >= 0.8s)
    cta_t = t - 0.75
    cta_p = ease_out_cubic(cta_t / 0.45) if cta_t > 0 else 0.0
    if cta_p > 0.01:
        y_slide = int((1.0 - cta_p) * 50)
        by = 1200 + y_slide
        pill_h = 130
        draw.rounded_rectangle([(ox, by), (1080 - ox, by + pill_h)], radius=18, fill=(255, 255, 255, 255))
        f_kicker = get_font(FONT_SANS_BOLD, 18)
        f_url = get_font(FONT_SERIF_BOLD, 38)

        kicker_txt = fig_data.get("ctaKicker", "READ THE FULL VERIFIED COUNCIL RECORD")
        k_w = draw.textlength(kicker_txt, font=f_kicker)
        draw.text(((1080 - k_w) // 2, by + 26), kicker_txt, font=f_kicker, fill=(100, 100, 110, 255))

        url_txt = fig_data.get("ctaUrl", "londonlocal.news")
        u_w = draw.textlength(url_txt, font=f_url)
        draw.text(((1080 - u_w) // 2, by + 62), url_txt, font=f_url, fill=(12, 12, 16, 255))

    # Footer citation
    draw_lower_third_footer_only(draw, scene.get("citationFooter", "SOURCE: London Local Civic Archive"))
    return img


def create_outro_archive_card(out_path, spec, scene, total_scenes=5, show_logo=True):
    """Renders the static Scene 5 Broadsheet Audit Trail & Endplate card (fallback)."""
    img = create_outro_archive_card_image(spec, scene, total_scenes=total_scenes, show_logo=show_logo, t=10.0)
    img.convert("RGB").save(out_path)


def draw_lower_third_footer_only(draw, citation_footer):
    f_meta = get_font(FONT_SANS, 19)
    rule_y = 1700
    draw.line([(MARGIN_X, rule_y), (1080 - MARGIN_X, rule_y)], fill=(255, 255, 255, 45), width=1)
    draw.text((MARGIN_X, rule_y + 22), citation_footer, font=f_meta, fill=(165, 165, 175, 255))


# ==============================================================================
# AUDIO SYNTHESIS & CACHING
# ==============================================================================


def generate_story_audio(spec, story_audio_dir, force_refresh=False):
    os.makedirs(story_audio_dir, exist_ok=True)
    voice = spec.get("branding", {}).get("voiceProfile", "en-GB-SoniaNeural")
    if voice == "en-GB-Neural2-B":
        voice = "en-GB-SoniaNeural"

    timings = []
    for scene in spec.get("timeline", []):
        num = scene["sceneNumber"]
        text = scene["voiceoverText"]
        out_mp3 = os.path.join(story_audio_dir, f"scene_{num}.mp3")

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
                    time.sleep(1.2)

            if not success:
                try:
                    cmd = ["edge-tts", "--voice", "en-GB-LibbyNeural", "--text", text, "--write-media", out_mp3]
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    success = True
                except Exception:
                    pass

            if not success and (not os.path.exists(out_mp3) or os.path.getsize(out_mp3) < 1000):
                dur_target = str(scene.get("durationSeconds", 7.0))
                cmd = [
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                    "-t", dur_target, "-c:a", "libmp3lame", "-b:a", "48k", out_mp3,
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        probe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", out_mp3,
        ]
        res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        dur = float(res.stdout.strip())
        timings.append((num, dur, out_mp3))

    return timings


# ==============================================================================
# MASTER VIDEO PIPELINE RENDERER
# ==============================================================================


def render_story_from_spec(spec_path, show_logo=True, force_tts=False):
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    video_id = spec.get("videoId", "sample_video")
    story_id = str(spec.get("storyId", "4178"))
    borough = spec.get("borough", "Westminster")
    timeline = spec.get("timeline", [])
    total_scenes = len(timeline)

    story_build_dir = os.path.join(BUILD_DIR, video_id)
    os.makedirs(story_build_dir, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Maintain backward compatibility with root assets/audio for story 4178
    if story_id == "4178":
        story_audio_dir = AUDIO_BASE_DIR
    else:
        story_audio_dir = os.path.join(AUDIO_BASE_DIR, video_id)

    print(f"\n==================================================================")
    print(f"🎬 BUILDING LONDON LOCAL BROADCAST REEL: {borough.upper()} (#{story_id})")
    print(f"   Spec: {os.path.relpath(spec_path, BASE_DIR)}")
    print(f"==================================================================")

    print("=== 1. Synthesising / Verifying BBC Broadcast Audio (en-GB-SoniaNeural) ===")
    timings = generate_story_audio(spec, story_audio_dir, force_refresh=force_tts)

    print("=== 2. Rendering Declarative Broadcast Figures & Overlays ===")
    segment_files = []

    for idx, scene in enumerate(timeline):
        num = scene["sceneNumber"]
        _, dur, mp3_path = timings[idx]
        pad_dur = dur + 0.35
        seg_out = os.path.join(story_build_dir, f"seg_{num}.mp4")

        vis = scene.get("visualAsset", {})
        vis_type = vis.get("type", "solid")
        vis_src = os.path.join(BASE_DIR, vis.get("source", ""))
        crop_mode = vis.get("cropMode", "full")
        trim_start = float(vis.get("trimStart", 0.0))

        if scene.get("type") == "outro_archive" or scene.get("figure", {}).get("type") == "outro_archive":
            total_frames = int(pad_dur * 30)
            cmd = [
                "ffmpeg", "-y",
                "-f", "rawvideo", "-pix_fmt", "rgba", "-s", "1080x1920", "-r", "30", "-i", "-",
                "-i", mp3_path,
                "-map", "0:v", "-map", "1:a",
                "-r", "30",
                "-c:v", "libx264", "-t", f"{pad_dur:.3f}",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-ar", "24000", "-ac", "1", "-b:a", "192k",
                seg_out,
            ]
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for f_idx in range(total_frames):
                t_sec = f_idx / 30.0
                frame_img = create_outro_archive_card_image(spec, scene, total_scenes=total_scenes, show_logo=show_logo, t=t_sec)
                proc.stdin.write(frame_img.tobytes())
            proc.stdin.close()
            proc.wait()
            segment_files.append(seg_out)
            print(f"  ✓ Scene {num} [Outro Archive - Animated Slide] encoded ({pad_dur:.2f}s @ 30fps)")
            continue

        if vis_type == "video" and os.path.exists(vis_src):
            if crop_mode == "architectural_upper":
                # B-Camera close-up punch-in on upper neoclassical columns & coat of arms
                vf_chain = (
                    "[0:v]crop=iw*0.80:ih*0.48:iw*0.10:0,"
                    "scale=1080:1920:force_original_aspect_ratio=increase,"
                    "crop=1080:1920,"
                    "eq=contrast=1.06:brightness=-0.03:saturation=0.85,"
                    "fps=30[vid];"
                    "[vid][1:v]overlay=0:0[outv]"
                )
            else:
                vf_chain = (
                    "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                    "crop=1080:1920,"
                    "fps=30[vid];"
                    "[vid][1:v]overlay=0:0[outv]"
                )

            cmd = [
                "ffmpeg", "-y",
                "-stream_loop", "-1",
                "-ss", f"{trim_start:.2f}",
                "-i", vis_src,
                "-f", "rawvideo", "-pix_fmt", "rgba", "-s", "1080x1920", "-r", "30", "-i", "-",
                "-i", mp3_path,
                "-filter_complex", vf_chain,
                "-map", "[outv]", "-map", "2:a",
                "-r", "30",
                "-c:v", "libx264", "-t", f"{pad_dur:.3f}",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-ar", "24000", "-ac", "1", "-b:a", "192k",
                seg_out,
            ]
            total_frames = int(pad_dur * 30)
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for f_idx in range(total_frames):
                t_sec = f_idx / 30.0
                frame_img = create_scene_overlay_image(spec, scene, total_scenes=total_scenes, show_logo=show_logo, t=t_sec)
                proc.stdin.write(frame_img.tobytes())
            proc.stdin.close()
            proc.wait()
            segment_files.append(seg_out)
            fig_label = scene.get("figure", {}).get("type", "overlay")
            print(f"  ✓ Scene {num} [Video: {crop_mode} + Animated Figure: {fig_label}] encoded ({pad_dur:.2f}s @ 30fps)")

        elif os.path.exists(vis_src):
            # Dynamic 35mm documentary camera drift + optical film grain + animated figure overlay
            if num % 2 == 1:
                pan_expr = "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)-(on/120)*10'"
            else:
                pan_expr = "x='iw/2-(iw/zoom/2)+(on/120)*12':y='ih/2-(ih/zoom/2)'"

            vf_chain = (
                f"[0:v]scale=1200:2133:force_original_aspect_ratio=increase,"
                f"zoompan=z='min(zoom+0.0005,1.06)':{pan_expr}:d=1:s=1080x1920:fps=30,"
                f"eq=brightness=-0.05:contrast=1.07:saturation=0.92,"
                f"noise=alls=8:allf=t+u[bg];"
                f"[bg][1:v]overlay=0:0[outv]"
            )
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", vis_src,
                "-f", "rawvideo", "-pix_fmt", "rgba", "-s", "1080x1920", "-r", "30", "-i", "-",
                "-i", mp3_path,
                "-filter_complex", vf_chain,
                "-map", "[outv]", "-map", "2:a",
                "-r", "30",
                "-c:v", "libx264", "-t", f"{pad_dur:.3f}",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-ar", "24000", "-ac", "1", "-b:a", "192k",
                seg_out,
            ]
            total_frames = int(pad_dur * 30)
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for f_idx in range(total_frames):
                t_sec = f_idx / 30.0
                frame_img = create_scene_overlay_image(spec, scene, total_scenes=total_scenes, show_logo=show_logo, t=t_sec)
                proc.stdin.write(frame_img.tobytes())
            proc.stdin.close()
            proc.wait()
            segment_files.append(seg_out)
            fig_label = scene.get("figure", {}).get("type", "overlay")
            print(f"  ✓ Scene {num} [35mm Drift+Grain + Animated Figure: {fig_label}] encoded ({pad_dur:.2f}s @ 30fps)")

    print("=== 3. Concatenating Frame-Accurate 30fps Master MP4 ===")
    concat_list = os.path.join(story_build_dir, "concat_list.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for seg in segment_files:
            f.write(f"file '{seg}'\n")

    story_output = os.path.join(OUTPUT_DIR, f"{video_id}.mp4")
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        story_output,
    ]
    subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # If rendering flagship story 4178, also update canonical sample_video_4178_editorial.mp4
    if story_id == "4178":
        canonical_out = os.path.join(OUTPUT_DIR, "sample_video_4178_editorial.mp4")
        subprocess.run(["cp", story_output, canonical_out], check=True)
        story_output = canonical_out

    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
        "-of", "default=noprint_wrappers=1", story_output,
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    print(f"✅ Master Rendered: {story_output}")
    print(res.stdout.strip())

    # Automatically update stream-optimized faststart MP4 in demos/
    demo_map = {
        "4178": "westminster_4178_broadcast.mp4",
        "4182": "camden_4182_broadcast.mp4",
        "4185": "southwark_4185_broadcast.mp4",
    }
    if story_id in demo_map:
        demos_dir = os.path.join(BASE_DIR, "demos")
        os.makedirs(demos_dir, exist_ok=True)
        demo_target = os.path.join(demos_dir, demo_map[story_id])
        tmp_target = os.path.join("/tmp", f"opt_{demo_map[story_id]}")
        print(f"📦 Encoding web-stream faststart demo: {demo_map[story_id]}...")
        opt_cmd = [
            "ffmpeg", "-y",
            "-i", story_output,
            "-c:v", "libx264", "-crf", "28", "-preset", "medium",
            "-c:a", "aac", "-b:a", "112k",
            "-movflags", "+faststart",
            tmp_target,
        ]
        subprocess.run(opt_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.replace(tmp_target, demo_target)
        d_size = os.path.getsize(demo_target) / (1024 * 1024)
        print(f"  ✓ {demo_map[story_id]} ({d_size:.2f} MB, faststart ready)")

    return story_output


def main():
    parser = argparse.ArgumentParser(description="London Local Modular Broadcast Video Engine (V9)")
    parser.add_argument("--spec", type=str, default=DEFAULT_SPEC, help="Path to story JSON specification")
    parser.add_argument("--batch", action="store_true", help="Render all story specs in specs/*.json")
    parser.add_argument("--show-authorised-logo", type=str, default="True", help="True for London Local logo, False for placeholder")
    parser.add_argument("--force-tts", action="store_true", help="Force re-synthesis of TTS audio")
    args = parser.parse_args()

    show_logo = str(args.show_authorised_logo).lower() not in ("false", "0", "no")

    if args.batch:
        spec_files = sorted(glob.glob(os.path.join(BASE_DIR, "specs/*.json")))
        print(f"🚀 Simultaneous Multi-Story Batch Mode: Found {len(spec_files)} story specs")
        outputs = []
        for sp in spec_files:
            out = render_story_from_spec(sp, show_logo=show_logo, force_tts=args.force_tts)
            outputs.append(out)
        print("\n==================================================================")
        print(f"🎉 BATCH COMPLETE: {len(outputs)} Broadcast Videos Rendered:")
        for o in outputs:
            print(f"  • {o}")
        print("==================================================================")
    else:
        render_story_from_spec(args.spec, show_logo=show_logo, force_tts=args.force_tts)


if __name__ == "__main__":
    main()
