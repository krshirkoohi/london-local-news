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
    """
    if bg_image:
        card = bg_image.convert("RGBA").resize((1080, 1920))
    else:
        card = Image.new("RGBA", (1080, 1920), (14, 14, 20, 255))

    base_path = os.path.join(TEMPLATES_DIR, "key_points_template_base.png")
    if os.path.exists(base_path):
        base = Image.open(base_path)
        card.paste(base, (0, 0), base)
    else:
        draw = ImageDraw.Draw(card)
        draw.text((109, 121), "Key points", font=get_font(FONT_SERIF_BOLD, 92), fill=(255, 255, 255, 255))

    draw = ImageDraw.Draw(card)
    f_point = get_font(FONT_SERIF, 46)
    f_cite = get_font(FONT_SERIF, 32)

    cur_y = 350
    for pt_text, cite_text in points[:3]:
        lines = wrap_text(draw, pt_text, f_point, 860)
        for line in lines[:4]:
            draw.text((110, cur_y), line, font=f_point, fill=(255, 255, 255, 255))
            cur_y += 62

        cur_y += 10
        cite_str = cite_text.strip().lstrip("<").rstrip(">")
        draw.text((110, cur_y), cite_str, font=f_cite, fill=(216, 216, 216, 255))
        cur_y += 110

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


def render_outro_card(story_id="4182", bg_image=None, debate_prompt=None, stakeholder_pills=None):
    """
    Renders the official Scene 5 outro card from 6.png.
    - 'Read the full story' at top (y=260)
    - Authentic London street sign with dynamic story_id (y=752..1125)
    - Optional Community debate prompt & stakeholder ward pills
    - 'Find it at London Local.' with tagline at bottom (y=1400..1650)
    """
    if bg_image:
        card = bg_image.convert("RGBA").resize((1080, 1920))
    else:
        card = Image.new("RGBA", (1080, 1920), (14, 14, 20, 255))

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
    f_num = get_font(FONT_SERIF, 108)
    draw.rectangle([(530, 885), (860, 1020)], fill=(251, 251, 251, 255))
    draw.text((545, 888), str(story_id), font=f_num, fill=(217, 72, 63, 255))

    if debate_prompt:
        box_y1, box_y2 = 1150, 1285
        draw.rounded_rectangle([(108, box_y1), (972, box_y2)], radius=12, fill=(20, 20, 28, 235), outline=(251, 191, 36, 120), width=1)
        f_deb_hdr = get_font(FONT_SANS_BOLD, 14)
        draw.text((132, box_y1 + 14), "COMMUNITY DEBATE · REPOST & TAG YOUR COUNCILLORS", font=f_deb_hdr, fill=(251, 191, 36, 255))
        f_deb_q = get_font(FONT_SERIF_BOLD, 22)
        q_lines = wrap_text(draw, debate_prompt, f_deb_q, 800)
        qy = box_y1 + 38
        for ql in q_lines[:2]:
            draw.text((132, qy), ql, font=f_deb_q, fill=(255, 255, 255, 255))
            qy += 28
        if stakeholder_pills:
            px = 132
            py = box_y2 - 34
            f_pill = get_font(FONT_SANS_BOLD, 13)
            for pill in stakeholder_pills[:3]:
                pw = int(draw.textlength(pill, font=f_pill) + 20)
                if px + pw > 950:
                    break
                draw.rounded_rectangle([(px, py), (px + pw, py + 24)], radius=12, fill=(35, 35, 48, 255), outline=(255, 255, 255, 40), width=1)
                draw.text((px + 10, py + 4), pill, font=f_pill, fill=(210, 210, 225, 255))
                px += pw + 10

    return card


# ==============================================================================
# 6. SELLING POINT VALUE PROPOSITION SLIDE ("London Local.png" Template)
# ==============================================================================


def render_selling_point_slide(custom_statement=None, pillars=None, bg_image=None):
    """
    Renders the official London Local value proposition slide from London Local.png:
    'Local news, from your council.'
    Enhanced with civic proof pillars, persistent watermark, and brand anchor.
    """
    if bg_image:
        card = bg_image.convert("RGBA").resize((1080, 1920))
    else:
        card = Image.new("RGBA", (1080, 1920), (14, 14, 20, 255))

    d = ImageDraw.Draw(card)
    for y in range(0, 1920):
        val = int(14 + (y / 1920) * 8)
        d.line([(0, y), (1080, y)], fill=(val, val, val + 2, 255))

    apply_persistent_watermark(card)

    f_main = get_font(FONT_SERIF_BOLD, 78)
    line1 = custom_statement[0] if custom_statement else "Local news, from"
    line2 = custom_statement[1] if custom_statement else "your council."

    d.text((108, 770), line1, font=f_main, fill=(255, 255, 255, 255))
    d.text((108, 870), line2, font=f_main, fill=(255, 255, 255, 255))
    l_yc = d.textlength(line2, font=f_main)
    d.ellipse([(108 + l_yc + 6, 915), (108 + l_yc + 22, 931)], fill=(217, 72, 63, 255))

    d.line([(108, 1010), (972, 1010)], fill=(255, 255, 255, 40), width=1)

    if pillars is None:
        pillars = [
            ("DIRECT FROM THE SOURCE", "Every story is anchored in verified council agendas, voting tallies, and financial order papers."),
            ("ZERO SENSATIONALISM", "Politically non-partisan civic intelligence designed to explain decisions, not farm rage."),
            ("HYPER-LOCAL IMPACT", "Focusing on the municipal policies that actually determine your rent, council tax, and neighbourhood."),
        ]

    f_pill_hdr = get_font(FONT_SANS_BOLD, 19)
    f_pill_body = get_font(FONT_SERIF, 26)

    py = 1070
    for hdr, desc in pillars:
        d.text((108, py), hdr, font=f_pill_hdr, fill=(245, 158, 11, 255))
        py += 34
        lines = wrap_text(draw=d, text=desc, font=f_pill_body, max_width=860)
        for l in lines:
            d.text((108, py), l, font=f_pill_body, fill=(230, 230, 240, 255))
            py += 36
        py += 26

    f_bot = get_font(FONT_SERIF, 32)
    bot_txt = "londonlocal.news  •  All 33 London Boroughs"
    bw = d.textlength(bot_txt, font=f_bot)
    d.text(((1080 - bw) // 2, 1720), bot_txt, font=f_bot, fill=(180, 180, 190, 255))
    return card
