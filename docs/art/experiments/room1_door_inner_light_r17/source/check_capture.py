"""Read-only render comparison for the recorded 1280x720 game camera."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

base = Path(__file__).resolve().parents[1]
evidence = base / "evidence"
# Fixed-camera door bay, with a little neutral wall around it.
roi = (535, 90, 747, 442)


def pixels(name):
    image = Image.open(evidence / f"{name}.png").convert("RGB")
    assert image.size == (1280, 720)
    return np.asarray(image.crop(roi), dtype=np.int16)


records = []
for fraction in (0, 20, 50, 100):
    on = pixels(f"fixed_game_{fraction}")
    off = pixels(f"emitter_off_game_{fraction}")
    changed = np.max(np.abs(on - off), axis=2) > 3
    y, x = np.where(changed)
    bbox = [int(x.min() + roi[0]), int(y.min() + roi[1]),
            int(x.max() + roi[0]), int(y.max() + roi[1])] if len(x) else None
    # Covered right jamb must not light before the moving leaf clears it.
    right_changes = int(changed[:, 733 - roi[0]:].sum())
    if fraction in (0, 20, 50):
        assert right_changes == 0, (fraction, right_changes)
    if fraction == 0:
        assert not changed.any()
    else:
        assert changed.any(), fraction
    if fraction == 20:
        assert bbox[2] < 600, bbox
    if fraction == 50:
        assert bbox[2] < 665, bbox
    records.append({"fraction_percent": fraction, "changed_pixels": int(changed.sum()),
                    "emitting_bbox_inclusive": bbox, "right_jamb_changes": right_changes})

assert np.array_equal(pixels("covered_leaf_forced_power"), pixels("emitter_off_game_0")), \
    "Covered leaf leaked light even with forced test power."
assert records[1]["changed_pixels"] < records[2]["changed_pixels"] < records[3]["changed_pixels"]
report = {"result": "PASS", "method": "same-camera emitter on/off image difference; RGB delta >3",
          "resolution": [1280, 720], "door_roi_xyxy_exclusive": roi,
          "closed_forced_power_no_visible_leak": True, "states": records,
          "scope": "Recorded front game camera only; oblique views reviewed separately."}
(base / "source" / "render_occlusion_check.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False))
