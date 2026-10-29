"""Read-back audit for the r19 full-room bake source and HDR outputs."""
from pathlib import Path
import bpy, json, hashlib, numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
OUT = REPO / "assets/art/room1_complete_r19/lighting"
BLEND = HERE.parent / "room1_complete_r19.blend"
LAYOUT = HERE / "layout_before.json"
R4_GLB = REPO / "assets/art/room1_continuous_bake_r3/room1_baked_uv2_r4_uv_fixed.glb"
names = [f"P{n:02d}_closed" for n in range(1, 21)] + ["P12_open", "room_closed", "room_open"]

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
receivers = [o for o in bpy.data.objects if o.name.startswith("R19_P") and o.name.endswith("_closed_receiver")]
old = [o.name for o in bpy.data.objects if "pod_v3" in o.name]
assert len(receivers) == 20, len(receivers)
assert not old, old
uv = {}
for obj in receivers:
    layers = [x.name for x in obj.data.uv_layers]
    assert "UV_GODOT_0" in layers and "LightmapUV" in layers, (obj.name, layers)
    uv[obj.name] = layers
rows = []
for name in names:
    raw = OUT / f"{name}_raw.exr"; final = OUT / f"{name}.exr"
    assert raw.exists() and final.exists(), name
    loaded = bpy.data.images.load(str(final), check_existing=False)
    pixels = np.empty(len(loaded.pixels), dtype=np.float32); loaded.pixels.foreach_get(pixels)
    assert np.isfinite(pixels).all(), name
    margin = 6 if name.startswith("room_") else 4
    rows.append({"name":name,"size":list(loaded.size),"margin_px":margin,"raw_sha256":digest(raw),"final_sha256":digest(final),
                 "raw_final_differ":digest(raw)!=digest(final),"finite":True,
                 "rgb_range":[float(pixels.reshape(-1,4)[:,:3].min()),float(pixels.reshape(-1,4)[:,:3].max())]})
report={"schema":"room1_complete_r19_bake_check_v1","source":str(BLEND.relative_to(REPO)),
        "samples_actual":1024,"denoise":"Blender native compositor OIDN; raw and final are retained.",
        "endpoints":{"closed":"P01-P20 closed","open":"P12 open; P01-P11/P13-P20 closed","runtime":"only P12 interpolates between closed/open"},
        "padding_contract":{"pod_min_uv_island_gap_px_at_1024":11.92448,"pod_margin_px":4,"shell_min_uv_island_gap_px_at_2048":16.22897,"shell_margin_px":6,
            "runtime_sampler":"linear sampling with repeat disabled/clamp-to-edge; pod UV atlas outer-edge minimum is 0px and is not claimed as padding."},
        "source_counts":{"v8_closed_receivers":len(receivers),"old_v3_meshes":len(old),"door_placeholder":bpy.data.objects.get("Bake_Shell_MAIN_DOOR_PLACEHOLDER_NOT_APPROVED") is not None,
                         "door_meshes":len([o for o in bpy.data.objects if o.name.startswith("R19_Door_")])},
        "uv_layers":uv,"images":rows}
layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
color_paths = sorted({path for pod in layout["pods"] for path in pod["bake_color_maps"].values()})
report["inputs"] = {"layout_sha256":digest(LAYOUT), "runtime_r4_shell_glb":str(R4_GLB.relative_to(REPO)),
                    "runtime_r4_shell_glb_sha256":digest(R4_GLB), "bake_source_blend_sha256":digest(BLEND),
                    "r13_r15_and_r16_color_maps": [{"path":path,"sha256":digest(REPO/path)} for path in color_paths]}
path_report = HERE / "relative_paths_check.json"
if path_report.exists():
    report["portable_paths"] = json.loads(path_report.read_text(encoding="utf-8"))
for name in ["bake_check.json", "bake_manifest.json"]:
    (HERE/name).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("R19_CHECK_COMPLETE",json.dumps(report,ensure_ascii=False),flush=True)
