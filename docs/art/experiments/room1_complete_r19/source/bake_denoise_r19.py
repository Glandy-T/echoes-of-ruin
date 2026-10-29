"""Apply the verified Blender compositor OIDN path to existing r19 raw EXRs."""
from pathlib import Path
import bpy, runpy

HERE = Path(__file__).resolve().parent
scope = runpy.run_path(str(HERE / "bake_room1_complete_r19.py"))
denoise = scope["denoise_linear_hdr"]
out = scope["OUT"]
names = [f"P{number:02d}_closed" for number in range(1, 21)] + ["room_closed", "room_open", "P12_open"]
for name in names:
    raw = out / f"{name}_raw.exr"; final = out / f"{name}.exr"
    assert raw.exists(), raw
    print("R19_DENOISE", name, flush=True)
    denoise(raw, final, name)
print("R19_DENOISE_COMPLETE", len(names), flush=True)
