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

# Unified brand color system (Pure White, Light Grey, Signature Dot Orange)
DOT_ORANGE = (254, 107, 33)  # Official London Local dot orange (#FE6B21)
COLOR_WHITE = (255, 255, 255)
COLOR_LIGHT_GREY = (225, 230, 240)
COLOR_MUTED_GREY = (170, 175, 185)

ARCHETYPE_CONFIG = {
    "transport": {
        "accent": DOT_ORANGE,
        "secondary": COLOR_LIGHT_GREY,
        "badge": "TFL CONSULTATION",
    },
    "housing": {
        "accent": DOT_ORANGE,
        "secondary": COLOR_LIGHT_GREY,
        "badge": "HOUSING & ESTATES",
    },
    "council_decision": {
        "accent": DOT_ORANGE,
        "secondary": COLOR_LIGHT_GREY,
        "badge": "FULL COUNCIL MOTION",
    },
    "environment_schools": {
        "accent": DOT_ORANGE,
        "secondary": COLOR_LIGHT_GREY,
        "badge": "SCHOOLS & CLIMATE",
    },
}

_font_cache = {}


def resolve_font_path(font_path):
    if font_path and os.path.exists(font_path):
        return font_path

    # Cross-platform fallbacks for Linux CI (fonts-liberation / fonts-dejavu-core)
    linux_fallbacks = {
        "Georgia Bold": [
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        ],
        "Georgia": [
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        ],
        "Arial Bold": [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ],
        "Arial": [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ],
    }
    for name, paths in linux_fallbacks.items():
        if name in (font_path or ""):
            for p in paths:
                if os.path.exists(p):
                    return p
    return font_path


def get_font(font_path, size):
    resolved = resolve_font_path(font_path)
    key = (resolved, size)
    if key not in _font_cache:
        try:
            _font_cache[key] = ImageFont.truetype(resolved, size)
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


def fit_text_to_bounds(draw, text, font_name, initial_size, max_width, max_height=None, max_lines=3, min_size=20):
    """
    Quality Control Utility:
    Dynamically measures, steps down font size, and wraps text so it fits
    strictly within max_width and max_lines without clipping or overflowing.
    Every rendered line must be <= max_width.
    """
    size = initial_size
    while size >= min_size:
        font = get_font(font_name, size)
        raw_lines = text.split("\n")
        all_wrapped = []
        for rl in raw_lines:
            all_wrapped.extend(wrap_text(draw, rl, font, max_width))
        
        line_spacing = int(size * 1.18)
        total_h = len(all_wrapped) * line_spacing
        lines_fit = len(all_wrapped) <= max_lines
        height_fit = (max_height is None or total_h <= max_height)
        width_fit = all(draw.textlength(l, font=font) <= max_width for l in all_wrapped)
        if lines_fit and height_fit and width_fit:
            return font, all_wrapped, line_spacing
        size -= 2

    font = get_font(font_name, min_size)
    raw_lines = text.split("\n")
    all_wrapped = []
    for rl in raw_lines:
        all_wrapped.extend(wrap_text(draw, rl, font, max_width))
    clamped_lines = []
    for l in all_wrapped[:max_lines]:
        while draw.textlength(l, font=font) > max_width and len(l) > 3:
            l = l[:-2] + "…"
        clamped_lines.append(l)
    return font, clamped_lines, int(min_size * 1.18)


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

        draw.line([(109, py + 8), (109, py + 52)], fill=(254, 107, 33, 240), width=4)
        draw.text((128, py), anchor, font=f_anchor, fill=(255, 255, 255, 255))

        sub_y = py + 70
        if sub:
            for line in wrap_text(draw, sub, f_sub, 760)[:2]:
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
        draw.rounded_rectangle([(108, 282), (905, 1600)], radius=18, fill=(12, 12, 18, 225), outline=(255, 255, 255, 55), width=2)

    if callable(inner_renderer_fn):
        inner_renderer_fn(card, container_box=(108, 282, 905, 1600))

    draw = ImageDraw.Draw(card)
    f_cite = get_font(FONT_SERIF, 32)
    cite_str = citation_source.strip().lstrip("<").rstrip(">")
    cw = draw.textlength(cite_str, font=f_cite)
    draw.text(((1080 - cw) // 2, 1625), cite_str, font=f_cite, fill=(216, 216, 216, 255))

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
        draw.text((60, 265), custom_text.get("footer", "londonlocal.news"), font=f_red, fill=(254, 107, 33, 255))
        return sign

    base_path = os.path.join(TEMPLATES_DIR, "street_sign_story_base.png")
    sign = Image.open(base_path).convert("RGBA").copy()
    draw = ImageDraw.Draw(sign)
    f_num = get_font(FONT_SERIF, 108)
    draw.text((465, 138), str(story_id), font=f_num, fill=(254, 107, 33, 255))
    return sign


def create_textured_borough_backdrop(borough="Westminster", accent_rgb=(254, 107, 33)):
    """
    Creates an atmospheric, high-definition textured dark London borough map backdrop (1080x1920).
    Features deep slate gradients, full 1:1 crisp vector lines with illuminated borough, and tactile film grain.
    """
    w, h = 1080, 1920
    base = Image.new("RGBA", (w, h), (14, 15, 20, 255))
    draw = ImageDraw.Draw(base)
    for y in range(h):
        val = int(12 + (y / h) * 10)
        draw.line([(0, y), (w, y)], fill=(val, val + 1, val + 4, 255))

    b_key = str(borough).strip().lower()
    # Prime cache
    generate_borough_map_overlay(borough, width=820, height=540, accent_rgb=accent_rgb)
    cache_key = (b_key, tuple(accent_rgb))
    full_map = _map_base_cache.get(cache_key)

    if full_map:
        seeds = {
            "camden": (660, 420),
            "westminster": (670, 490),
            "southwark": (750, 600),
            "tower hamlets": (840, 520),
            "isle of dogs": (840, 540),
            "greenwich": (895, 595),
            "hackney": (780, 430),
            "islington": (725, 425),
        }
        seed = seeds.get(b_key, (720, 530))
        crop_x1 = max(0, min(1448 - 1080, seed[0] - 540))
        crop_x2 = crop_x1 + 1080
        map_1to1 = full_map.crop((crop_x1, 0, crop_x2, 1086)).copy()

        r, g, b, a = map_1to1.split()
        a = a.point(lambda p: int(p * 0.35))
        map_1to1.putalpha(a)
        base.paste(map_1to1, (0, 417), map_1to1)

    # Cinematic vertical vignette to preserve maximum contrast
    vignette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(vignette)
    for y in range(h):
        if y < 420:
            a = int(180 * (1.0 - y / 420.0))
            v_draw.line([(0, y), (w, y)], fill=(10, 11, 15, a))
        elif y > 1320:
            a = int(190 * ((y - 1320.0) / 600.0))
            v_draw.line([(0, y), (w, y)], fill=(10, 11, 15, a))
    base = Image.alpha_composite(base, vignette)

    # Tactile film grain noise
    np.random.seed(42)
    noise = np.random.normal(0, 3.5, (h, w)).astype(np.int16)
    arr = np.array(base.convert("RGB"), dtype=np.int16)
    arr = np.clip(arr + noise[:, :, None], 0, 255).astype(np.uint8)
    return Image.fromarray(arr).convert("RGBA")


def render_outro_card(story_id="4182", bg_image=None, borough="Westminster", accent_rgb=DOT_ORANGE):
    """
    Renders the official Scene 5 outro card over a textured dark London borough map:
    - Master persistent watermark London Local. at top
    - Centered 'Read the full story' heading (y=460)
    - Authentic London enamel street sign with dynamic story_id (y=640..1020)
    - 'Direct from council agendas to your phone.' (y=1120)
    - Clean 'londonlocal.news' at bottom (y=1720)
    """
    if bg_image:
        card = bg_image.convert("RGBA").resize((1080, 1920)).copy()
    else:
        card = create_textured_borough_backdrop(borough=borough, accent_rgb=accent_rgb)

    draw = ImageDraw.Draw(card)
    apply_persistent_watermark(card)

    f_title = get_font(FONT_SERIF_BOLD, 72)
    txt = "Read the full story"
    tw = draw.textlength(txt, font=f_title)
    draw.text(((1080 - tw) // 2, 460), txt, font=f_title, fill=(255, 255, 255, 255))

    sign = render_street_sign(story_id=str(story_id))
    # Resize sign to fit safely within TikTok safe zones (max width 820px, centered horizontally on 1080px canvas)
    sign_w, sign_h = 820, int(380 * 820 / 920)
    sign_resized = sign.resize((sign_w, sign_h), Image.Resampling.LANCZOS)
    card.paste(sign_resized, ((1080 - sign_w) // 2, 660), sign_resized)

    f_sub = get_font(FONT_SERIF, 34)
    sub_txt = "Direct from council agendas to your phone."
    sw = draw.textlength(sub_txt, font=f_sub)
    draw.text(((1080 - sw) // 2, 1100), sub_txt, font=f_sub, fill=(215, 220, 230, 255))

    f_bot = get_font(FONT_SERIF, 32)
    bot_txt = "londonlocal.news"
    bw = draw.textlength(bot_txt, font=f_bot)
    draw.text(((1080 - bw) // 2, 1620), bot_txt, font=f_bot, fill=(180, 185, 195, 255))

    return card


# ==============================================================================
# 6. SELLING POINT VALUE PROPOSITION SLIDE ("London Local.png" Template)
# ==============================================================================


def render_selling_point_slide(custom_statement=None, bg_image=None, borough="Westminster", accent_rgb=DOT_ORANGE):
    """
    Renders the official London Local value proposition slide from London Local.png:
    'Local news, from your council.'
    Clean, bold brand payoff with single orange dot, 3 trust badges, and zero clutter over a textured borough map.
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
    # The iconic single dot in signature London Local dot orange
    d.ellipse([(108 + l_yc + 8, 955), (108 + l_yc + 26, 973)], fill=DOT_ORANGE + (255,))

    d.line([(108, 1060), (905, 1060)], fill=(255, 255, 255, 45), width=1)

    f_sub = get_font(FONT_SERIF, 36)
    sub_txt = "Direct from council agendas to your phone."
    d.text((108, 1100), sub_txt, font=f_sub, fill=(210, 215, 225, 255))

    f_bot = get_font(FONT_SERIF, 34)
    bot_txt = "londonlocal.news"
    bw = d.textlength(bot_txt, font=f_bot)
    d.text(((1080 - bw) // 2, 1620), bot_txt, font=f_bot, fill=(180, 185, 195, 255))
    return card


# ==============================================================================
# 7. LONDON BOROUGH MAP OVERLAY & CAPTION COMPONENTS
# ==============================================================================


_map_base_cache = {}


def generate_borough_map_overlay(borough_name, width=820, height=540, zoom=1.0, accent_rgb=DOT_ORANGE):
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
        "tower hamlets": (840, 520),
        "isle of dogs": (840, 540),
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
        if b_key in ("tower hamlets", "isle of dogs"):
            ImageDraw.Draw(work_map).line([(746, 452), (756, 470)], fill=(100, 100, 100), width=4)
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

        # Clean anti-aliased vector lines at full native 1448x1086 resolution
        raw_arr = np.array(raw_map, dtype=np.float32)
        line_intensity = np.clip((242.0 - raw_arr) * 1.6, 0.0, 220.0).astype(np.uint8)
        line_layer = Image.new("RGBA", (1448, 1086), (225, 230, 242, 0))
        line_layer.putalpha(Image.fromarray(line_intensity))
        map_img.alpha_composite(line_layer)

        _map_base_cache[cache_key] = map_img

    base_img = _map_base_cache[cache_key]
    # Base bounding box (800x700) centered on the illuminated borough seed
    z = max(1.0, min(1.25, float(zoom)))
    half_w = int(400 / z)
    half_h = int(350 / z)
    cx = int(seed[0])
    cy = int(seed[1])
    x1 = max(0, min(1448 - 2 * half_w, cx - half_w))
    y1 = max(0, min(1086 - 2 * half_h, cy - half_h))
    cropped = base_img.crop((x1, y1, x1 + 2 * half_w, y1 + 2 * half_h)).resize((width, height), Image.Resampling.LANCZOS)
    return cropped


def render_phrase_caption_pill(image, voiceover_text, t=0.0, total_dur=6.0, y_top=1568, accent_rgb=DOT_ORANGE):
    """
    Renders word-synchronized kinetic British-English broadcast captions inside the mobile safe zone
    (y=1568..1636, cleanly above the AI disclaimer at y=1706 and below scene cards).
    Highlights the currently spoken word in accent_rgb.
    """
    if not voiceover_text or total_dur <= 0:
        return image

    words = [w for w in voiceover_text.strip().split() if w]
    if not words:
        return image

    # Group into readable 4-word broadcast phrases
    chunk_size = 4
    chunks = [words[i : i + chunk_size] for i in range(0, len(words), chunk_size)]
    num_chunks = len(chunks)

    # Progress and active chunk
    chunk_dur = max(0.4, total_dur / num_chunks)
    chunk_idx = min(num_chunks - 1, max(0, int(t / chunk_dur)))
    active_words = chunks[chunk_idx]

    # Active word index within current chunk
    t_in_chunk = t - (chunk_idx * chunk_dur)
    word_dur = chunk_dur / max(1, len(active_words))
    active_word_idx = min(len(active_words) - 1, max(0, int(t_in_chunk / word_dur)))

    draw = ImageDraw.Draw(image)
    f_cap = get_font(FONT_SANS_BOLD, 28)

    space_w = draw.textlength(" ", font=f_cap)
    word_widths = [draw.textlength(w, font=f_cap) for w in active_words]
    total_text_w = sum(word_widths) + space_w * (len(active_words) - 1)

    pad_x = 28
    pill_w = min(940, int(total_text_w + pad_x * 2))
    px1 = (1080 - pill_w) // 2
    px2 = px1 + pill_w
    py1, py2 = y_top, y_top + 64

    # Opaque dark backing for maximum contrast over any B-roll
    draw.rounded_rectangle(
        [(px1, py1), (px2, py2)],
        radius=16,
        fill=(10, 10, 16, 235),
        outline=(255, 255, 255, 55),
        width=1,
    )

    cur_x = (1080 - int(total_text_w)) // 2
    for w_i, word in enumerate(active_words):
        w_len = word_widths[w_i]
        if w_i == active_word_idx:
            # Active word: illuminated in accent colour with high contrast
            draw.text((cur_x, py1 + 15), word, font=f_cap, fill=accent_rgb + (255,))
        elif w_i < active_word_idx:
            # Spoken words: clean bright white
            draw.text((cur_x, py1 + 15), word, font=f_cap, fill=(255, 255, 255, 255))
        else:
            # Upcoming words: subdued legible grey
            draw.text((cur_x, py1 + 15), word, font=f_cap, fill=(180, 185, 200, 200))
        cur_x += int(w_len + space_w)

    return image
