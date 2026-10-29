"""Independent saved-file geometry and route readback for stair blockout v2."""
from pathlib import Path
from collections import defaultdict, deque
import hashlib
import json
import bpy

ROOT = Path(__file__).resolve().parents[5]
OUT = ROOT / "docs/art/experiments/cryo_building_stairs_v2"
DATA = json.loads((ROOT / "docs/cad/cryo_standard_floor/v3_trim/floor_layout.json").read_text(encoding="utf-8"))
P = DATA["parameters"]
CX, CY = P["CenterX"], P["CenterY"]
LEVELS = [("B4", -4), ("B3", -3), ("B2", -2), ("B1", -1)] + [(f"{i}F", i-1) for i in range(1,17)]
STOREY = 3.8
bpy.ops.wm.open_mainfile(filepath=str(OUT / "cryo_building_stairs_v2.blend"))


def bounds(obj):
    pts = [obj.matrix_world @ __import__('mathutils').Vector(p) for p in obj.bound_box]
    return (min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts),
            max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))


def inside(obj, x, y, z):
    a,b,c,d,e,f = bounds(obj)
    return a+1e-4 < x < d-1e-4 and b+1e-4 < y < e-1e-4 and c+1e-4 < z < f-1e-4


floor = [o for o in bpy.data.objects if o.get("kind") == "frozen_floor_cell_clipped_for_stairs"]
walls = [o for o in bpy.data.objects if o.get("frozen_wall_id")]
shafts = DATA["stairs"]
errors = []
for label, index in LEVELS:
    local_floor = [o for o in floor if o.get("level") == label]
    for stair in shafts:
        # A sample at the middle of the first flight must be open through the
        # original slab and unobstructed by any frozen wall. The landing is
        # deliberately outside this sample position.
        if stair["side"] == "West":
            x, y = stair["x1"]+3.5, stair["y1"]+1.1
        elif stair["side"] == "East":
            x, y = stair["x2"]-3.5, stair["y1"]+1.1
        elif stair["side"] == "North":
            x, y = stair["x1"]+1.1, stair["y1"]+3.5
        else:
            x, y = stair["x1"]+1.1, stair["y2"]-3.5
        p = (x-CX, y-CY, index*STOREY-.05)
        if any(inside(o, *p) for o in local_floor):
            errors.append(f"{label}/{stair['id']}: slab covers shaft")
        wall_sample = (p[0],p[1],index*STOREY+1.0)
        if any(o.get("level") == label and inside(o, *wall_sample) for o in walls):
            errors.append(f"{label}/{stair['id']}: frozen wall obstructs first flight")
        for segment in ["EntryLanding"] + ([] if label == "16F" else ["TurnLanding", "SlopeA", "SlopeB"]):
            if bpy.data.objects.get(f"{label}_{stair['id']}_{segment}") is None:
                errors.append(f"{label}/{stair['id']}: missing {segment}")
        if label != "16F":
            for segment in ("SlopeA", "SlopeB"):
                slope = bpy.data.objects[f"{label}_{stair['id']}_{segment}"]
                if slope.data.polygons[0].normal.z < .1:
                    errors.append(f"{label}/{stair['id']}: {segment} top normal does not face upward")
        if bpy.data.objects.get(f"{label}_{stair['id']}_StairCore"):
            errors.append(f"{label}/{stair['id']}: old solid core remains")

doors = [o for o in bpy.data.objects if o.get("locked_placeholder")]
expected_doors = len(LEVELS)*len(DATA["doors"])-2
if len(doors) != expected_doors:
    errors.append(f"locked placeholders {len(doors)} != {expected_doors}")
for number in ("D001", "D077"):
    if any(o.get("level") == "4F" and o.get("door_id") == number for o in doors):
        errors.append(f"4F/{number} should be an open route gap")

graph = defaultdict(set)
for edge in DATA["routes"]["edges"]:
    if edge["kind"] in ("daily", "emergency"):
        graph[edge["a"]].add(edge["b"])
        if not edge.get("directed", False):
            graph[edge["b"]].add(edge["a"])
visited = {"SW-01"}
queue = deque(visited)
while queue:
    for nxt in graph[queue.popleft()]:
        if nxt not in visited:
            visited.add(nxt)
            queue.append(nxt)
if "West_StairLanding" not in visited:
    errors.append("frozen route graph does not connect SW-01 to West stair")

result = {
    "schema": "cryo_building_stairs_v2_reopen_validation",
    "result": "PASS" if not errors else "FAIL",
    "errors": errors,
    "level_count": len(LEVELS),
    "four_open_shafts_checked_each_level": 4*len(LEVELS),
    "stair_transitions": sum(1 for o in bpy.data.objects if o.get("segment") == "slope_a"),
    "locked_door_placeholders": len(doors),
    "f4_sw01_to_west_stair_route_in_frozen_graph": "West_StairLanding" in visited,
    "source_v1_hash_matches_recorded": hashlib.sha256((ROOT / "docs/art/experiments/cryo_building_blockout_v1/cryo_building_blockout_v1.blend").read_bytes()).hexdigest() == bpy.data.collections["CRYO_BUILDING_STAIRS_V2"].get("v1_source_sha256"),
    "godot_runtime_walk_test": "NOT_RUN",
    "1f_external_exit": "TBD",
}
if not result["source_v1_hash_matches_recorded"]:
    result["errors"].append("v1 source hash changed since v2 build")
    result["result"] = "FAIL"
(OUT / "reopen_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False), flush=True)
if errors:
    raise SystemExit(1)
