"""Run with Blender in background from the repository root."""
import bpy
import numpy as np
from pathlib import Path
import json

exp = Path.cwd() / "docs/art/experiments"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(exp / "protagonist_walk_r5_hem_fix/walk.glb"))
body = max((o for o in bpy.context.scene.objects if o.type == "MESH"), key=lambda o: len(o.data.polygons))
used = sorted({i for p in body.data.polygons for i in p.vertices})
rest = np.array([body.matrix_world @ v.co for v in body.data.vertices])
height = float(np.ptp(rest[used, 2]))
scale = 1.65 / height
heels = {}
for side in ("L","R"):
    foot = [i for i in used if rest[i, 2] < .05 and (rest[i, 1] > 0) == (side == "L")]
    back = [i for i in foot if rest[i, 0] <= min(rest[foot, 0]) + .015]
    heels[side] = [i for i in back if rest[i, 2] < min(rest[back, 2]) + .004]
trace = []
for f in range(57):
    bpy.context.scene.frame_set(f)
    mesh = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    row = {}
    for side, points in heels.items():
        xyz = np.array([mesh.matrix_world @ mesh.data.vertices[i].co for i in points])
        row[side] = {"forward": float(xyz[:, 0].mean()), "bottom": float(xyz[:, 2].min())}
    trace.append(row)
contacts = [(9,"R"), (26,"L"), (37,"R")]
contacts_x = [trace[f][s]["forward"] for f,s in contacts]
steps = np.diff(contacts_x) * scale
period = sum(steps) / 2.0
report = dict(source_fps=24, source_frames=[0,56], contacts=contacts, height_native=height,
              meters_per_unit=scale, steps_m=steps.tolist(), average_step_m=np.mean(steps),
              game_period_s=period, sprite_fps=8/period,
              sample_frames=np.linspace(9,37,8,endpoint=False).tolist(), heel_trace_native=trace)
(exp / "protagonist_walk_side_r1/gait.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("RESULT", steps, np.mean(steps), period, 8/period)
