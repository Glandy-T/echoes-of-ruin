"""Prepare the r32 door layers: M05-L powder-coat base + r30 structure/traces.

No new generation and no new mark shapes.  Every pixel comes from one of two
existing project textures:
  * M05-L.png  (PixelLab native 256x256, building art pack, 80 px/m)
  * r30 door_front.png (r29 PixelLab body + r30 Aseprite bezel cleanup)

Layers written to source/layers/ (RGBA, 112x184), assembled by build_aseprite.lua:
  1. m05l_base            native crop of M05-L, no scaling / flipping
  2. r30_darker_traces    r30 pixels darker than r30's flat coat, carried over
                          as the same relative darkness on the new base
                          (new = base * r30 / r30_coat, per channel)
  3. r30_structure        r30 seal ring and status aperture, absolute colours

r30 pixels lighter than its flat coat (74% of them form a 1-4 px bright rim
along the leaf edge) are not carried over: M05 forbids a bright edge ring, and
that rim is what read as a polished sheet-metal edge.

Run from repo root with Python 3.11 + Pillow + NumPy:
    python docs/art/experiments/room1_door_powder_r32/source/build_layers.py
"""
import json, hashlib, pathlib
import numpy as np
from PIL import Image, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[4]
M05L = ROOT / "assets/art/cryo_building_review_v1/textures/M05-L.png"
R30 = ROOT / "assets/art/room1_door_window_r30/door_front.png"
OUT = HERE / "layers"
OUT.mkdir(exist_ok=True)

W, H = 112, 184
R30_COAT = np.array([183, 192, 179])
SEAL = [np.array([105, 129, 124]), np.array([105, 130, 129])]
APERTURE = (51, 64, 62, 70)  # inclusive x0, y0, x1, y1 -- kept exactly (r30 README)

m05 = np.asarray(Image.open(M05L).convert("RGB")).astype(float)
r30 = np.asarray(Image.open(R30).convert("RGB")).astype(int)
assert r30.shape == (H, W, 3) and m05.shape == (256, 256, 3)

# Choose the native crop with the least large-scale shading, so the door
# carries M05-L's fine grain and not a broad light/dark patch.
lum = m05 @ [0.2126, 0.7152, 0.0722]
broad = np.asarray(Image.fromarray(lum.astype(np.uint8)).filter(ImageFilter.GaussianBlur(10))).astype(float)
best = None
for y in range(0, 256 - H + 1, 4):
    for x in range(0, 256 - W + 1, 4):
        s = broad[y:y + H, x:x + W].std()
        if best is None or s < best[0]:
            best = (s, x, y)
_, cx, cy = best
base = m05[cy:cy + H, cx:cx + W]

r30_lum = r30 @ [0.2126, 0.7152, 0.0722]
coat_lum = R30_COAT @ [0.2126, 0.7152, 0.0722]
is_coat = (r30 == R30_COAT).all(-1)
is_seal = np.zeros((H, W), bool)
for c in SEAL:
    is_seal |= (r30 == c).all(-1)
ap = np.zeros((H, W), bool)
x0, y0, x1, y1 = APERTURE
ap[y0:y1 + 1, x0:x1 + 1] = True
structure = is_seal | ap
darker = (~is_coat) & (~structure) & (r30_lum < coat_lum)
lighter = (~is_coat) & (~structure) & (r30_lum > coat_lum)

def rgba(rgb, mask):
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = np.clip(np.rint(rgb), 0, 255).astype(np.uint8)
    out[..., 3] = np.where(mask, 255, 0)
    return out

traces = base * (r30 / R30_COAT)
layers = {
    "m05l_base": rgba(base, np.ones((H, W), bool)),
    "r30_darker_traces": rgba(traces, darker),
    "r30_structure": rgba(r30, structure),
}
for name, arr in layers.items():
    Image.fromarray(arr, "RGBA").save(OUT / f"{name}.png")

flat = base.copy()
flat[darker] = traces[darker]
flat[structure] = r30[structure]
flat = np.clip(np.rint(flat), 0, 255).astype(np.uint8)
Image.fromarray(flat, "RGB").save(OUT / "expected_flat.png")

sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
record = {
    "inputs": {"M05-L": {"path": str(M05L.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(M05L)},
               "r30": {"path": str(R30.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(R30)}},
    "m05l_native_crop_xywh": [int(cx), int(cy), W, H],
    "pixels": {"base_only": int((~darker & ~structure).sum()), "r30_darker_traces": int(darker.sum()),
               "r30_structure": int(structure.sum()), "r30_lighter_dropped": int(lighter.sum())},
    "r30_lighter_dropped_within_4px_of_edge": round(float(((np.nonzero(lighter)[1] < 4) | (np.nonzero(lighter)[1] > W - 5) |
                                                         (np.nonzero(lighter)[0] < 4) | (np.nonzero(lighter)[0] > H - 5)).mean()), 3),
    "new_generation_requests": 0,
}
(HERE / "layer_record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
print(json.dumps(record, indent=1))
