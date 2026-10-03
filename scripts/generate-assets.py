#!/usr/bin/env python3
"""Generate favicons and touch icons from the source logo.

The source is a 2048x2048 JPEG whose mark occupies only a centred band, with a
dark navy gradient field around it. We locate the mark by luminance profile
rather than assuming a fixed crop, because the field is a gradient: thresholding
on distance-from-corner finds nothing.

Colour is never keyed to transparency. The mark has genuinely dark interior
regions (the globe's inner channels, the gap between the two rings), so any
luminance key would punch holes in it and leave a halo on the ring edges. Each
icon therefore keeps the logo's own background, which also means it reads as a
tile rather than a floating shape.

Usage: python3 scripts/generate-assets.py
"""

from pathlib import Path

import io

import cairosvg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "source" / "logo.jpg"
PUBLIC = ROOT / "public"
INTERNAL = ROOT / "src" / "assets"

LUMA_THRESHOLD = 80  # background sits near 46; the mark's lit surfaces are well above
MIN_COVERAGE = 0.01  # ignore stray JPEG noise rows/columns

# Alpha-matte thresholds for lifting the mark off its own navy field. Measured
# against this logo: background 4-60, ring surfaces 70+. See make_og().
MATTE_FLOOR = 60.0
MATTE_CEIL = 95.0


def find_mark(img: Image.Image) -> tuple[int, int, int, int]:
    """Bounding box of the mark, from luminance row/column profiles."""
    import numpy as np

    a = np.asarray(img.convert("RGB")).astype("float32")
    lum = 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]
    mask = lum > LUMA_THRESHOLD

    height, width = mask.shape
    rows = np.where(mask.sum(axis=1) > width * MIN_COVERAGE)[0]
    cols = np.where(mask.sum(axis=0) > height * MIN_COVERAGE)[0]
    return int(cols.min()), int(rows.min()), int(cols.max()), int(rows.max())


def mark_background(mark: Image.Image) -> tuple[int, int, int]:
    """The navy field the mark sits on, as a flat RGB triple.

    Taken from the median of the mark's own top and bottom border strips. The
    logo carries a vignette, so its field is not one colour, and the median is
    what lets us reproduce the edges faithfully enough for a matte.
    """
    import numpy as np

    edge = 8
    frame = np.concatenate(
        [
            np.asarray(mark.crop((0, 0, mark.width, edge))).reshape(-1, 3),
            np.asarray(mark.crop((0, mark.height - edge, mark.width, mark.height))).reshape(-1, 3),
        ]
    )
    return tuple(int(v) for v in np.median(frame, axis=0))


def matte_mark(mark: Image.Image, bg: tuple[int, int, int]) -> Image.Image:
    """Lift the mark off its background, keyed on distance from `bg`.

    Threshold values are measured, not guessed. Distance from the fill across the
    mark's own background regions spans roughly 4-60 (corners average 17-26; the
    bottom band averages 47 because of the drop shadow), while ring surfaces
    start near 70 and run to 300+. Keying at 60/95 therefore removes the entire
    background including its shadow without eroding the rings — which matters
    because the rings touch the bounding box horizontally, so a plain inset
    cannot protect them.

    Because the fill is the mark's own navy, everything this keys away (the
    globe's interior channels, the gaps between rings) reappears as the same
    navy underneath. That is why no halo forms.
    """
    import numpy as np

    arr = np.asarray(mark).astype("float32")
    dist = np.sqrt(((arr - np.array(bg, dtype="float32")) ** 2).sum(axis=2))
    alpha = np.clip((dist - MATTE_FLOOR) / (MATTE_CEIL - MATTE_FLOOR), 0.0, 1.0)
    mask = Image.fromarray((alpha * 255).astype("uint8"), "L").filter(ImageFilter.GaussianBlur(2.0))

    out = mark.convert("RGBA")
    out.putalpha(mask)
    return out


def square_tile(mark: Image.Image, size: int, pad: float = 0.07) -> Image.Image:
    """Centre the matted mark on a square canvas of its own field colour."""
    bg = mark_background(mark)
    fg = matte_mark(mark, bg)

    inner = int(size * (1 - pad * 2))
    scaled = fg.resize((inner, max(1, round(mark.height * inner / mark.width))), Image.LANCZOS)

    tile = Image.new("RGB", (size, size), bg)
    # Centre on the scaled image's own dimensions, not on `inner`: the mark is
    # 1.65:1, so using `inner` for the vertical offset lands it above centre.
    tile.paste(scaled, ((size - scaled.width) // 2, (size - scaled.height) // 2), scaled)
    return tile


def build_ttf() -> dict[str, Path]:
    """Convert Geist's woff files to TTF so PIL can render them.

    fontTools reads .woff with the stdlib zlib, so this needs no extra
    dependency. .woff2 would require brotli, which is not installed, and is not
    what we use here. The result is cached outside the repo because it is a
    build artefact, not a source file.
    """
    from fontTools.ttLib import TTFont

    out_dir = Path.home() / "tmp" / "ttf"
    out_dir.mkdir(parents=True, exist_ok=True)
    faces = {
        "GeistSans-400": "geist-sans/files/geist-sans-latin-400-normal.woff",
        "GeistSans-600": "geist-sans/files/geist-sans-latin-600-normal.woff",
        "GeistMono-400": "geist-mono/files/geist-mono-latin-400-normal.woff",
        "GeistMono-500": "geist-mono/files/geist-mono-latin-500-normal.woff",
    }
    resolved = {}
    for name, rel in faces.items():
        target = out_dir / f"{name}.ttf"
        if not target.exists():
            font = TTFont(ROOT / "node_modules" / "@fontsource" / rel)
            font.flavor = None
            font.save(target)
        resolved[name] = target
    return resolved


def tracked_text(
    draw: "ImageDraw.ImageDraw",
    xy: tuple[int, int],
    text: str,
    font: "ImageFont.FreeTypeFont",
    fill: tuple[int, int, int],
    tracking: float = 0.0,
) -> int:
    """Draw text with letter-spacing. Geist tracks headings at about -5% of size,
    which PIL has no native support for."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += round(draw.textlength(ch, font=font) + tracking)
    return x


def text_width(
    draw: "ImageDraw.ImageDraw", text: str, font: "ImageFont.FreeTypeFont", tracking: float = 0.0
) -> int:
    return round(
        sum(draw.textlength(c, font=font) + tracking for c in text) - tracking
    )


def make_og(src: Image.Image, mark: Image.Image, faces: dict[str, Path]) -> None:
    """1200x630 social card.

    The canvas is a flat fill of the logo's own field colour, sampled from the
    band above the mark so the pasted mark does not read as a pasted rectangle.
    An earlier version cropped the background out of the source, which was a
    mistake: the mark's bounding box starts partway into that band, so scaling
    the crop stretched the top of the rings across the whole card.
    """
    W, H = 1200, 630
    bg = mark_background(mark)
    mark_rgba = matte_mark(mark, bg)

    card = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(card)

    sans_600 = ImageFont.truetype(str(faces["GeistSans-600"]), 56)
    sans_400 = ImageFont.truetype(str(faces["GeistSans-400"]), 25)
    mono_400 = ImageFont.truetype(str(faces["GeistMono-400"]), 19)

    title = "opencode-shared-browser"
    subtitle = "One signed-in Chrome, shared across opencode instances."
    foot = "edrayel/opencode-shared-browser   ·   Apache-2.0"

    mark_w = 340
    mark_s = mark_rgba.resize((mark_w, round(mark.height * mark_w / mark.width)), Image.LANCZOS)
    mark_y = 74
    card.paste(mark_s, ((W - mark_w) // 2, mark_y), mark_s)

    # Centre each line on its own measured width, so tracking cannot skew it.
    def centred(text: str, font: ImageFont.FreeTypeFont, y: int, fill, tracking=0.0) -> None:
        w = text_width(draw, text, font, tracking)
        tracked_text(draw, ((W - w) // 2, y), text, font, fill, tracking)

    centred(title, sans_600, mark_y + mark_s.height + 52, (255, 255, 255), -1.6)
    centred(subtitle, sans_400, mark_y + mark_s.height + 136, (176, 190, 210))
    centred(foot, mono_400, H - 58, (134, 150, 176))

    card.save(PUBLIC / "og.png", optimize=True)
    print(f"wrote public/og.png {card.size} bg={bg}")


def main() -> None:
    src = Image.open(SRC).convert("RGB")
    print(f"source: {src.size[0]}x{src.size[1]}")

    left, top, right, bottom = find_mark(src)
    mark = src.crop((left, top, right + 1, bottom + 1))
    print(f"mark:   {mark.width}x{mark.height} at ({left},{top})")

    PUBLIC.mkdir(parents=True, exist_ok=True)
    INTERNAL.mkdir(parents=True, exist_ok=True)

    # Full mark for the header and any future use, at a sane weight.
    logo = mark.copy()
    logo.thumbnail((512, 512), Image.LANCZOS)
    logo.save(INTERNAL / "logo.png", optimize=True)
    print(f"wrote src/assets/logo.png {logo.size}")

    for size in (48, 180):
        tile = square_tile(mark, size)
        name = "apple-touch-icon.png" if size == 180 else f"favicon-{size}.png"
        tile.save(PUBLIC / name, optimize=True)
        print(f"wrote public/{name} {tile.size} (detailed raster)")

    # Below ~32px the detailed render is illegible, so the small PNGs are
    # rasterised from the simplified SVG mark instead. Browsers that understand
    # SVG use favicon.svg directly; these cover the rest.
    svg = (PUBLIC / "favicon.svg").read_text()
    for size in (16, 32):
        png = cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size)
        (PUBLIC / f"favicon-{size}.png").write_bytes(png)
        print(f"wrote public/favicon-{size}.png {size}x{size} (simplified mark)")

    # Multi-resolution .ico for legacy browsers, from the simplified mark so the
    # 16px entry stays readable.
    ico_base = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=256, output_height=256)))
    ico_base.save(PUBLIC / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    print("wrote public/favicon.ico [16,32,48] (simplified mark)")

    make_og(src, mark, build_ttf())


if __name__ == "__main__":
    main()