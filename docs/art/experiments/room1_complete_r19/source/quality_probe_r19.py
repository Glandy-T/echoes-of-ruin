"""Higher-sample shell-only convergence probe, kept outside runtime assets."""
from pathlib import Path
import json, os, runpy

here = Path(__file__).resolve().parent
scope = runpy.run_path(str(here / "bake_room1_complete_r19.py"))
shared = scope["bake_receiver"].__globals__
probe = here / "quality_probe_1024"
probe.mkdir(parents=True, exist_ok=True)
shared["OUT"] = probe
os.environ["R19_SAMPLES"] = "1024"
os.environ["R19_REBAKE"] = "1"
rows = []
for endpoint in ("closed", "open"):
    receivers, shell, scene, uv_hash, mapping = scope["build_endpoint"](endpoint, save_blend=False)
    row = scope["bake_receiver"](shell, "room_"+endpoint, 2048)
    row.update({"samples":1024,"shell_uv2_hash":uv_hash,"runtime_assets_modified":False})
    rows.append(row)
(here / "quality_probe_1024.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
print("R19_QUALITY_PROBE_COMPLETE", flush=True)
