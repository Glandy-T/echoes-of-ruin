"""Read-only same-camera halo and visible-source checks; no art is painted."""
import json
from pathlib import Path
import numpy as np
from PIL import Image

base = Path(__file__).resolve().parents[1]
evidence = base / "evidence"

def pixels(name):
    return np.asarray(Image.open(evidence / f"{name}.png").convert("RGB"), dtype=np.int16)

checks = []
for fraction in (0, 20, 50, 100):
    core = pixels(f"core_game_{fraction}")
    soft = pixels(f"soft_game_{fraction}")
    source = pixels(f"soft_game_{fraction}_source")
    assert np.array_equal(source, pixels(f"core_game_{fraction}_source"))
    changed = np.max(np.abs(soft-core), axis=2) > 2
    y, x = np.where(changed)
    bbox = [int(x.min()), int(y.min()), int(x.max()), int(y.max())] if len(x) else None
    mask = np.max(source, axis=2) > 2
    my, mx = np.where(mask)
    if fraction == 0:
        assert not mask.any() and not changed.any(), "Closed door retained glow."
    else:
        assert mask.any() and changed.any()
        # Halo must grow beyond the razor-thin source, yet stay local to it.
        sx, sy = core.shape[1]/source.shape[1], core.shape[0]/source.shape[0]
        source_bbox = [int(mx.min()*sx), int(my.min()*sy), int(mx.max()*sx), int(my.max()*sy)]
        assert bbox[0] >= source_bbox[0]-24 and bbox[2] <= source_bbox[2]+24
        assert bbox[1] >= source_bbox[1]-24 and bbox[3] <= source_bbox[3]+24
        assert int(changed.sum()) > int(mask.sum())
    if fraction in (20, 50):
        assert not mask[:, int(733*source.shape[1]/core.shape[1]):].any(), "Covered right source lit."
        assert not changed[:, 733:747].any(), "Distant covered right jamb gained halo."
    checks.append({"fraction_percent": fraction, "halo_changed_pixels": int(changed.sum()),
                   "visible_source_pixels": int(mask.sum()), "halo_bbox_inclusive": bbox})
room_checks = []
for before in sorted(evidence.glob("core_room_*.png")):
    if before.stem.endswith("_source"):
        continue
    after = before.stem.replace("core_", "soft_", 1)
    delta = np.max(np.abs(pixels(after)-pixels(before.stem)), axis=2) > 2
    mask = np.max(pixels(after+"_source"), axis=2) > 2
    y, x = np.where(mask)
    allowed = np.zeros(delta.shape, dtype=bool)
    if x.size:
        allowed[max(0,int(y.min())-24):int(y.max())+25,
                max(0,int(x.min())-24):int(x.max())+25] = True
    assert not (delta & ~allowed).any(), before.stem
    room_checks.append({"file":after+".png", "changes_outside_door_halo":0,
                        "visible_source_pixels":int(mask.sum()), "changed_pixels":int(delta.sum())})
report = {"result": "PASS", "closed_no_source_or_halo": True,
          "covered_right_source_and_jamb_clean": True, "halo_toggle_preserves_source": True,
          "states": checks, "six_room_camera_checks":room_checks,
          "method": "RGB delta >2; same-camera core vs halo and saved visible-source masks",
          "limit": "Postprocess feather can cross the immediate silhouette by a few pixels; not volumetric fog or GI."}
(base / "source" / "render_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
