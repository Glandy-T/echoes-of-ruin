"""Build the Room 1 full-wall pixel surfaces.

This is deliberately authored as connected deposits and construction seams, not
as noise.  The four outputs share their first/last two columns, so the physical
wall corners do not reveal a texture seam when their UVs meet.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[3]
OUT = PROJECT / "assets/art/room1_seam_contact_r6"
LAYERS = ROOT / "source/wall_layers"
WALLS = {"left": (728, 272), "right": (728, 272), "front": (1648, 272), "rear": (1648, 272)}
BASE = (211, 214, 201, 255)
EDGE_PROFILE = [(188, 196, 185, 255), (211, 215, 202, 255)]

# Each wall gets a different non-repeating order.  The figures select one of
# four broad, hand-authored contour families; adjacent bays never select the
# same family.  The seam spacing itself remains the engineering rhythm.
VARIANT_ORDERS = {
    "left":  [0, 2, 1, 3, 0, 1],
    "right": [3, 1, 0, 2, 3, 0],
    "front": [1, 3, 0, 2, 1, 0, 3, 2, 0, 1, 3, 2, 1],
    "rear":  [2, 0, 3, 1, 2, 3, 0, 1, 3, 2, 0, 1, 2],
}
TOP = (
    (5, 9, 7, 15, 11, 19, 8, 13),
    (7, 14, 9, 17, 13, 8, 18, 10),
    (4, 11, 18, 12, 7, 15, 10, 20),
    (9, 6, 14, 19, 10, 16, 7, 13),
)
LOWER = (
    (13, 22, 17, 29, 20, 33, 19, 15),
    (19, 14, 28, 20, 34, 23, 17, 27),
    (15, 30, 22, 18, 32, 25, 35, 16),
    (24, 18, 31, 22, 16, 29, 21, 34),
)


def transparent(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def fade_edges(image: Image.Image, margin: int = 6) -> Image.Image:
    """Leave physical texture corners structurally identical across walls."""
    px = image.load()
    width, height = image.size
    for x in range(width):
        distance = min(x, width - 1 - x)
        if distance < 2:
            factor = 0.0
        elif distance < margin:
            factor = (distance - 1) / (margin - 1)
        else:
            continue
        for y in range(height):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, round(a * factor))
    return image


def structure(size):
    img = transparent(size)
    d = ImageDraw.Draw(img)
    rows = [
        (0, 10, "#BCC4B9"), (11, 12, "#D3D7CA"), (13, 13, "#E7E7D4"),
        (14, 15, "#A6B4B0"), (16, 17, "#52666B"), (18, 35, "#CCDDE4"),
        (36, 37, "#62777B"), (38, 39, "#9EAFAC"), (40, 41, "#E2E4D1"),
        (42, 43, "#C1C8BC"), (249, 249, "#B7C0B3"), (250, 251, "#485E63"),
        (252, 253, "#A5B6AE"), (254, 255, "#BBC5B7"), (256, 260, "#829591"),
        (261, 265, "#778C89"), (266, 268, "#687F7D"), (269, 269, "#A0ADA3"),
        (270, 271, "#344D55"),
    ]
    for y0, y1, colour in rows:
        d.rectangle((0, y0, size[0] - 1, y1), fill=colour)
    return img


def quiet_plane(size, wall):
    """Low-contrast broad mineral variation, never isolated speckles."""
    img = transparent(size)
    d = ImageDraw.Draw(img)
    w, _ = size
    offset = {"left": 0, "right": 47, "front": 89, "rear": 137}[wall]
    colours = ("#D7D9CB", "#CDD2C5", "#D1D5C8")
    for idx, x in enumerate(range(30 + offset % 41, w - 90, 221)):
        colour = colours[(idx + offset // 41) % len(colours)]
        y = 68 + ((idx * 37 + offset) % 57)
        # Wide faint mineral planes, deliberately held away from light/base.
        d.polygon([(x, y), (min(w - 12, x + 82), y - 3),
                   (min(w - 12, x + 118), y + 28), (x + 43, y + 43),
                   (x - 8, y + 27)], fill=colour)
    return fade_edges(img)


def seam_layer(size):
    img = transparent(size)
    d = ImageDraw.Draw(img)
    width, _ = size
    for x in range(48, width, 128):
        # Eight pixels total: two-pixel dark core with a restrained bevel.
        for dx, colour in ((-4, "#E7E7D4"), (-3, "#B8C4B7"), (-2, "#7D9190"),
                           (-1, "#52666B"), (0, "#52666B"), (1, "#78908D"),
                           (2, "#BBC6BA"), (3, "#D8DBCE")):
            d.line((x + dx, 44, x + dx, 248), fill=colour)
    return img


def profile_points(start, end, anchor, values, upward=False):
    """Two-pixel staircase boundary for an edge-connected deposit."""
    points = [(start, anchor), (end, anchor)]
    contour = []
    span = max(1, end - start)
    rhythm = (0, -1, 1, 0, 2, -1, 0, 1, -2, 0, 1, -1)
    for i, x in enumerate(range(start, end + 1, 2)):
        t = (x - start) / span
        sample = t * (len(values) - 1)
        at = int(sample)
        frac = sample - at
        depth = values[at] * (1 - frac) + values[min(at + 1, len(values) - 1)] * frac
        y = anchor - round(depth + rhythm[i % len(rhythm)]) if upward else anchor + round(depth + rhythm[i % len(rhythm)])
        if contour:
            contour.append((x, contour[-1][1]))
        contour.append((x, y))
    dpoints = points + list(reversed(contour))
    return dpoints


def deposits(size, wall):
    top = transparent(size)
    lower = transparent(size)
    dt, dl = ImageDraw.Draw(top), ImageDraw.Draw(lower)
    width, _ = size
    order = VARIANT_ORDERS[wall]
    breaks = list(range(0, width, 128)) + [width - 1]
    for bay, start in enumerate(breaks[:-1]):
        end = breaks[bay + 1]
        style = order[bay % len(order)]
        # The lower retention deliberately does not mirror the upper deposit.
        # That breaks the repeated-panel look while keeping all marks anchored.
        lower_style = (order[(bay + 1) % len(order)] + bay % 2) % 4
        # Deposits reach seam shoulders; only the two-pixel seal core is protected.
        for scale, colour in ((1.0, "#BBC3B5"), (.65, "#A7B3A5"), (.28, "#929F94")):
            vals = [round(v * scale) for v in TOP[style]]
            dt.polygon(profile_points(start, end, 44, vals), fill=colour)
        for scale, colour in ((1.0, "#B4BCAF"), (.65, "#9EA99C"), (.28, "#8B988D")):
            vals = [round(v * scale) for v in LOWER[lower_style]]
            dl.polygon(profile_points(start, end, 249, vals, upward=True), fill=colour)
    return fade_edges(top), fade_edges(lower)


def seam_film(size, wall):
    img = transparent(size)
    d = ImageDraw.Draw(img)
    width, _ = size
    order = VARIANT_ORDERS[wall]
    for i, x in enumerate(range(48, width, 128)):
        style = (order[(i + 2) % len(order)] + i % 2) % 4
        # Connected to one shoulder of its real structural seam; no free dots.
        if style in (0, 2):
            d.polygon([(x - 2, 70 + 4 * style), (x - 8, 70 + 4 * style),
                       (x - 8, 84 + 4 * style), (x - 11, 84 + 4 * style),
                       (x - 11, 113 + 3 * style), (x - 2, 113 + 3 * style)], fill="#B6C0B2")
            d.polygon([(x + 1, 185 - 3 * style), (x + 8, 185 - 3 * style),
                       (x + 8, 204 - 3 * style), (x + 11, 204 - 3 * style),
                       (x + 11, 228), (x + 1, 228)], fill="#A8B4A6")
        else:
            d.polygon([(x + 1, 96 + 2 * style), (x + 7, 96 + 2 * style),
                       (x + 7, 113 + 2 * style), (x + 10, 113 + 2 * style),
                       (x + 10, 142 + style), (x + 1, 142 + style)], fill="#B7C0B2")
            d.polygon([(x - 2, 158 - style), (x - 9, 158 - style),
                       (x - 9, 177 - style), (x - 12, 177 - style),
                       (x - 12, 203 - style), (x - 2, 203 - style)], fill="#A8B4A6")
    return fade_edges(img)


def contact(size, wall):
    img = transparent(size)
    d = ImageDraw.Draw(img)
    width, _ = size
    order = VARIANT_ORDERS[wall]
    for bay, x in enumerate(range(18, width - 20, 160)):
        style = order[bay % len(order)]
        end = min(width - 8, x + 37 + style * 7)
        d.polygon([(x, 260), (x + 11, 260), (x + 11, 258), (end - 12, 258),
                   (end - 12, 261), (end, 261), (end, 264), (x + 6, 264),
                   (x + 6, 262), (x, 262)], fill="#5D7672")
        d.line((x + 8, 255, min(end - 5, x + 31), 255), fill="#B3BEAD")
    return fade_edges(img)


def protect_joint_cores(img: Image.Image):
    """Protect diffuser and seal core, never punch a clean moat around aging."""
    px = img.load()
    w, h = img.size
    for x in range(w):
        for y in range(18, 36):
            px[x, y] = (0, 0, 0, 0)
    for x in range(48, w, 128):
        for xx in range(max(0, x - 1), min(w, x + 1)):
            for y in range(44, 249):
                px[xx, y] = (0, 0, 0, 0)
    return img


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    LAYERS.mkdir(parents=True, exist_ok=True)
    manifest = {"density_texels_per_m": 80, "walls": {}, "variants": {
        "top_deposit": 4, "lower_accumulation": 4, "joint_film": 4,
        "base_contact": 4, "composed_panel_variants": 8,
        "assignment": VARIANT_ORDERS,
    }, "continuity": "First and last two columns are the same base/structure profile on all four wall maps."}
    for wall, size in WALLS.items():
        base = Image.new("RGBA", size, BASE)
        layers = {
            "base": base,
            "quiet_mineral_plane": quiet_plane(size, wall),
            "structure": structure(size),
            "joints": seam_layer(size),
        }
        layers["base"].save(LAYERS / f"{wall}_base.png")
        layers["top_deposit"], layers["lower_accumulation"] = deposits(size, wall)
        layers["joint_seal_film"] = protect_joint_cores(seam_film(size, wall))
        layers["base_contact"] = contact(size, wall)
        result = base.copy()
        for name in ("quiet_mineral_plane", "structure", "joints", "top_deposit", "lower_accumulation", "joint_seal_film", "base_contact"):
            layers[name] = protect_joint_cores(layers[name]) if name in ("top_deposit", "lower_accumulation") else layers[name]
            layers[name].save(LAYERS / f"{wall}_{name}.png")
            result = Image.alpha_composite(result, layers[name])
        result.convert("RGB").save(OUT / f"wall_{wall}.png")
        manifest["walls"][wall] = {"size": list(size), "source_raster_sha256": hashlib.sha256((OUT / f"wall_{wall}.png").read_bytes()).hexdigest(),
                                   "joint_centers_px": list(range(48, size[0], 128))}
    (ROOT / "source/wall_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    build()
