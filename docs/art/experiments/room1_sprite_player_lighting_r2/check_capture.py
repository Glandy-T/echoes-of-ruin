"""Check actual Room 1 screenshots for the paper-character lighting review."""
from pathlib import Path
import json
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"

def image(name: str) -> np.ndarray:
    return np.asarray(Image.open(EVIDENCE / f"{name}.png").convert("RGB"), dtype=np.float32)

names = ["open_light_on", "open_light_off", "open_light_restored", "walk_light_on"]
frames = {name: image(name) for name in names}
assert all(frame.shape == (720, 1280, 3) for frame in frames.values())
# The fixed review view keeps the character within this crop. It includes enough
# background to prevent one bright pixel from falsely passing the comparison.
roi = {name: frame[210:475, 580:700] for name, frame in frames.items()}
means = {name: np.mean(value, axis=(0, 1)).round(2).tolist() for name, value in roi.items()}
lum = {name: float(np.mean(value)) for name, value in roi.items()}
assert lum["open_light_on"] > lum["open_light_off"] + 12.0, lum
assert lum["open_light_restored"] > lum["open_light_off"] + 12.0, lum
assert lum["walk_light_on"] > lum["open_light_off"] + 12.0, lum
readback = json.loads((EVIDENCE / "readback.json").read_text(encoding="utf8"))
assert readback["strip_on"] == 1.0
assert readback["texture_filter"] == 0
assert readback["walk"]["walking"] and readback["walk"]["distance_m"] > 0.2
result = {"roi": "x=580..699,y=210..474", "mean_rgb": means, "mean_luminance": lum, "pass": True}
(HERE / "capture_quality.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
print(json.dumps(result, ensure_ascii=False, indent=2))
