"""Read back the exported master and verify the top-only scope."""
from pathlib import Path
from PIL import Image
import json
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
EXP = HERE.parent
old = Image.open(HERE / "header_guide.png").convert("RGBA")
new = Image.open(ROOT / "assets/art/room1_integrated_door_pixellab_v7/door_front.png").convert("RGBA")
readback = Image.open(HERE / "aseprite_readback.png").convert("RGBA")
mask = Image.open(HERE / "header_mask.png").convert("L")
changed = [(x, y) for y in range(184) for x in range(112) if old.getpixel((x,y)) != new.getpixel((x,y))]
outside = [(x,y) for x,y in changed if mask.getpixel((x,y)) == 0]
report = {"changed_pixels": len(changed), "outside_header_mask": len(outside),
          "aseprite_pixel_exact": new.tobytes() == readback.tobytes(), "size": list(new.size)}
(EXP / "header_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
for name, im in (("top_before", old), ("top_after", new)):
    im.crop((0,0,112,40)).resize((672,240), Image.Resampling.NEAREST).save(EXP / "evidence" / (name + ".png"))
new.resize((448,736), Image.Resampling.NEAREST).save(EXP / "evidence/assembled_header_4x.png")
print(json.dumps(report))
assert not outside and report["aseprite_pixel_exact"]
