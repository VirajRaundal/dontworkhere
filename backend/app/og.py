"""Open Graph share-image generation (1200x630 PNG) for an entry.

Rendered with Pillow so social/link unfurlers get a branded card. Avoids emoji
(no reliable color-emoji font cross-platform) and draws flag glyphs as shapes.
"""
import io
import textwrap

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
NAVY = (13, 27, 42)
NAVY_SOFT = (23, 42, 61)
CORAL = (255, 77, 77)
CREAM = (255, 248, 240)
CREAM_DIM = (255, 248, 240, 170)
GOLD = (255, 215, 0)
MUTED = (150, 165, 180)

_FONT_CANDIDATES = {
    "bold": [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ],
    "regular": [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
    ],
}


def _font(size: int, weight: str = "regular"):
    for path in _FONT_CANDIDATES[weight]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _flag(draw: ImageDraw.ImageDraw, x: int, y: int, h: int, on: bool):
    """Draw a small flag glyph (pole + pennant) at (x, y)."""
    pole = CREAM if on else (70, 84, 98)
    cloth = CORAL if on else (70, 84, 98)
    draw.rectangle([x, y, x + 3, y + h], fill=pole)
    draw.polygon([(x + 3, y), (x + 3 + h, y + h * 0.28), (x + 3, y + h * 0.55)], fill=cloth)


def render_og_png(entry: dict) -> bytes:
    img = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    # left accent bar
    draw.rectangle([0, 0, 16, H], fill=CORAL)

    pad = 80
    # brand row
    draw.text((pad, 56), "DONTWORKHERE", font=_font(28, "bold"), fill=CORAL)
    draw.text((pad, 92), "The toxic-boss accountability directory", font=_font(22), fill=MUTED)

    # quote (wrapped, truncated)
    quote = (entry.get("quote") or "").strip()
    qfont = _font(52, "bold")
    wrapped = textwrap.wrap(quote, width=34)
    if len(wrapped) > 5:
        wrapped = wrapped[:5]
        wrapped[-1] = wrapped[-1].rstrip(".,") + "…"
    y = 170
    draw.text((pad - 6, y - 40), "“", font=_font(120, "bold"), fill=(255, 77, 77))
    for line in wrapped:
        draw.text((pad, y), line, font=qfont, fill=CREAM)
        y += 64

    # attribution
    person = (entry.get("person_name") or "").strip()
    company = (entry.get("company_name") or "").strip()
    title = (entry.get("person_title") or "").strip()
    attrib = person + (f", {title}" if title else "") + (f"  ·  {company}" if company else "")
    draw.text((pad, 500), attrib[:80], font=_font(30, "bold"), fill=GOLD)

    # score flags (bottom-right)
    score = entry.get("red_flag_score") or 0
    try:
        score = int(score)
    except Exception:
        score = 0
    fx = W - pad - 5 * 34
    for i in range(5):
        _flag(draw, fx + i * 34, 506, 30, on=i < score)
    draw.text((W - pad - 5 * 34, 548), f"RED FLAG SCORE {score}/5", font=_font(18, "bold"), fill=MUTED)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
