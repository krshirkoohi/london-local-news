#!/usr/bin/env python3
"""
London Local Reusable Asset & Template Engine
=============================================
Engineered from the official brand design templates:
- Persistent watermark.png (London Local. serif logo at top center)
- AI disclaimer.png (AI-GENERATED MEDIA pill at bottom center)
- Main headline.png (Centered serif title & subtitle hook layout)
- 4.png (Key points broadsheet layout with <cite_source> citations)
- 5.png (Facts and figures container frame with bottom citation)
- 6.png (Authentic London enamel street sign outro plate)
- London Local.png (Value proposition selling point: "Local news, from your council.")

All templates are pixel-calibrated for 9:16 vertical short-form broadcast video (1080x1920).
"""

import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "assets", "templates")

# Core typography matching the official design templates (Georgia / Georgia Bold)
FONT_SERIF_BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
FONT_SERIF = "/System/Library/Fonts/Supplemental/Georgia.ttf"
FONT_SANS_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_SANS = "/System/Library/Fonts/Supplemental/Arial.ttf"

_font_cache = {}


def get_font(font_path, size):
    key = (font_path, size)
    if key not in _font_cache:
        try:
            _font_cache[key] = ImageFont.truetype(font_path, size)
        except Exception:
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


def wrap_text(draw, text, font, max_width):
    words = text.split(" ")
    lines = []
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


# ==============================================================================
# 1. PERSISTENT WATERMARK & AI DISCLAIMER REUSABLE COMPONENTS
# ==============================================================================


def apply_persistent_watermark(image):
    """Applies the master London Local. persistent watermark at top-centre."""
    wm_path = os.path.join(TEMPLATES_DIR, "Persistent watermark.png")
    if os.path.exists(wm_path):
        wm = Image.open(wm_path)
        image.paste(wm, (0, 0), wm)
    else:
        draw = ImageDraw.Draw(image)
        f_wm = get_font(FONT_SERIF_BOLD, 54)
        txt = "London Local."
        w = draw.textlength(txt, font=f_wm)
        draw.text(((1080 - w) // 2, 125), txt, font=f_wm, fill=(255, 255, 255, 255))
    return image


def apply_ai_disclaimer(image, show=True):
    """Applies the official AI-GENERATED MEDIA disclaimer badge at bottom-centre."""
    if not show:
        return image
    disc_path = os.path.join(TEMPLATES_DIR, "AI disclaimer.png")
    if os.path.exists(disc_path):
        disc = Image.open(disc_path)
        image.paste(disc, (0, 0), disc)
    else:
        draw = ImageDraw.Draw(image)
        f_disc = get_font(FONT_SANS_BOLD, 17)
        txt = "AI-GENERATED MEDIA"
        w = draw.textlength(txt, font=f_disc)
        draw.text(((1080 - w) // 2, 1782), txt, font=f_disc, fill=(155, 155, 165, 255))
    return image


# ==============================================================================
# 2. MAIN HEADLINE TITLE CARD (Hook Scene)
# ==============================================================================


def render_main_headline_card(headline, subtitle, bg_image=None, is_ai=True):
    """
    Renders the official Main headline title card.
    Headline at y=912..993 (Georgia Bold), Subtitle at y=1025..1086 (Georgia).
    Includes Persistent watermark and AI disclaimer.
    """
    if bg_image:
        card = bg_image.convert("RGBA").resize((1080, 1920))
    else:
        card = Image.new("RGBA", (1080, 1920), (14, 14, 20, 255))

    draw = ImageDraw.Draw(card)

    apply_persistent_watermark(card)

    f_h1 = get_font(FONT_SERIF_BOLD, 80)
    h1_lines = wrap_text(draw, headline, f_h1, 880)

    f_sub = get_font(FONT_SERIF_BOLD, 50)
    sub_lines = wrap_text(draw, subtitle, f_sub, 880)

    total_h = len(h1_lines) * 92 + 30 + len(sub_lines) * 62
    start_y = 1000 - (total_h // 2)

    cur_y = start_y
    for line in h1_lines:
        lw = draw.textlength(line, font=f_h1)
        draw.text(((1080 - lw) // 2, cur_y), line, font=f_h1, fill=(255, 255, 255, 255))
        cur_y += 92

    cur_y += 24
    for line in sub_lines:
        lw = draw.textlength(line, font=f_sub)
        draw.text(((1080 - lw) // 2, cur_y), line, font=f_sub, fill=(255, 255, 255, 255))
        cur_y += 62

    apply_ai_disclaimer(card, show=is_ai)
    return card


# ==============================================================================
# 3. KEY POINTS BROADSHEET COMPONENT (4.png Template)
# ==============================================================================


def render_key_points_card(points, bg_image=None, is_ai=False):
    """
    Renders the official Key points broadsheet card from 4.png.
    points: list of tuples [ (point_text, citation_text), ... ] (up to 3)
    Each point is formatted with a bold subject anchor for instant TikTok scannability.
    """
    if bg_image:
        card = bg_image.convert("RGBA").resize((1080, 1920))
    else:
        card = Image.new("RGBA", (1080, 1920), (14, 14, 20, 255))

    draw = ImageDraw.Draw(card)
    f_title = get_font(FONT_SERIF_BOLD, 92)
    draw.text((109, 135), "Key points", font=f_title, fill=(255, 255, 255, 255))

    f_anchor = get_font(FONT_SERIF_BOLD, 52)
    f_sub = get_font(FONT_SERIF, 34)
    f_cite = get_font(FONT_SERIF, 26)

    start_y = 380
    spacing = 380

    for idx, pt in enumerate(points[:3]):
        py = start_y + idx * spacing
        if len(pt) == 3:
            anchor, sub, cite_text = pt
        elif len(pt) == 2:
            pt_text, cite_text = pt
            if " · " in pt_text:
                anchor, sub = pt_text.split(" · ", 1)
            else:
                words = pt_text.split()
                if len(words) > 4:
                    anchor = " ".join(words[:4])
                    sub = " ".join(words[4:])
                else:
                    anchor = pt_text
                    sub = ""
        else:
            anchor = str(pt[0])
            sub = ""
            cite_text = "Council Public Record"

        draw.line([(109, py + 8), (109, py + 52)], fill=(245, 158, 11, 240), width=4)
        draw.text((128, py), anchor, font=f_anchor, fill=(255, 255, 255, 255))

        sub_y = py + 70
        if sub:
            for line in wrap_text(draw, sub, f_sub, 840)[:2]:
                draw.text((128, sub_y), line, font=f_sub, fill=(220, 225, 235, 255))
                sub_y += 46

        cite_str = cite_text.strip().lstrip("<").rstrip(">")
        draw.text((128, sub_y + 10), cite_str, font=f_cite, fill=(155, 160, 170, 255))

    apply_ai_disclaimer(card, show=is_ai)
    return card


# ==============================================================================
# 4. FACTS AND FIGURES FRAME COMPONENT (5.png Template)
# ==============================================================================


def render_facts_figures_card(inner_renderer_fn, citation_source, bg_image=None, glass_mode=True, is_ai=False):
    """
    Renders the official Facts and figures frame from 5.png.
    Header: 'Facts and figures' at top-left (y=119..225).
    Container: x=[108, 971], y=[282, 1741] (width=864, height=1460).
    Bottom Citation: <cite_source> centered at y=1774.
    """
    if bg_image:
        card = bg_image.convert("RGBA").resize((1080, 1920))
    else:
        card = Image.new("RGBA", (1080, 1920), (14, 14, 20, 255))

    template_file = "facts_and_figures_frame_glass.png" if glass_mode else "facts_and_figures_frame_solid.png"
    base_path = os.path.join(TEMPLATES_DIR, template_file)
    if os.path.exists(base_path):
        base = Image.open(base_path)
        card.paste(base, (0, 0), base)
    else:
        draw = ImageDraw.Draw(card)
        draw.text((108, 119), "Facts and figures", font=get_font(FONT_SERIF_BOLD, 92), fill=(255, 255, 255, 255))
        draw.rounded_rectangle([(108, 282), (971, 1741)], radius=18, fill=(12, 12, 18, 225), outline=(255, 255, 255, 55), width=2)

    if callable(inner_renderer_fn):
        inner_renderer_fn(card, container_box=(108, 282, 971, 1741))

    draw = ImageDraw.Draw(card)
    f_cite = get_font(FONT_SERIF, 36)
    cite_str = citation_source.strip().lstrip("<").rstrip(">")
    cw = draw.textlength(cite_str, font=f_cite)
    draw.text(((1080 - cw) // 2, 1774), cite_str, font=f_cite, fill=(216, 216, 216, 255))

    apply_ai_disclaimer(card, show=is_ai)
    return card


# ==============================================================================
# 5. ENAMEL STREET SIGN OUTRO PLATE (6.png Template)
# ==============================================================================


def render_street_sign(story_id="4182", custom_text=None):
    """
    Renders an authentic isolated London enamel street sign (920x380) with 4 corner screws,
    double black enamel border, and custom story ID or text.
    """
    if custom_text:
        base_path = os.path.join(TEMPLATES_DIR, "street_sign_blank.png")
        sign = Image.open(base_path).convert("RGBA").copy()
        draw = ImageDraw.Draw(sign)
        f_top = get_font(FONT_SERIF_BOLD, 54)
        f_sub = get_font(FONT_SERIF_BOLD, 64)
        draw.text((60, 65), custom_text.get("top", "LONDONLOCAL.NEWS/").upper(), font=f_top, fill=(15, 15, 20, 255))
        draw.text((60, 140), custom_text.get("title", "COUNCIL REPORT").upper(), font=f_sub, fill=(15, 15, 20, 255))
        draw.line([(60, 245), (860, 245)], fill=(15, 15, 20, 255), width=4)
        f_red = get_font(FONT_SERIF_BOLD, 38)
        draw.text((60, 265), custom_text.get("footer", "londonlocal.news"), font=f_red, fill=(217, 72, 63, 255))
        return sign

    base_path = os.path.join(TEMPLATES_DIR, "street_sign_story_base.png")
    sign = Image.open(base_path).convert("RGBA").copy()
    draw = ImageDraw.Draw(sign)
    f_num = get_font(FONT_SERIF, 108)
    draw.text((465, 138), str(story_id), font=f_num, fill=(217, 72, 63, 255))
    return sign


def create_textured_borough_backdrop(borough="Westminster", accent_rgb=(217, 72, 63)):
    """
    Creates an atmospheric, textured dark London borough map backdrop (1080x1920).
    Features deep slate gradients, subtle borough boundary vector lines, and tactile film grain.
    """
    w, h = 1080, 1920
    base = Image.new("RGBA", (w, h), (12, 13, 18, 255))
    draw = ImageDraw.Draw(base)
    for y in range(h):
        val = int(12 + (y / h) * 8)
        draw.line([(0, y), (w, y)], fill=(val, val + 1, val + 4, 255))

    # Composite London borough map across center at subtle civic watermark opacity (26%)
    map_crop = generate_borough_map_overlay(borough, width=1280, height=960, zoom=1.0, accent_rgb=accent_rgb)
    if map_crop:
        r, g, b, a = map_crop.split()
        a = a.point(lambda p: int(p * 0.26))
        map_crop.putalpha(a)
        base.paste(map_crop, (-100, 480), map_crop)

    # Cinematic vertical vignette to preserve maximum contrast for text & street sign
    vignette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(vignette)
    for y in range(h):
        if y < 380:
            a = int(190 * (1.0 - y / 380.0))
            v_draw.line([(0, y), (w, y)], fill=(8, 9, 14, a))
        elif y > 1250:
            a = int(195 * ((y - 1250.0) / 670.0))
            v_draw.line([(0, y), (w, y)], fill=(8, 9, 14, a))
    base = Image.alpha_composite(base, vignette)

    # Tactile film grain noise
    np.random.seed(42)
    noise = np.random.normal(0, 5.0, (h, w)).astype(np.int16)
    arr = np.array(base.convert("RGB"), dtype=np.int16)
    arr[:, :, 0] = np.clip(arr[:, :, 0] + noise, 0, 255)
    arr[:, :, 1] = np.clip(arr[:, :, 1] + noise, 0, 255)
    arr[:, :, 2] = np.clip(arr[:, :, 2] + noise, 0, 255)
    textured = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    return textured


def render_outro_card(story_id="4182", bg_image=None, borough="Westminster", accent_rgb=(217, 72, 63)):
    """
    Renders the official Scene 5 outro card from 6.png over a textured dark London borough map:
    - 'Read the full story' at top (y=260)
    - Authentic London street sign with dynamic story_id (y=752..1125)
    - 'Find it at London Local.' with tagline at bottom (y=1400..1650)
    """
    if bg_image:
        card = bg_image.convert("RGBA").resize((1080, 1920))
    else:
        card = create_textured_borough_backdrop(borough=borough, accent_rgb=accent_rgb)

    base_path = os.path.join(TEMPLATES_DIR, "outro_base_full.png")
    if os.path.exists(base_path):
        base = Image.open(base_path)
        card.paste(base, (0, 0), base)
    else:
        draw = ImageDraw.Draw(card)
        draw.text((300, 260), "Read the full story", font=get_font(FONT_SERIF_BOLD, 68), fill=(255, 255, 255, 255))
        sign = render_street_sign(story_id=story_id)
        card.paste(sign, (80, 750), sign)

    draw = ImageDraw.Draw(card)
    sid_str = str(story_id)
    num_size = 86 if len(sid_str) >= 5 else 108
    f_num = get_font(FONT_SERIF, num_size)
    draw.rectangle([(530, 885), (890, 1020)], fill=(251, 251, 251, 255))
    y_num = 900 if len(sid_str) >= 5 else 888
    draw.text((545, y_num), sid_str, font=f_num, fill=(217, 72, 63, 255))

    # Authentic mission statement below street sign plate
    f_sub = get_font(FONT_SERIF, 32)
    sub_txt = "Direct from council agendas to your phone."
    sw = draw.textlength(sub_txt, font=f_sub)
    draw.text(((1080 - sw) // 2, 1220), sub_txt, font=f_sub, fill=(210, 215, 225, 255))

    return card


# ==============================================================================
# 6. SELLING POINT VALUE PROPOSITION SLIDE ("London Local.png" Template)
# ==============================================================================


def render_selling_point_slide(custom_statement=None, bg_image=None, borough="Westminster", accent_rgb=(217, 72, 63)):
    """
    Renders the official London Local value proposition slide from London Local.png:
    'Local news, from your council.'
    Clean, bold brand payoff with single red dot, 3 trust badges, and zero clutter over a textured borough map.
    """
    if bg_image:
        card = bg_image.convert("RGBA").resize((1080, 1920)).copy()
    else:
        card = create_textured_borough_backdrop(borough=borough, accent_rgb=accent_rgb)

    d = ImageDraw.Draw(card)
    apply_persistent_watermark(card)

    f_main = get_font(FONT_SERIF_BOLD, 84)
    line1 = custom_statement[0] if custom_statement else "Local news, from"
    line2 = custom_statement[1].rstrip(".") if custom_statement else "your council"

    d.text((108, 800), line1, font=f_main, fill=(255, 255, 255, 255))
    d.text((108, 910), line2, font=f_main, fill=(255, 255, 255, 255))
    l_yc = d.textlength(line2, font=f_main)
    # The iconic single red dot acts as the period
    d.ellipse([(108 + l_yc + 8, 955), (108 + l_yc + 26, 973)], fill=(217, 72, 63, 255))

    d.line([(108, 1060), (972, 1060)], fill=(255, 255, 255, 45), width=1)

    f_sub = get_font(FONT_SERIF, 36)
    sub_txt = "Direct from council agendas to your phone."
    d.text((108, 1100), sub_txt, font=f_sub, fill=(210, 215, 225, 255))

    f_bot = get_font(FONT_SERIF, 34)
    bot_txt = "londonlocal.news"
    bw = d.textlength(bot_txt, font=f_bot)
    d.text(((1080 - bw) // 2, 1720), bot_txt, font=f_bot, fill=(180, 185, 195, 255))
    return card


# ==============================================================================
# 7. LONDON BOROUGH MAP OVERLAY & CAPTION COMPONENTS
# ==============================================================================

ARCHETYPE_CONFIG = {
    "housing": {
        "accent": (245, 158, 11),      # Warm Amber
        "secondary": (52, 211, 153),   # Emerald
        "badge": "HOUSING & ESTATES",
    },
    "council_decision": {
        "accent": (217, 72, 63),       # London Local Coral-Red
        "secondary": (245, 158, 11),   # Amber
        "badge": "FULL COUNCIL MOTION",
    },
    "environment_schools": {
        "accent": (52, 211, 153),      # Clean Air / Climate Emerald
        "secondary": (245, 158, 11),   # Amber
        "badge": "SCHOOLS & CLIMATE",
    },
}

_map_base_cache = {}


def generate_borough_map_overlay(borough_name, width=820, height=540, zoom=1.0, accent_rgb=(245, 158, 11)):
    """
    Renders an inverted, high-contrast dark broadsheet map of London
    from London borough map.png with the specified borough illuminated.
    Caches the base 1448x1086 render per borough for instant 30fps zoom/pan animation.
    """
    base_map_path = os.path.join(TEMPLATES_DIR, "London borough map.png")
    if not os.path.exists(base_map_path):
        return None
    from PIL import ImageFilter, ImageOps

    b_key = str(borough_name).strip().lower()
    cache_key = (b_key, tuple(accent_rgb))

    seeds = {
        "camden": (660, 420),
        "westminster": (670, 490),
        "southwark": (750, 600),
        "islington": (725, 425),
        "lambeth": (695, 620),
        "hackney": (780, 430),
        "tower hamlets": (805, 490),
        "waltham forest": (835, 315),
        "kensington and chelsea": (610, 515),
        "hammersmith and fulham": (575, 530),
        "wandsworth": (625, 620),
        "lewisham": (815, 635),
        "greenwich": (895, 595),
        "newham": (895, 465),
        "haringey": (735, 330),
        "barnet": (635, 270),
        "brent": (555, 395),
        "ealing": (480, 470),
    }
    seed = seeds.get(b_key, (660, 420))

    if cache_key not in _map_base_cache:
        raw_map = Image.open(base_map_path).convert("L")
        inv_map = ImageOps.invert(raw_map)

        work_map = Image.open(base_map_path).convert("RGB")
        ImageDraw.floodfill(work_map, seed, (255, 0, 0), thresh=45)

        mask = Image.new("L", (1448, 1086), 0)
        w_px = work_map.load()
        m_px = mask.load()
        for y in range(1086):
            for x in range(1448):
                r, g, b = w_px[x, y]
                if r > 200 and g < 50 and b < 50:
                    m_px[x, y] = 255

        mask = mask.filter(ImageFilter.GaussianBlur(1.2))

        map_img = Image.new("RGBA", (1448, 1086), (18, 18, 26, 255))
        fill_layer = Image.new("RGBA", (1448, 1086), tuple(accent_rgb) + (235,))
        map_img.paste(fill_layer, (0, 0), mask)

        inv_px = inv_map.load()
        out_px = map_img.load()
        for y in range(0, 1086, 2):
            for x in range(0, 1448, 2):
                v = inv_px[x, y]
                if v > 40:
                    a = min(220, int(v * 1.2))
                    col = (230, 235, 245, a)
                    out_px[x, y] = col
                    if x + 1 < 1448:
                        out_px[x + 1, y] = col
                    if y + 1 < 1086:
                        out_px[x, y + 1] = col
                    if x + 1 < 1448 and y + 1 < 1086:
                        out_px[x + 1, y + 1] = col

        _map_base_cache[cache_key] = map_img

    base_img = _map_base_cache[cache_key]
    # Base bounding box (320, 180, 1120, 880) -> 800x700 centered around central/inner London
    z = max(1.0, min(1.25, float(zoom)))
    half_w = int(400 / z)
    half_h = int(350 / z)
    cx = int(720 + (seed[0] - 720) * (1.0 - 1.0 / z) * 0.7)
    cy = int(530 + (seed[1] - 530) * (1.0 - 1.0 / z) * 0.7)
    x1 = max(0, min(1448 - 2 * half_w, cx - half_w))
    y1 = max(0, min(1086 - 2 * half_h, cy - half_h))
    cropped = base_img.crop((x1, y1, x1 + 2 * half_w, y1 + 2 * half_h)).resize((width, height), Image.Resampling.LANCZOS)
    return cropped


def render_phrase_caption_pill(image, voiceover_text, t=0.0, total_dur=6.0, y_top=1568):
    """
    Renders phrase-synchronized British-English broadcast captions inside the mobile safe zone
    (y=1568..1636, cleanly above the AI disclaimer at y=1706 and below scene cards).
    """
    if not voiceover_text or total_dur <= 0:
        return image

    words = [w for w in voiceover_text.strip().split() if w]
    if not words:
        return image

    # Group into readable 5-word broadcast phrases
    chunk_size = 5
    chunks = [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]
    progress = max(0.0, min(0.999, t / max(0.5, total_dur - 0.25)))
    chunk_idx = min(len(chunks) - 1, int(progress * len(chunks)))
    active_phrase = chunks[chunk_idx]

    draw = ImageDraw.Draw(image)
    f_cap = get_font(FONT_SANS_BOLD, 28)
    tw = draw.textlength(active_phrase, font=f_cap)
    pad_x = 28
    pill_w = min(940, int(tw + pad_x * 2))
    px1 = (1080 - pill_w) // 2
    px2 = px1 + pill_w
    py1, py2 = y_top, y_top + 64

    draw.rounded_rectangle(
        [(px1, py1), (px2, py2)],
        radius=16,
        fill=(10, 10, 15, 228),
        outline=(255, 255, 255, 55),
        width=1,
    )
    tx = (1080 - int(tw)) // 2
    draw.text((tx, py1 + 15), active_phrase, font=f_cap, fill=(255, 255, 255, 255))
    return image
