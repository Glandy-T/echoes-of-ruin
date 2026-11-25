"""Audit the actual deliverables against D, independently of the export code."""
from pathlib import Path
import json

import numpy as np
from PIL import Image, ImageSequence

HERE = Path(__file__).resolve().parent
OUT = HERE / "45"


def pixels(path):
    with Image.open(path) as im:
        return np.array(im.convert("RGBA"))


def mismatches(a, b):
    if a.shape != b.shape:
        raise ValueError(f"Size mismatch: {a.shape} vs {b.shape}")
    return int(np.any(a != b, axis=-1).sum())


def audit():
    original = HERE.parent / "protagonist_idle_pose_45_r1/D/raw/01.png"
    first = pixels(OUT / "01.png")
    second = pixels(OUT / "02.png")
    checks = {}
    if sorted(p.name for p in OUT.glob("[0-9][0-9].png")) != ["01.png", "02.png"]:
        raise ValueError("Expected exactly two sprite exposures")
    if first.shape != (128,128,4) or original.read_bytes() != (OUT / "01.png").read_bytes():
        raise ValueError("Full inhale must be a byte-identical copy of D")
    # Independent reconstruction: delete an array row and prepend transparent RGBA.
    reconstructed = np.vstack((np.zeros_like(first[:1]), np.delete(first, 38, axis=0)))
    checks["inhale_vs_D"] = mismatches(first, pixels(original))
    checks["exhale_vs_exact_reconstruction"] = mismatches(second, reconstructed)
    checks["exhale_top_vs_transparent"] = mismatches(second[:1], np.zeros_like(first[:1]))
    checks["exhale_y1_to_38_vs_inhale_y0_to_37"] = mismatches(second[1:39], first[:38])
    checks["below_cut_y39_to_127"] = mismatches(second[39:], first[39:])
    advisor = HERE.parent / "protagonist_idle_45_breath_r3/advisor_row_delete/breath_B.png"
    checks["exhale_vs_advisor_B"] = mismatches(second, pixels(advisor))

    for name in ("breath_1x.gif", "breath_3x.gif", "room_native.gif"):
        with Image.open(OUT / name) as gif:
            if gif.n_frames != 2 or gif.info.get("loop") != 0:
                raise ValueError(f"Invalid cycle: {name}")
            for i, f in enumerate(ImageSequence.Iterator(gif)):
                if f.info["duration"] != (1200,1600)[i]:
                    raise ValueError(f"Incorrect playback timing: {name} frame {i+1}")
                if name.startswith("breath_"):
                    scale = 1 if name == "breath_1x.gif" else 3
                    expected = Image.new("RGB", (128,128), "#555b5e")
                    im = Image.fromarray((first,second)[i])
                    expected.paste(im, mask=im.getchannel("A"))
                    rgb = np.repeat(np.repeat(np.asarray(expected), scale, axis=0), scale, axis=1)
                    checks[f"{name}_frame_{i+1}"] = mismatches(np.array(f.convert("RGB")), rgb)
    if any(checks.values()):
        raise ValueError(f"Unexpected pixels: {checks}")
    candidates = {y: mismatches(first[y], first[y-1]) for y in range(34,53)}
    if [y for y,n in candidates.items() if n == min(candidates.values())] != [38]:
        raise ValueError("Selected row is not the unique minimum")
    report = dict(result="PASS", first_png_byte_identical=True, row=38, durations_ms=[1200,1600],
                  row_difference_counts=candidates, unexpected_pixel_counts=checks)
    (HERE / "verification.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    audit()
