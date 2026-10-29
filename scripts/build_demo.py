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
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reusable_templates as rt
from production_contract import scene_layout, check_render_contract, audio_fingerprint

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

MARGIN_X = 162  # Symmetrical 15.0% safe margin for TikTok/Reels (162px = 15.0%)
MARGIN_RIGHT = 162
SAFE_X2 = 1080 - MARGIN_RIGHT  # 918px
SAFE_WIDTH = SAFE_X2 - MARGIN_X  # 756px
SAFE_BOTTOM = 1640  # TikTok Safe Zone: >= 250px above bottom edge (1920 - 280px)

# Consistent Brand Color Palette
DOT_ORANGE = (254, 107, 33)        # Signature London Local dot orange (#FE6B21) for bars, sliders, accents
COLOR_WHITE = (255, 255, 255)       # Primary headlines, hero figures, titles
COLOR_LIGHT_GREY = (225, 230, 240)  # Secondary text, subtitles, descriptions, labels
COLOR_MUTED_GREY = (170, 175, 185)  # Citations, timestamps, divider rules


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
    """Loads the official London Local transparent wordmark from assets/templates/."""
    tpl_wm = os.path.join(BASE_DIR, "assets", "templates", "logo_watermark.png")
    if os.path.exists(tpl_wm):
        wm = Image.open(tpl_wm).convert("RGBA")
        aspect = wm.width / wm.height
        return wm.resize((int(target_height * aspect), target_height), Image.Resampling.LANCZOS)
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

    # Top progress bar (4px height at y=0..4) in signature dot orange
    draw.rectangle([(0, 0), (1080, 5)], fill=(255, 255, 255, 35))
    prog_w = int(1080 * (scene_num / max(1, total_scenes)))
    draw.rectangle([(0, 0), (prog_w, 5)], fill=DOT_ORANGE + (240,))

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
    pill_x2 = SAFE_X2
    pill_x1 = pill_x2 - pill_w
    draw.rounded_rectangle(
        [(pill_x1, 66), (pill_x2, 120)],
        radius=27,
        fill=(10, 10, 14, 195),
        outline=(255, 255, 255, 60),
        width=1,
    )
    draw.text((pill_x1 + 23, 83), tag_text, font=f_tag, fill=COLOR_LIGHT_GREY + (255,))

    # Optional AI Illustrative Disclaimer Pill (Top-Left Second Row)
    if disclaimer:
        f_ai = get_font(FONT_SANS_BOLD, 15)
        ai_text = disclaimer.upper()
        ai_w = draw.textlength(ai_text, font=f_ai)
        draw.rounded_rectangle(
            [(MARGIN_X, 132), (MARGIN_X + int(ai_w + 52), 168)],
            radius=18,
            fill=(12, 12, 16, 195),
            outline=DOT_ORANGE + (210,),
            width=1,
        )
        draw.ellipse([(MARGIN_X + 16, 146), (MARGIN_X + 24, 154)], fill=DOT_ORANGE + (255,))
        draw.text((MARGIN_X + 33, 142), ai_text, font=f_ai, fill=DOT_ORANGE + (255,))

    # Scene Counter Pill (Top-Right Second Row)
    f_sc = get_font(FONT_SANS_BOLD, 15)
    sc_text = f"SCENE 0{scene_num} / 0{total_scenes}"
    sc_w = draw.textlength(sc_text, font=f_sc)
    sc_x2 = SAFE_X2
    sc_x1 = sc_x2 - int(sc_w + 32)
    draw.rounded_rectangle(
        [(sc_x1, 132), (sc_x2, 168)],
        radius=18,
        fill=(12, 12, 16, 175),
        outline=(255, 255, 255, 40),
        width=1,
    )
    draw.text((sc_x1 + 16, 142), sc_text, font=f_sc, fill=COLOR_MUTED_GREY + (255,))


def draw_spatial_postcode_hud(draw, spec, scene_num=1, t=10.0):
    """Renders Frame-1 OCR Postcode Geo-Routing Banner & Scene-1 Spatial Lock-On Reticle."""
    postcode_tag = spec.get("postcodeTag", "")
    coords = spec.get("coordinates", "")
    if not postcode_tag:
        return

    # Top Frame-1 OCR Geo-Routing Bar (y=182..230) so platform vision models route to local postcodes
    bar_y1, bar_y2 = 182, 230
    draw.rounded_rectangle(
        [(MARGIN_X, bar_y1), (SAFE_X2, bar_y2)],
        radius=12,
        fill=(14, 14, 20, 215),
        outline=DOT_ORANGE + (160,),
        width=1,
    )

    # Pulsing live location reticle on left in dot orange
    cx, cy = MARGIN_X + 26, (bar_y1 + bar_y2) // 2
    pulse = (t * 2.2) % 1.0
    p_rad = int(5 + 7 * pulse)
    p_alpha = int(210 * (1.0 - pulse))
    draw.ellipse([(cx - p_rad, cy - p_rad), (cx + p_rad, cy + p_rad)], outline=DOT_ORANGE + (p_alpha,), width=2)
    draw.ellipse([(cx - 5, cy - 5), (cx + 5, cy + 5)], fill=DOT_ORANGE + (255,))

    f_pc = get_font(FONT_SANS_BOLD, 18)
    draw.text((MARGIN_X + 46, bar_y1 + 13), postcode_tag.upper(), font=f_pc, fill=COLOR_WHITE + (255,))

    # Right coordinate / citizen brief tag
    f_rt = get_font(FONT_SANS_BOLD, 15)
    rt_txt = "CITIZEN IMPACT BRIEF"
    rw = draw.textlength(rt_txt, font=f_rt)
    draw.text((SAFE_X2 - 20 - rw, bar_y1 + 15), rt_txt, font=f_rt, fill=DOT_ORANGE + (255,))

    # Scene 1 Spatial Lock-On Reticle in the first 1.8 seconds ("Wait, I know that place!" hook)
    if scene_num == 1 and t <= 1.85 and coords:
        fade = 1.0 if t < 1.35 else max(0.0, (1.85 - t) / 0.5)
        al = int(235 * fade)
        if al > 15:
            rx1, ry1, rx2, ry2 = MARGIN_X, 440, SAFE_X2, 535
            draw.rounded_rectangle([(rx1, ry1), (rx2, ry2)], radius=14, fill=(10, 10, 15, int(185 * fade)), outline=DOT_ORANGE + (al,), width=2)
            f_lock = get_font(FONT_SANS_BOLD, 16)
            f_coord = get_font(FONT_SANS_BOLD, 21)
            l_txt = "SPATIAL LOCK · VERIFIED BOROUGH LOCATION"
            lw = draw.textlength(l_txt, font=f_lock)
            draw.text(((1080 - lw) // 2, ry1 + 18), l_txt, font=f_lock, fill=DOT_ORANGE + (al,))
            cw = draw.textlength(coords, font=f_coord)
            draw.text(((1080 - cw) // 2, ry1 + 48), coords, font=f_coord, fill=COLOR_WHITE + (al,))


def draw_bottom_vignette(draw, start_y=940):
    for y in range(start_y, 1920):
        factor = (y - start_y) / (1920 - start_y)
        alpha = int(248 * (factor ** 1.25))
        draw.line([(0, y), (1080, y)], fill=(8, 8, 11, alpha))


def draw_lower_third_text(draw, graphic, citation_footer, top_y=1300):
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
        draw.text((MARGIN_X, curr_y), clean_kicker.upper(), font=f_kicker, fill=DOT_ORANGE + (255,))
        curr_y += 34

    h1_lines = wrap_text_to_width(draw, headline, f_h1, SAFE_WIDTH)
    for hl in h1_lines[:2]:
        draw.text((MARGIN_X, curr_y), hl, font=f_h1, fill=COLOR_WHITE + (255,))
        curr_y += 64

    curr_y += 12
    b_lines = wrap_text_to_width(draw, body, f_body, SAFE_WIDTH)
    for bl in b_lines[:3]:
        draw.text((MARGIN_X, curr_y), bl, font=f_body, fill=COLOR_LIGHT_GREY + (255,))
        curr_y += 39

    # Citation Rule & Footer (clamped safely above TikTok 250px bottom margin)
    rule_y = 1570
    draw.line([(MARGIN_X, rule_y), (SAFE_X2, rule_y)], fill=(255, 255, 255, 45), width=1)
    cite_lines = wrap_text_to_width(draw, citation_footer, f_meta, SAFE_WIDTH)
    if cite_lines:
        draw.text((MARGIN_X, rule_y + 18), cite_lines[0], font=f_meta, fill=COLOR_MUTED_GREY + (255,))


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
        [(MARGIN_X, fig_y1), (SAFE_X2, fig_y2)],
        radius=16,
        fill=(16, 16, 22, 228),
        outline=(255, 255, 255, 65),
        width=1,
    )

    f_hdr = get_font(FONT_SANS_BOLD, 18)
    hdr_left = fig_data.get("headerLeft", "CHAMBER DIVISION TALLY")
    raw_right = fig_data.get("headerRight", "MOTION CARRIED").replace("✓", "").strip()
    draw.text((MARGIN_X + 26, fig_y1 + 20), hdr_left, font=f_hdr, fill=DOT_ORANGE + (255,))

    # Badge pops in with scale/opacity after vote bar fills (t >= 0.75s)
    if t >= 0.75:
        rw = draw.textlength(raw_right, font=f_hdr)
        rx = int(SAFE_X2 - 26 - rw)
        chk_col = DOT_ORANGE + (255,)
        draw_vector_check(draw, rx - 22, fig_y1 + 22, chk_col, size=14)
        draw.text((rx, fig_y1 + 20), raw_right, font=f_hdr, fill=chk_col)

    parties = fig_data.get("parties", [])
    total_seats = sum(max(1, p.get("seats", 1)) for p in parties) or 1
    bar_x1 = MARGIN_X + 26
    bar_x2 = SAFE_X2 - 26
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
        [(MARGIN_X + 6, fig_y1 + 8), (SAFE_X2 + 6, fig_y2 + 8)],
        radius=14,
        fill=(0, 0, 0, 160),
    )
    # Warm archival broadsheet paper card
    paper_bg = (248, 246, 240, 250)
    ink_dark = (18, 18, 22, 255)
    ink_muted = (85, 85, 95, 255)
    draw.rounded_rectangle(
        [(MARGIN_X, fig_y1), (SAFE_X2, fig_y2)],
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
    draw.text((SAFE_X2 - 28 - rw, fig_y1 + 18), right_hdr, font=f_doc_hdr, fill=DOT_ORANGE + (255,))

    # Double parliamentary rule
    draw.line([(MARGIN_X + 28, fig_y1 + 46), (SAFE_X2 - 28, fig_y1 + 46)], fill=(40, 40, 45, 220), width=2)
    draw.line([(MARGIN_X + 28, fig_y1 + 51), (SAFE_X2 - 28, fig_y1 + 51)], fill=(40, 40, 45, 120), width=1)

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

    # Signature Dot-Orange Audit Bracket on the left margin of the excerpt
    if hl_progress > 0.1:
        bracket_h = int(105 * hl_progress)
        draw.line([(MARGIN_X + 16, fig_y1 + 64), (MARGIN_X + 16, fig_y1 + 64 + bracket_h)], fill=DOT_ORANGE + (240,), width=4)
        draw.line([(MARGIN_X + 16, fig_y1 + 64), (MARGIN_X + 24, fig_y1 + 64)], fill=DOT_ORANGE + (240,), width=3)

    qy = fig_y1 + 66
    for ql in q_lines[:3]:
        hl_words = [w for w in highlight.split(" ") if len(w) > 3]
        if any(hw in ql for hw in hl_words):
            lw = draw.textlength(ql, font=f_quote)
            # Sweeping highlight rectangle in refined light grey
            current_hl_w = int(lw * hl_progress)
            if current_hl_w > 4:
                draw.rounded_rectangle(
                    [(MARGIN_X + 24, qy - 2), (MARGIN_X + 28 + current_hl_w, qy + 32)],
                    radius=4,
                    fill=(226, 230, 240, 235),
                )
        draw.text((MARGIN_X + 28, qy), ql, font=f_quote, fill=ink_dark)
        qy += 38

    # Signatories Footer Bar inside paper card
    sig_y = fig_y2 - 52
    draw.line([(MARGIN_X + 28, sig_y - 8), (SAFE_X2 - 28, sig_y - 8)], fill=(200, 195, 185, 255), width=1)
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
        st_x2 = SAFE_X2 - 24
        st_x1 = st_x2 - st_box_w
        st_y = sig_y - 4
        draw.rounded_rectangle([(st_x1, st_y), (st_x2, st_y + 36)], radius=6, fill=(254, 242, 242, 245), outline=DOT_ORANGE + (240,), width=2)
        draw.text((st_x1 + 16, st_y + 9), receipt_stamp, font=f_stamp, fill=DOT_ORANGE + (255,))


def render_figure_stat_comparison(draw, fig_data, t=10.0):
    """Renders dual floating glassmorphic metric cards with staggered entry and progressive bar fills in consistent dot orange."""
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
        bar_col = DOT_ORANGE + (255,)
        card_inner_w = card_w - 52

        # 1. Kicker
        kicker_txt = str(c.get("kicker", ""))
        f_kicker, k_lines, _ = rt.fit_text_to_bounds(draw, kicker_txt, FONT_SANS_BOLD, initial_size=16, max_width=card_inner_w, max_lines=1, min_size=12)
        draw.text((cx + 26, py1 + 20), k_lines[0] if k_lines else kicker_txt, font=f_kicker, fill=bar_col)

        # 2. Hero Value (Dynamic font scaling strictly bounded within card_inner_w)
        val_str = str(c.get("value", ""))
        f_val, val_lines, _ = rt.fit_text_to_bounds(draw, val_str, FONT_SERIF_BOLD, initial_size=70, max_width=card_inner_w, max_lines=1, min_size=28)
        val_size = getattr(f_val, "size", 70)
        y_val_offset = (70 - val_size) // 2
        draw.text((cx + 26, py1 + 44 + y_val_offset), val_lines[0] if val_lines else val_str, font=f_val, fill=COLOR_WHITE + (255,))

        # 3. Label
        lbl_txt = str(c.get("label", ""))
        f_lbl, lbl_lines, _ = rt.fit_text_to_bounds(draw, lbl_txt, FONT_SANS_BOLD, initial_size=22, max_width=card_inner_w, max_lines=1, min_size=14)
        draw.text((cx + 26, py1 + 132), lbl_lines[0] if lbl_lines else lbl_txt, font=f_lbl, fill=COLOR_WHITE + (255,))

        # Benchmark bar fills progressively in signature dot orange
        bar_p = ease_out_cubic((card_t - 0.2) / 0.7) if card_t > 0.2 else 0.0
        bx1, bx2 = cx + 26, cx + card_w - 26
        by1, by2 = py1 + 174, py1 + 184
        draw.rounded_rectangle([(bx1, by1), (bx2, by2)], radius=5, fill=(45, 48, 58, 255))
        ratio = max(0.1, min(1.0, float(c.get("barRatio", 0.85)))) * bar_p
        fill_w = int((bx2 - bx1) * ratio)
        if fill_w > 4:
            draw.rounded_rectangle([(bx1, by1), (bx1 + fill_w, by2)], radius=5, fill=bar_col)

        draw.text((cx + 26, py1 + 198), c.get("subtext", ""), font=get_font(FONT_SANS, 17), fill=COLOR_LIGHT_GREY + (255,))


def render_figure_action_matrix(draw, fig_data, t=10.0):
    """Renders a 2x2 connected civic governance grid with staggered pillar entrances."""
    hdr_p = ease_out_cubic(t / 0.35)
    hdr_y1, hdr_y2 = 1005, 1052
    draw.rounded_rectangle(
        [(MARGIN_X, hdr_y1), (MARGIN_X + int((SAFE_WIDTH) * hdr_p), hdr_y2)],
        radius=10,
        fill=DOT_ORANGE + (230,),
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
        draw.text((px + 20, py + 16), p.get("code", ""), font=get_font(FONT_SANS_BOLD, 18), fill=DOT_ORANGE + (255,))
        d_lines = wrap_text_to_width(draw, p.get("desc", ""), get_font(FONT_SANS, 20), gw - 40)
        dy = py + 46
        for dl in d_lines[:2]:
            draw.text((px + 20, dy), dl, font=get_font(FONT_SANS, 20), fill=(230, 230, 235, 255))
            dy += 26


def render_template_scene1_hook(spec, scene, t=10.0, total_dur=6.0):
    """Renders the official Scene 1 Hook overlay from Main headline.png over B-roll."""
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Top scrim vignette behind Persistent Watermark for maximum contrast against any sky
    for y in range(0, 260):
        a = int(185 * (1.0 - (y / 260.0)**1.4))
        draw.line([(0, y), (1080, y)], fill=(8, 8, 12, a))

    rt.apply_persistent_watermark(overlay)

    # Soft, subtle center scrim vignette behind text for maximum legibility over moving B-roll
    for y in range(720, 1360):
        dist = abs(y - 1040) / 320
        a = int(190 * max(0.0, 1.0 - dist**2))
        if a > 0:
            draw.line([(0, y), (1080, y)], fill=(8, 8, 12, a))

    archetype = rt.ARCHETYPE_CONFIG.get(spec.get("storyType", "council_decision"), rt.ARCHETYPE_CONFIG["council_decision"])
    accent_rgb = archetype["accent"]

    # Optional Postcode / Area Kicker with high-contrast backing badge
    pc = spec.get("postcodeTag", "")
    if pc:
        f_pc = rt.get_font(rt.FONT_SANS_BOLD, 20)
        pw = draw.textlength(pc, font=f_pc)
        pill_w = min(SAFE_WIDTH, int(pw + 36))
        px1 = (1080 - pill_w) // 2
        px2 = px1 + pill_w
        py1 = 770
        py2 = py1 + 42
        draw.rounded_rectangle([(px1, py1), (px2, py2)], radius=10, fill=(14, 15, 22, 225), outline=DOT_ORANGE + (190,), width=1)
        draw.text(((1080 - pw) // 2, py1 + 10), pc, font=f_pc, fill=DOT_ORANGE + (255,))

    # Headline and Subtitle with dynamic bounds-checking and auto-fit
    h_txt = scene.get("onScreenGraphic", {}).get("headline", spec.get("headline", ""))
    b_txt = scene.get("onScreenGraphic", {}).get("body", "")

    f_h1, h_lines, h_spacing = rt.fit_text_to_bounds(draw, h_txt, rt.FONT_SERIF_BOLD, initial_size=72, max_width=SAFE_WIDTH, max_lines=3, min_size=46)
    f_sub, b_lines, b_spacing = rt.fit_text_to_bounds(draw, b_txt, rt.FONT_SERIF_BOLD, initial_size=40, max_width=SAFE_WIDTH, max_lines=3, min_size=28)

    # Animation ease-in: fade and 20px rise
    p = ease_out_cubic(min(1.0, max(0.0, t / 0.4)))
    y_off = int((1.0 - p) * 20)

    hy = 840 + y_off
    for line in h_lines:
        lw = draw.textlength(line, font=f_h1)
        draw.text(((1080 - lw) // 2, hy), line, font=f_h1, fill=COLOR_WHITE + (int(255 * p),))
        hy += h_spacing

    hy += 18
    for line in b_lines:
        lw = draw.textlength(line, font=f_sub)
        draw.text(((1080 - lw) // 2, hy), line, font=f_sub, fill=COLOR_LIGHT_GREY + (int(255 * p),))
        hy += b_spacing

    archetype = rt.ARCHETYPE_CONFIG.get(spec.get("storyType", "council_decision"), rt.ARCHETYPE_CONFIG["council_decision"])
    accent_rgb = archetype["accent"]

    if spec.get("branding", {}).get("showCaptions", False):
        rt.render_phrase_caption_pill(overlay, scene.get("voiceoverText", ""), t=t, total_dur=total_dur, y_top=1540, accent_rgb=accent_rgb)

    # Bottom scrim for AI-GENERATED MEDIA badge contrast over bright streets
    for y in range(1650, 1920):
        a = int(165 * ((y - 1650) / 270.0)**1.2)
        draw.line([(0, y), (1080, y)], fill=(8, 8, 12, a))

    # AI disclaimer cleanly anchored at bottom
    rt.apply_ai_disclaimer(overlay, show=scene.get("visualAsset", {}).get("isIllustrative", False))
    return overlay


def render_template_scene2_receipt(spec, scene, t=10.0, total_dur=6.0):
    """Renders an authentic Verified Public Record Excerpt card with live subtle highlight vertically centered over 35mm B-roll."""
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Top scrim for watermark contrast
    for y in range(0, 250):
        a = int(180 * (1.0 - (y / 250.0)**1.4))
        draw.line([(0, y), (1080, y)], fill=(8, 8, 12, a))

    rt.apply_persistent_watermark(overlay)

    fig = scene.get("figure", {})
    fig_data = fig.get("data", {})

    ox = MARGIN_X
    card_w = SAFE_WIDTH

    f_doc_hdr = rt.get_font(rt.FONT_SANS_BOLD, 21)
    f_mtitle = rt.get_font(rt.FONT_SERIF_BOLD, 44)
    f_quote = rt.get_font(rt.FONT_SERIF_BOLD, 36)
    f_sig = rt.get_font(rt.FONT_SANS_BOLD, 21)
    f_sub_sig = rt.get_font(rt.FONT_SANS, 19)
    f_stamp = rt.get_font(rt.FONT_SANS_BOLD, 19)

    # Excerpt quote text
    prefix = fig_data.get("excerptPrefix", "")
    highlight = fig_data.get("highlightPhrase", "")
    suffix = fig_data.get("excerptSuffix", "")
    full_quote = f"{prefix}{highlight}{suffix}"
    q_lines = rt.wrap_text(draw, full_quote, f_quote, card_w - 80)

    # Pre-calculate content height with balanced vertical margins (clean excerpt card without micro-clauses)
    pad_top = 40
    hdr_h = 62
    title_h = 72
    quote_h = len(q_lines[:5]) * 52 + 32
    sig_h = 84
    pad_bot = 36

    total_card_h = pad_top + hdr_h + title_h + quote_h + sig_h + pad_bot
    cy1 = 920 - (total_card_h // 2)
    cy2 = cy1 + total_card_h

    # Smooth animated entry
    p_card = ease_out_cubic(min(1.0, max(0.0, t / 0.4)))
    y_slide = int((1.0 - p_card) * 30)
    act_cy1, act_cy2 = cy1 + y_slide, cy2 + y_slide

    # Background scrim vignette for legibility over moving 35mm B-roll
    for y in range(act_cy1 - 100, act_cy2 + 100):
        dist = abs(y - (act_cy1 + act_cy2) // 2) / ((act_cy2 - act_cy1 + 200) // 2)
        a = int(195 * max(0.0, 1.0 - dist**2))
        if a > 0:
            draw.line([(0, y), (1080, y)], fill=(8, 8, 12, a))

    # Archival Cream Source Excerpt Card
    draw.rounded_rectangle(
        [(ox, act_cy1), (ox + card_w, act_cy2)],
        radius=20,
        fill=(250, 248, 242, 252),
        outline=(255, 255, 255, 110),
        width=2,
    )

    ink_dark = (20, 22, 28, 255)
    ink_muted = (95, 100, 112, 255)

    # Masthead
    left_hdr = fig_data.get("docHeaderLeft", f"LONDON BOROUGH OF {spec.get('borough', '').upper()} · PUBLIC RECORD")
    right_hdr = fig_data.get("docHeaderRight", "VERIFIED EXCERPT")
    curr_y = act_cy1 + pad_top
    draw.text((ox + 35, curr_y), left_hdr, font=f_doc_hdr, fill=ink_muted)
    rw = draw.textlength(right_hdr, font=f_doc_hdr)
    draw.text((ox + card_w - 35 - rw, curr_y), right_hdr, font=f_doc_hdr, fill=DOT_ORANGE + (255,))
    curr_y += 38

    draw.line([(ox + 35, curr_y), (ox + card_w - 35, curr_y)], fill=(40, 40, 45, 240), width=3)
    curr_y += 24

    # Subject Header
    mtitle = scene.get("onScreenGraphic", {}).get("headline", "Verified Council Record").replace("\n", " ")
    for tl in rt.wrap_text(draw, mtitle, f_mtitle, card_w - 70)[:1]:
        draw.text((ox + 35, curr_y), tl, font=f_mtitle, fill=ink_dark)
    curr_y += title_h

    # Signature Dot-Orange margin bracket & highlighted quote
    hl_progress = ease_out_cubic(max(0.0, min(1.0, (t - 0.35) / 1.25))) if t >= 0.35 else 0.0
    bracket_start = curr_y - 6
    bracket_h = int((len(q_lines[:5]) * 52 + 10) * max(0.1, hl_progress))

    if hl_progress > 0.05:
        draw.line([(ox + 18, bracket_start), (ox + 18, bracket_start + bracket_h)], fill=DOT_ORANGE + (245,), width=4)
        draw.line([(ox + 18, bracket_start), (ox + 28, bracket_start)], fill=DOT_ORANGE + (245,), width=3)
        if hl_progress > 0.9:
            draw.line([(ox + 18, bracket_start + bracket_h), (ox + 28, bracket_start + bracket_h)], fill=DOT_ORANGE + (245,), width=3)

    for ql in q_lines[:5]:
        hl_words = [w.strip(".,\"'") for w in highlight.split(" ") if len(w.strip(".,\"'")) > 3]
        if any(hw in ql for hw in hl_words):
            lw = draw.textlength(ql, font=f_quote)
            current_hl_w = int(lw * hl_progress)
            if current_hl_w > 4:
                # Refined light grey highlight marker
                draw.rounded_rectangle([(ox + 32, curr_y - 2), (ox + 36 + current_hl_w, curr_y + 42)], radius=4, fill=(226, 230, 240, 235))
        draw.text((ox + 35, curr_y), ql, font=f_quote, fill=ink_dark)
        curr_y += 52

    curr_y += 18
    draw.line([(ox + 35, curr_y), (ox + card_w - 35, curr_y)], fill=(210, 205, 195, 255), width=2)
    curr_y += 20

    # Authentic Attribution & Provenance Badge
    draw.text((ox + 35, curr_y), fig_data.get("mover", "Source: Council Committee Report"), font=f_sig, fill=ink_dark)
    draw.text((ox + 35, curr_y + 30), fig_data.get("seconder", "Published on londonlocal.news"), font=f_sub_sig, fill=ink_muted)

    st_txt = fig_data.get("receiptStamp", "VERIFIED SOURCE")
    st_w = draw.textlength(st_txt, font=f_stamp)
    st_x2 = ox + card_w - 35
    st_x1 = st_x2 - int(st_w + 34)
    draw.rounded_rectangle([(st_x1, curr_y + 4), (st_x2, curr_y + 50)], radius=8, fill=(254, 242, 242, 245), outline=DOT_ORANGE + (240,), width=2)
    draw.text((st_x1 + 17, curr_y + 15), st_txt, font=f_stamp, fill=DOT_ORANGE + (255,))

    archetype = rt.ARCHETYPE_CONFIG.get(spec.get("storyType", "council_decision"), rt.ARCHETYPE_CONFIG["council_decision"])
    accent_rgb = archetype["accent"]

    if spec.get("branding", {}).get("showCaptions", False):
        rt.render_phrase_caption_pill(overlay, scene.get("voiceoverText", ""), t=t, total_dur=total_dur, y_top=1540, accent_rgb=accent_rgb)

    # Bottom scrim for citation & AI-GENERATED MEDIA badge contrast
    for y in range(1580, 1920):
        a = int(175 * ((y - 1580) / 340.0)**1.2)
        draw.line([(0, y), (1080, y)], fill=(8, 8, 12, a))

    # Clean verified source attribution line at bottom (safely at y=1615, well above 1640)
    cite = scene.get("citationFooter", spec.get("meetingDateDisplay", "Council Public Record"))
    cite_clean = cite.strip().lstrip("<").rstrip(">")
    f_cite = rt.get_font(rt.FONT_SANS_BOLD, 21)
    for cl in rt.wrap_text(draw, cite_clean, f_cite, SAFE_WIDTH)[:1]:
        cw = draw.textlength(cl, font=f_cite)
        draw.text(((1080 - cw) // 2, 1615), cl, font=f_cite, fill=(225, 230, 240, 255))

    rt.apply_ai_disclaimer(overlay, show=scene.get("visualAsset", {}).get("isIllustrative", False))
    return overlay


def render_selling_point_slide_card(spec, t=10.0):
    """Renders the official grand finale Selling Point slide from London Local.png."""
    card = Image.new("RGBA", (1080, 1920), (14, 14, 20, 255))
    draw = ImageDraw.Draw(card)

    for y in range(0, 1920):
        val = int(14 + (y / 1920) * 8)
        draw.line([(0, y), (1080, y)], fill=(val, val, val + 2, 255))

    rt.apply_persistent_watermark(card)

    f_main = rt.get_font(rt.FONT_SERIF_BOLD, 84)
    line1 = "Local news, from"
    line2 = "your council"  # Single red dot acts as the period (NO trailing period!)

    p_title = ease_out_cubic(min(1.0, max(0.0, t / 0.3)))
    draw.text((MARGIN_X, 800), line1, font=f_main, fill=(255, 255, 255, int(255 * p_title)))
    draw.text((MARGIN_X, 910), line2, font=f_main, fill=(255, 255, 255, int(255 * p_title)))
    l_yc = draw.textlength(line2, font=f_main)
    draw.ellipse([(MARGIN_X + l_yc + 8, 955), (MARGIN_X + l_yc + 26, 973)], fill=DOT_ORANGE + (int(255 * p_title),))

    draw.line([(MARGIN_X, 1060), (SAFE_X2, 1060)], fill=(255, 255, 255, 45), width=1)

    f_sub = rt.get_font(rt.FONT_SERIF, 36)
    sub_txt = "Direct from council agendas to your phone."
    draw.text((MARGIN_X, 1100), sub_txt, font=f_sub, fill=COLOR_LIGHT_GREY + (int(255 * p_title),))

    # 3 Sleek Trust Badges
    f_badge = rt.get_font(rt.FONT_SANS_BOLD, 20)
    badges = ["OFFICIAL RECEIPTS", "ZERO SENSATIONALISM", "ALL 33 BOROUGHS"]
    bx = MARGIN_X
    for b in badges:
        bw = draw.textlength(b, font=f_badge)
        draw.rounded_rectangle([(bx, 1200), (bx + bw + 36, 1248)], radius=12, fill=(22, 24, 32, 255), outline=DOT_ORANGE + (160,), width=1)
        draw.text((bx + 18, 1214), b, font=f_badge, fill=DOT_ORANGE + (int(255 * p_title),))
        bx += int(bw + 40)

    f_bot = rt.get_font(rt.FONT_SERIF, 34)
    bot_txt = "londonlocal.news"
    bw = draw.textlength(bot_txt, font=f_bot)
    draw.text(((1080 - bw) // 2, 1615), bot_txt, font=f_bot, fill=(180, 185, 195, 255))
    return card


def render_template_scene3_key_points(spec, scene, t=10.0, total_dur=6.0):
    """Renders the official Scene 3 Key Points broadsheet slide from 4.png over darkened 35mm footage with progressive step illumination."""
    overlay = Image.new("RGBA", (1080, 1920), (12, 12, 18, 222))
    draw = ImageDraw.Draw(overlay)

    archetype = rt.ARCHETYPE_CONFIG.get(spec.get("storyType", "council_decision"), rt.ARCHETYPE_CONFIG["council_decision"])
    accent_rgb = archetype["accent"]

    # Section Heading with Quality Control dynamic fitting (fits inside SAFE_WIDTH)
    heading = spec.get("keyPointsHeading", scene.get("onScreenGraphic", {}).get("headline", "Key points")).replace("\n", " ")
    f_title, head_lines, head_spacing = rt.fit_text_to_bounds(draw, heading, rt.FONT_SERIF_BOLD, initial_size=82, max_width=SAFE_WIDTH, max_lines=2, min_size=48)
    hy = 120
    for hl in head_lines:
        draw.text((MARGIN_X, hy), hl, font=f_title, fill=(255, 255, 255, 255))
        hy += head_spacing

    points = spec.get("keyPoints", [])

    f_anchor = rt.get_font(rt.FONT_SERIF_BOLD, 46)
    f_sub = rt.get_font(rt.FONT_SANS, 28)
    f_cite = rt.get_font(rt.FONT_SANS_BOLD, 21)
    f_step = rt.get_font(rt.FONT_SERIF_BOLD, 52)

    start_y = max(330, hy + 25)
    spacing = 355

    # Calm, smooth progressive step illumination across scene duration
    t1 = total_dur * 0.42
    t2 = total_dur * 0.76
    fade_half = 0.18  # smooth 0.36s crossfade between tabs

    tab_intensities = [0.0, 0.0, 0.0]
    if t < t1 - fade_half:
        tab_intensities[0] = 1.0
    elif t < t1 + fade_half:
        p = (t - (t1 - fade_half)) / (2 * fade_half)
        tab_intensities[0] = 1.0 - p
        tab_intensities[1] = p
    elif t < t2 - fade_half:
        tab_intensities[1] = 1.0
    elif t < t2 + fade_half:
        p = (t - (t2 - fade_half)) / (2 * fade_half)
        tab_intensities[1] = 1.0 - p
        tab_intensities[2] = p
    else:
        tab_intensities[2] = 1.0

    for idx, pt in enumerate(points[:3]):
        t_start = 0.10 + idx * 0.22
        p_pt = ease_out_cubic(min(1.0, max(0.0, (t - t_start) / 0.3))) if t >= t_start else 0.0
        if p_pt <= 0.01:
            continue

        py = start_y + idx * spacing
        y_off = int((1.0 - p_pt) * 15)

        if len(pt) == 3:
            anchor, sub, cite_text = pt
        elif len(pt) == 2:
            anchor, cite_text = pt
            sub = ""
        else:
            anchor = str(pt[0])
            sub = ""
            cite_text = "Council Public Record"

        act_val = tab_intensities[idx] * p_pt
        # Base card container: always draw a solid/dark card backdrop so text never floats over bright video
        card_fill_a = int(195 + 45 * act_val)
        card_outline = (accent_rgb + (int(220 * act_val),)) if act_val > 0.05 else (255, 255, 255, int(45 * p_pt))
        draw.rounded_rectangle(
            [(MARGIN_X, py - 18 + y_off), (SAFE_X2, py + 235 + y_off)],
            radius=18,
            fill=(18, 20, 28, int(card_fill_a * p_pt)),
            outline=card_outline,
            width=2,
        )

        # Left vertical accent line on card (crossfades between muted grey and bright accent)
        r_bar = int(140 * (1.0 - act_val) + accent_rgb[0] * act_val)
        g_bar = int(145 * (1.0 - act_val) + accent_rgb[1] * act_val)
        b_bar = int(160 * (1.0 - act_val) + accent_rgb[2] * act_val)
        a_bar = int(180 * (1.0 - act_val) + 255 * act_val)
        draw.line([(MARGIN_X + 10, py + 12 + y_off), (MARGIN_X + 10, py + 72 + y_off)], fill=(r_bar, g_bar, b_bar, int(a_bar * p_pt)), width=5)

        # Prominent Hero Step Number (52px bold serif)
        step_txt = f"0{idx + 1}"
        r_step = int(180 * (1.0 - act_val) + accent_rgb[0] * act_val)
        g_step = int(185 * (1.0 - act_val) + accent_rgb[1] * act_val)
        b_step = int(200 * (1.0 - act_val) + accent_rgb[2] * act_val)
        draw.text((MARGIN_X + 28, py + 14 + y_off), step_txt, font=f_step, fill=(r_step, g_step, b_step, int(255 * p_pt)))

        # Vertical Divider
        draw.line([(MARGIN_X + 106, py + 20 + y_off), (MARGIN_X + 106, py + 70 + y_off)], fill=(255, 255, 255, int(70 * p_pt)), width=2)

        # Bold Anchor Headline
        draw.text((MARGIN_X + 126, py + 16 + y_off), anchor, font=f_anchor, fill=(255, 255, 255, int(255 * p_pt)))

        sub_y = py + 92 + y_off
        if sub:
            for line in rt.wrap_text(draw, sub, f_sub, SAFE_WIDTH - 50)[:2]:
                draw.text((MARGIN_X + 28, sub_y), line, font=f_sub, fill=(225, 230, 240, int(255 * p_pt)))
                sub_y += 38

        cite_str = cite_text.strip().lstrip("<").rstrip(">")
        draw.text((MARGIN_X + 28, sub_y + 8), cite_str, font=f_cite, fill=(180, 185, 200, int(255 * p_pt)))

    archetype = rt.ARCHETYPE_CONFIG.get(spec.get("storyType", "council_decision"), rt.ARCHETYPE_CONFIG["council_decision"])
    accent_rgb = archetype["accent"]

    if spec.get("branding", {}).get("showCaptions", False):
        rt.render_phrase_caption_pill(overlay, scene.get("voiceoverText", ""), t=t, total_dur=total_dur, y_top=1540, accent_rgb=accent_rgb)

    # Clean bottom public record attribution (crisp 21px bold sans at y=1615)
    f_bot = rt.get_font(rt.FONT_SANS_BOLD, 21)
    bot_txt = scene.get("sourceLabel", f"LONDON BOROUGH OF {spec.get('borough', 'Council').upper()} · VERIFIED PUBLIC RECORD")
    bw = draw.textlength(bot_txt, font=f_bot)
    draw.text(((1080 - bw) // 2, 1615), bot_txt, font=f_bot, fill=(205, 210, 225, 255))

    rt.apply_ai_disclaimer(overlay, show=scene.get("visualAsset", {}).get("isIllustrative", False))
    return overlay


def render_template_scene4_facts_figures(spec, scene, t=10.0, total_dur=6.0):
    """Renders the official Scene 4 Facts and figures frame from 5.png with animated London Borough Map."""
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    archetype = rt.ARCHETYPE_CONFIG.get(spec.get("storyType", "council_decision"), rt.ARCHETYPE_CONFIG["council_decision"])
    accent_rgb = archetype["accent"]

    # Top scrim for 'Facts and figures' contrast over moving 35mm B-roll
    for y in range(0, 280):
        a = int(210 * (1.0 - (y / 280.0)**1.4))
        draw.line([(0, y), (1080, y)], fill=(8, 8, 12, a))

    # Header from 5.png - Dynamic narrative title or fallback, centered within SAFE_WIDTH on 540px axis
    heading = spec.get("factsFiguresHeading", scene.get("onScreenGraphic", {}).get("headline", "Facts and figures")).replace("\n", " ")
    f_title, head_lines, _ = rt.fit_text_to_bounds(draw, heading, rt.FONT_SERIF_BOLD, initial_size=74, max_width=SAFE_WIDTH, max_lines=1, min_size=38)
    title_txt = head_lines[0] if head_lines else "Facts and figures"
    tw = draw.textlength(title_txt, font=f_title)
    draw.text(((1080 - tw) // 2, 115), title_txt, font=f_title, fill=(255, 255, 255, 255))

    # Container frame from 5.png (bounded strictly within SAFE_X2 and ending at 1545)
    bx1, by1, bx2, by2 = MARGIN_X, 260, SAFE_X2, 1545
    draw.rounded_rectangle([(bx1, by1), (bx2, by2)], radius=20, fill=(22, 23, 31, 245), outline=(255, 255, 255, 45), width=2)

    fig = scene.get("figure", {})
    fig_type = fig.get("type", "")
    fig_data = fig.get("data", {})

    cards = []
    if fig_type == "stat_comparison":
        cards = fig_data.get("cards", [])
    else:
        for s in spec.get("timeline", []):
            if s.get("figure", {}).get("type") == "stat_comparison":
                cards = s.get("figure", {}).get("data", {}).get("cards", [])
                break

    # Upper: Two Hero Stat Cards
    cw = (bx2 - bx1 - 50) // 2
    c1_x1, c1_x2 = bx1 + 20, bx1 + 20 + cw
    c2_x1, c2_x2 = c1_x2 + 10, bx2 - 20

    if len(cards) >= 2:
        for idx, (cx1, cx2, c) in enumerate([(c1_x1, c1_x2, cards[0]), (c2_x1, c2_x2, cards[1])]):
            t_card = t - (0.1 + idx * 0.2)
            p_c = ease_out_cubic(t_card / 0.4) if t_card > 0 else 0.0
            if p_c <= 0.01:
                continue
            card_inner_w = cx2 - cx1 - 48
            bar_col = tuple(c.get("barColor", list(accent_rgb))) + (255,)
            draw.rounded_rectangle([(cx1, by1 + 24), (cx2, by1 + 335)], radius=16, fill=(16, 17, 24, 255), outline=(255, 255, 255, 60), width=1)

            # 1. Kicker
            kicker_str = str(c.get("kicker", ""))
            f_kicker, k_lines, _ = rt.fit_text_to_bounds(draw, kicker_str, rt.FONT_SANS_BOLD, initial_size=17, max_width=card_inner_w, max_lines=1, min_size=12)
            draw.text((cx1 + 24, by1 + 46), k_lines[0] if k_lines else kicker_str, font=f_kicker, fill=bar_col)

            # 2. Hero Value (Dynamic font scaling strictly bounded within card_inner_w)
            val_str = str(c.get("value", ""))
            f_val, val_lines, _ = rt.fit_text_to_bounds(draw, val_str, rt.FONT_SERIF_BOLD, initial_size=70, max_width=card_inner_w, max_lines=1, min_size=28)
            val_size = getattr(f_val, "size", 70)
            y_val_offset = (70 - val_size) // 2
            draw.text((cx1 + 24, by1 + 80 + y_val_offset), val_lines[0] if val_lines else val_str, font=f_val, fill=(255, 255, 255, 255))

            # 3. Label
            f_lbl = rt.get_font(rt.FONT_SANS_BOLD, 20)
            lbl_lines = rt.wrap_text(draw, c.get("label", ""), f_lbl, card_inner_w)
            draw.text((cx1 + 24, by1 + 172), lbl_lines[0] if lbl_lines else "", font=f_lbl, fill=(230, 230, 235, 255))

            # 4. Progress bar
            draw.rounded_rectangle([(cx1 + 24, by1 + 218), (cx2 - 24, by1 + 230)], radius=6, fill=(45, 45, 55, 255))
            ratio = max(0.1, min(1.0, float(c.get("barRatio", 0.85)))) * p_c
            fill_w = int(card_inner_w * ratio)
            if fill_w > 4:
                draw.rounded_rectangle([(cx1 + 24, by1 + 218), (cx1 + 24 + fill_w, by1 + 230)], radius=6, fill=bar_col)

            # 5. Subtext
            f_card_sub = rt.get_font(rt.FONT_SANS, 17)
            sub_lines = rt.wrap_text(draw, c.get("subtext", ""), f_card_sub, card_inner_w)
            sub_y = by1 + 246
            for sl in sub_lines[:2]:
                draw.text((cx1 + 24, sub_y), sl, font=f_card_sub, fill=(185, 185, 195, 255))
                sub_y += 24

    # Middle: Map Container with Calm, Stable London Borough Vector Map
    map_y = by1 + 355
    map_h = 720
    draw.rounded_rectangle([(bx1 + 20, map_y), (bx2 - 20, map_y + map_h)], radius=18, fill=(16, 17, 24, 255), outline=(255, 255, 255, 60), width=1)

    borough_name = spec.get("borough", "Camden")
    # Keep map steady and stable to prevent disorientation
    zoom_factor = 1.0
    map_crop = rt.generate_borough_map_overlay(
        borough_name,
        width=bx2 - bx1 - 80,
        height=map_h - 95,
        zoom=zoom_factor,
        accent_rgb=accent_rgb,
    )
    if map_crop:
        overlay.paste(map_crop, (bx1 + 40, map_y + 18), map_crop)

    # Locator Pill (with crisp vector pin dot instead of Unicode emoji)
    b_label = f"LONDON BOROUGH OF {borough_name.upper()}"
    f_pill = rt.get_font(rt.FONT_SANS_BOLD, 20)
    pw = draw.textlength(b_label, font=f_pill)
    pill_w = int(pw + 68)
    pill_x1 = (1080 - pill_w) // 2
    pill_y1 = map_y + map_h - 66
    draw.rounded_rectangle([(pill_x1, pill_y1), (pill_x1 + pill_w, map_y + map_h - 18)], radius=12, fill=(14, 14, 20, 245), outline=accent_rgb + (220,), width=1)
    draw.ellipse([(pill_x1 + 20, pill_y1 + 17), (pill_x1 + 34, pill_y1 + 31)], fill=accent_rgb + (255,))
    draw.text((pill_x1 + 44, pill_y1 + 12), b_label, font=f_pill, fill=accent_rgb + (255,))

    # Bottom Takeaway Card (100% Data-Driven from spec["takeawayCard"])
    vy1 = map_y + map_h + 20
    draw.rounded_rectangle([(bx1 + 20, vy1), (bx2 - 20, vy1 + 165)], radius=16, fill=(16, 17, 24, 255), outline=(255, 255, 255, 60), width=1)

    takeaway = spec.get("takeawayCard", {})
    t_kicker = takeaway.get("kicker", "WHAT HAPPENS NEXT")
    t_title = takeaway.get("title", scene.get("onScreenGraphic", {}).get("headline", "Council Implementation").replace("\n", " "))
    t_sub = takeaway.get("subtitle", scene.get("onScreenGraphic", {}).get("body", ""))

    f_kicker = rt.get_font(rt.FONT_SANS_BOLD, 18)
    kw = draw.textlength(t_kicker.upper(), font=f_kicker)
    draw.text(((1080 - kw) // 2, vy1 + 22), t_kicker.upper(), font=f_kicker, fill=DOT_ORANGE + (255,))

    t_width = bx2 - bx1 - 80
    f_ttitle, tt_lines, _ = rt.fit_text_to_bounds(draw, t_title, rt.FONT_SERIF_BOLD, initial_size=31, max_width=t_width, max_lines=1, min_size=20)
    t_text = tt_lines[0] if tt_lines else t_title
    tw = draw.textlength(t_text, font=f_ttitle)
    draw.text(((1080 - tw) // 2, vy1 + 56), t_text, font=f_ttitle, fill=(255, 255, 255, 255))

    f_sub = rt.get_font(rt.FONT_SANS, 20)
    for sl in rt.wrap_text(draw, t_sub, f_sub, t_width)[:1]:
        sw = draw.textlength(sl, font=f_sub)
        draw.text(((1080 - sw) // 2, vy1 + 104), sl, font=f_sub, fill=(195, 200, 210, 255))

    # Bottom scrim for caption, citation & AI-GENERATED MEDIA badge contrast over bright B-roll
    for y in range(1545, 1920):
        a = int(195 * ((y - 1545) / 375.0)**0.9)
        draw.line([(0, y), (1080, y)], fill=(8, 8, 12, a))

    archetype = rt.ARCHETYPE_CONFIG.get(spec.get("storyType", "council_decision"), rt.ARCHETYPE_CONFIG["council_decision"])
    accent_rgb = archetype["accent"]

    if spec.get("branding", {}).get("showCaptions", False):
        rt.render_phrase_caption_pill(overlay, scene.get("voiceoverText", ""), t=t, total_dur=total_dur, y_top=1540, accent_rgb=accent_rgb)

    # Bottom Citation (clamped cleanly at y=1615, well above 1640)
    cite = scene.get("citationFooter", spec.get("meetingDateDisplay", "Council Public Record"))
    cite_str = cite.strip().lstrip("<").rstrip(">")
    f_cite = rt.get_font(rt.FONT_SANS_BOLD, 21)
    for cl in rt.wrap_text(draw, cite_str, f_cite, SAFE_WIDTH)[:1]:
        cw = draw.textlength(cl, font=f_cite)
        draw.text(((1080 - cw) // 2, 1615), cl, font=f_cite, fill=(225, 230, 240, 255))

    rt.apply_ai_disclaimer(overlay, show=scene.get("visualAsset", {}).get("isIllustrative", False))
    return overlay


def create_scene_overlay_image(spec, scene, total_scenes=5, show_logo=True, t=10.0, total_dur=6.0):
    """Generates the official template-based broadcast image for any scene at time t."""
    layout = scene_layout(scene)
    spec = {**spec, **{key: scene[key] for key in ("keyPoints", "keyPointsHeading", "takeawayCard") if key in scene}}
    renderers = {
        "hook": render_template_scene1_hook,
        "receipt": render_template_scene2_receipt,
        "key_points": render_template_scene3_key_points,
        "facts_figures": render_template_scene4_facts_figures,
    }
    if layout == "outro":
        return create_outro_archive_card_image(spec, scene, total_scenes=total_scenes, show_logo=show_logo, t=t, total_dur=total_dur)
    return renderers[layout](spec, scene, t=t, total_dur=total_dur)


def create_scene_overlay(out_path, spec, scene, total_scenes=5, show_logo=True):
    """Generates the static broadcast overlay PNG for fallback / testing."""
    img = create_scene_overlay_image(spec, scene, total_scenes=total_scenes, show_logo=show_logo, t=10.0, total_dur=6.0)
    img.save(out_path)


def create_outro_archive_card_image(spec, scene, total_scenes=5, show_logo=True, t=10.0, total_dur=8.8):
    """
    Renders the official Scene 5 Outro sequence on a textured dark London borough map:
    - Phase 1 (0.0s..4.0s): Street sign (6.png) holding for 4.0s with authentic archive story URL
    - Transition (4.0s..4.6s): Smooth 0.6s cinematic crossfade
    - Phase 2 (4.6s..8.8s+): Grand finale Selling Point slide (London Local.png) holding for 4+ seconds
    """
    fig_type = scene.get("figure", {}).get("type", "")
    if fig_type == "broadsheet_audit":
        return _render_legacy_audit_card(spec, scene, total_scenes=total_scenes, show_logo=show_logo, t=t)

    story_id = str(spec.get("displayStoryId", spec.get("storyId", "4178")))
    borough = spec.get("borough", "Westminster")
    archetype = rt.ARCHETYPE_CONFIG.get(spec.get("storyType", "council_decision"), rt.ARCHETYPE_CONFIG["council_decision"])
    accent_rgb = archetype["accent"]

    # Cached atmospheric textured dark London borough backdrop
    if not hasattr(create_outro_archive_card_image, "_backdrop_cache"):
        create_outro_archive_card_image._backdrop_cache = {}
    cache_key = f"{borough}_{accent_rgb}"
    if cache_key not in create_outro_archive_card_image._backdrop_cache:
        create_outro_archive_card_image._backdrop_cache[cache_key] = rt.create_textured_borough_backdrop(borough=borough, accent_rgb=accent_rgb)
    bg_backdrop = create_outro_archive_card_image._backdrop_cache[cache_key]

    # Street sign outro card (6.png) over textured borough map
    outro_sign = rt.render_outro_card(
        story_id=story_id,
        bg_image=bg_backdrop,
        borough=borough,
        accent_rgb=accent_rgb,
    )

    # Selling point payoff (London Local.png: "Local news, from your council.") over textured borough map
    selling_point = rt.render_selling_point_slide(
        bg_image=bg_backdrop,
        borough=borough,
        accent_rgb=accent_rgb,
    )

    # Narrative pacing:
    # Clean transition between selling point and street sign (fades out text to avoid double-exposure clash)
    t_mid = min(3.0, max(1.8, total_dur * 0.40))
    t_fade_half = 0.15
    if t < t_mid - t_fade_half:
        return selling_point
    elif t > t_mid + t_fade_half:
        return outro_sign
    else:
        progress = (t - (t_mid - t_fade_half)) / (2 * t_fade_half)
        if progress < 0.5:
            dim = 1.0 - (progress * 2)
            return Image.blend(bg_backdrop, selling_point, dim)
        else:
            bright = (progress - 0.5) * 2
            return Image.blend(bg_backdrop, outro_sign, bright)


def _render_legacy_audit_card(spec, scene, total_scenes=5, show_logo=True, t=10.0):
    """Fallback: Renders the legacy Scene 5 Broadsheet Audit Trail table."""
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
    draw.text((ox, 530), audit_hdr, font=get_font(FONT_SANS_BOLD, 21), fill=DOT_ORANGE + (255,))

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
        b_col = tuple(rec.get("badgeColor", list(DOT_ORANGE))) + (255,)
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

        fingerprint = audio_fingerprint(text, voice)
        stamp_path = out_mp3 + ".sha256"
        try:
            with open(stamp_path, encoding="utf-8") as stamp:
                cache_matches = stamp.read().strip() == fingerprint
        except FileNotFoundError:
            cache_matches = False

        if not force_refresh and cache_matches and os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 1000:
            success = True
        else:
            success = False
            for attempt in range(3):
                try:
                    cmd = ["edge-tts", "--voice", voice, "--rate=+18%", "--text", text, "--write-media", out_mp3]
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    success = True
                    break
                except Exception:
                    time.sleep(1.2)

            if not success:
                try:
                    cmd = ["edge-tts", "--voice", "en-GB-LibbyNeural", "--rate=+18%", "--text", text, "--write-media", out_mp3]
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    success = True
                except Exception:
                    pass

            if not success:
                raise RuntimeError(f"TTS failed for scene {num}; no silent fallback is permitted")
            with open(stamp_path, "w", encoding="utf-8") as stamp:
                stamp.write(fingerprint + "\n")

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


def render_story_from_spec(spec_path, show_logo=True, force_tts=False, draft=False):
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    check_render_contract(spec, draft=draft)
    output_dir = os.path.join(BUILD_DIR, "drafts") if draft else OUTPUT_DIR
    video_id = spec.get("videoId", "sample_video")
    story_id = str(spec.get("storyId", "4178"))
    borough = spec.get("borough", "Westminster")
    timeline = spec.get("timeline", [])
    total_scenes = len(timeline)

    story_build_dir = os.path.join(BUILD_DIR, "drafts", "work", video_id) if draft else os.path.join(BUILD_DIR, video_id)
    os.makedirs(story_build_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Maintain backward compatibility with root assets/audio for story 4178
    if draft:
        story_audio_dir = os.path.join(story_build_dir, "draft_audio")
    elif story_id == "4178":
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
        pad_dur = dur + 0.18
        seg_out = os.path.join(story_build_dir, f"seg_{num}.mp4")

        vis = scene.get("visualAsset", {})
        vis_type = vis.get("type", "solid")
        vis_src = os.path.join(BASE_DIR, vis.get("source", ""))
        crop_mode = vis.get("cropMode", "full")
        trim_start = float(vis.get("trimStart", 0.0))

        if scene_layout(scene) == "outro":
            # Outro scene dynamically respects duration target (default 7.5s for 30s TikTok runtime)
            pad_dur = max(dur + 0.18, float(scene.get("durationSeconds", 7.5)))
            total_frames = int(pad_dur * 30)
            cmd = [
                "ffmpeg", "-y",
                "-f", "rawvideo", "-pix_fmt", "rgba", "-s", "1080x1920", "-r", "30", "-i", "-",
                "-i", mp3_path,
                "-filter_complex", "[1:a]apad[aud]",
                "-map", "0:v", "-map", "[aud]",
                "-r", "30",
                "-c:v", "libx264", "-t", f"{pad_dur:.3f}",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-ar", "24000", "-ac", "1", "-b:a", "192k",
                seg_out,
            ]
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for f_idx in range(total_frames):
                t_sec = f_idx / 30.0
                frame_img = create_outro_archive_card_image(spec, scene, total_scenes=total_scenes, show_logo=show_logo, t=t_sec, total_dur=pad_dur)
                proc.stdin.write(frame_img.tobytes())
            proc.stdin.close()
            proc.wait()
            segment_files.append(seg_out)
            print(f"  ✓ Scene {num} [Outro Archive - Animated Slide] encoded ({pad_dur:.2f}s @ 30fps)")
            continue

        if vis_type == "video" and os.path.exists(vis_src):
            # Probe source duration to prevent abrupt EOF looping or snapping
            try:
                probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", vis_src]
                src_dur = float(subprocess.check_output(probe_cmd).strip())
            except Exception:
                src_dur = 10.0

            # Dynamic pacing: clamp trim_start and subtly stretch PTS if scene outlasts remaining clip
            safe_trim = min(trim_start, max(0.0, src_dur - 2.0))
            avail_dur = max(0.5, src_dur - safe_trim)
            if pad_dur > avail_dur:
                speed_scale = avail_dur / pad_dur
                setpts_filter = f"setpts=(1/{speed_scale:.4f})*PTS,"
            else:
                setpts_filter = ""

            if crop_mode == "fast_push_in":
                # High-contrast rapid push-in (Camden mould hook)
                vf_chain = (
                    f"[0:v]{setpts_filter}"
                    "scale=1080:1920:force_original_aspect_ratio=increase,"
                    "crop=1080:1920,"
                    f"scale=w='1080*(1.0 + 0.20*min(t/{pad_dur:.3f}, 1.0))':h='1920*(1.0 + 0.20*min(t/{pad_dur:.3f}, 1.0))':eval=frame,"
                    "crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,"
                    "eq=contrast=1.24:brightness=-0.05:saturation=1.05,"
                    "fps=30[vid];"
                    "[vid][1:v]overlay=0:0[outv]"
                )
            elif crop_mode == "heat_shimmer":
                # Warm solar heat haze with subtle thermal breathing (smooth, zero camera shake)
                vf_chain = (
                    f"[0:v]{setpts_filter}"
                    "scale=1080:1920:force_original_aspect_ratio=increase,"
                    "crop=1080:1920,"
                    f"scale=w='1080*(1.0 + 0.05*min(t/{pad_dur:.3f}, 1.0))':h='1920*(1.0 + 0.05*min(t/{pad_dur:.3f}, 1.0))':eval=frame,"
                    "crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,"
                    "eq=contrast='1.12+0.03*sin(2.5*PI*t)':brightness='0.02+0.015*sin(2*PI*t)':saturation=1.25,"
                    "colorbalance=rs=0.12:gs=0.03:bs=-0.14,"
                    "fps=30[vid];"
                    "[vid][1:v]overlay=0:0[outv]"
                )
            elif crop_mode == "architectural_upper":
                # Depth-of-field editorial backdrop: calm, soft focus blur, dark vignette
                # Makes foreground documents and figures pop with zero dizzying 2x zoom-ins
                vf_chain = (
                    f"[0:v]{setpts_filter}"
                    "scale=1080:1920:force_original_aspect_ratio=increase,"
                    "crop=1080:1920,"
                    "gblur=sigma=12:steps=2,"
                    "eq=contrast=1.10:brightness=-0.14:saturation=0.85,"
                    "vignette=PI/4,"
                    "fps=30[vid];"
                    "[vid][1:v]overlay=0:0[outv]"
                )
            else:
                # Full 9:16 portrait documentary framing: grounded, smooth forward motion, no looping
                vf_chain = (
                    f"[0:v]{setpts_filter}"
                    "scale=1080:1920:force_original_aspect_ratio=increase,"
                    "crop=1080:1920,"
                    "eq=contrast=1.06:brightness=-0.05:saturation=0.92,"
                    "fps=30[vid];"
                    "[vid][1:v]overlay=0:0[outv]"
                )

            cmd = [
                "ffmpeg", "-y",
                "-ss", f"{safe_trim:.2f}",
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
                frame_img = create_scene_overlay_image(spec, scene, total_scenes=total_scenes, show_logo=show_logo, t=t_sec, total_dur=pad_dur)
                proc.stdin.write(frame_img.tobytes())
            proc.stdin.close()
            proc.wait()
            segment_files.append(seg_out)
            fig_label = scene.get("figure", {}).get("type", "overlay")
            print(f"  ✓ Scene {num} [Video: {crop_mode} + Animated Figure: {fig_label}] encoded ({pad_dur:.2f}s @ 30fps)")

        elif os.path.exists(vis_src):
            if crop_mode == "fast_push_in":
                # High-contrast rapid push-in on still image (Camden mould hook)
                vf_chain = (
                    f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                    f"crop=1080:1920,"
                    f"scale=w='1080*(1.0 + 0.20*min(t/{pad_dur:.3f}, 1.0))':h='1920*(1.0 + 0.20*min(t/{pad_dur:.3f}, 1.0))':eval=frame,"
                    f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,"
                    f"eq=contrast=1.24:brightness=-0.05:saturation=1.05,"
                    f"fps=30[bg];"
                    f"[bg][1:v]overlay=0:0[outv]"
                )
            elif crop_mode == "heat_shimmer":
                # Warm solar heat haze on still image (smooth, zero camera shake)
                vf_chain = (
                    f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                    f"crop=1080:1920,"
                    f"scale=w='1080*(1.0 + 0.05*min(t/{pad_dur:.3f}, 1.0))':h='1920*(1.0 + 0.05*min(t/{pad_dur:.3f}, 1.0))':eval=frame,"
                    f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,"
                    f"eq=contrast='1.12+0.03*sin(2.5*PI*t)':brightness='0.02+0.015*sin(2*PI*t)':saturation=1.25,"
                    f"colorbalance=rs=0.12:gs=0.03:bs=-0.14,"
                    f"fps=30[bg];"
                    f"[bg][1:v]overlay=0:0[outv]"
                )
            else:
                # Ultra-smooth subtle documentary camera drift (continuous subpixel pan, zero zoom resets)
                vf_chain = (
                    f"[0:v]scale=1160:2062:force_original_aspect_ratio=increase,"
                    f"crop=1160:2062,"
                    f"crop=1080:1920:x='(1160-1080)*(t/{pad_dur:.3f})':y='(2062-1920)*0.5',"
                    f"eq=brightness=-0.06:contrast=1.08:saturation=0.90,"
                    f"noise=alls=6:allf=t+u[bg];"
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
                frame_img = create_scene_overlay_image(spec, scene, total_scenes=total_scenes, show_logo=show_logo, t=t_sec, total_dur=pad_dur)
                proc.stdin.write(frame_img.tobytes())
            proc.stdin.close()
            proc.wait()
            segment_files.append(seg_out)
            fig_label = scene.get("figure", {}).get("type", "overlay")
            print(f"  ✓ Scene {num} [35mm Motion ({crop_mode}) + Animated Figure: {fig_label}] encoded ({pad_dur:.2f}s @ 30fps)")

    print("=== 3. Concatenating Frame-Accurate 30fps Master MP4 ===")
    concat_list = os.path.join(story_build_dir, "concat_list.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for seg in segment_files:
            f.write(f"file '{seg}'\n")

    story_output = os.path.join(output_dir, f"{video_id}.mp4")
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        story_output,
    ]
    subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # If rendering flagship story 4178, also update canonical sample_video_4178_editorial.mp4
    if not draft and story_id == "4178":
        canonical_out = os.path.join(OUTPUT_DIR, "sample_video_4178_editorial.mp4")
        subprocess.run(["cp", story_output, canonical_out], check=True)
        story_output = canonical_out

    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
        "-of", "default=noprint_wrappers=1", story_output,
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    print(f"✅ {'Review Draft' if draft else 'Master'} Rendered: {story_output}")
    print(res.stdout.strip())

    # Automatically update stream-optimized faststart MP4 in demos/
    demo_map = {
        "4178": "westminster_4178_broadcast.mp4",
        "4182": "camden_4182_broadcast.mp4",
        "4185": "southwark_4185_broadcast.mp4",
        "10441": "d7_bus_10441_broadcast.mp4",
    }
    if not draft and story_id in demo_map:
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
    parser.add_argument("--draft", action="store_true", help="Render for review under build/drafts; do not update output or demos")
    args = parser.parse_args()

    show_logo = str(args.show_authorised_logo).lower() not in ("false", "0", "no")

    if args.batch:
        spec_files = sorted(glob.glob(os.path.join(BASE_DIR, "specs/*.json")))
        print(f"🚀 Simultaneous Multi-Story Batch Mode: Found {len(spec_files)} story specs")
        outputs = []
        for sp in spec_files:
            out = render_story_from_spec(sp, show_logo=show_logo, force_tts=args.force_tts, draft=args.draft)
            outputs.append(out)
        print("\n==================================================================")
        print(f"🎉 BATCH COMPLETE: {len(outputs)} Broadcast Videos Rendered:")
        for o in outputs:
            print(f"  • {o}")
        print("==================================================================")
    else:
        render_story_from_spec(args.spec, show_logo=show_logo, force_tts=args.force_tts, draft=args.draft)


if __name__ == "__main__":
    main()
