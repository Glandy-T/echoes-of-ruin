"""Add four open, continuous stair shafts to the v1 spatial blockout.

The frozen CAD JSON supplies only plan coordinates. Stair geometry and level
connections are independent, provisional Blender modules, not CAD imports.
Run in a new background Blender process; the source v1 blend is never saved.
"""
from pathlib import Path
import hashlib
import json
import math
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[5]
OUT = ROOT / "docs/art/experiments/cryo_building_stairs_v2"
V1 = ROOT / "docs/art/experiments/cryo_building_blockout_v1/cryo_building_blockout_v1.blend"
DATA_PATH = ROOT / "docs/cad/cryo_standard_floor/v3_trim/floor_layout.json"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "evidence").mkdir(exist_ok=True)

DATA = json.loads(DATA_PATH.read_text(encoding="utf-8"))
P = DATA["parameters"]
STOREY = 3.8
SLAB = 0.10
CX, CY = P["CenterX"], P["CenterY"]
STAIRS = DATA["stairs"]
LEVELS = [("B4", -4), ("B3", -3), ("B2", -2), ("B1", -1)] + [(f"{i}F", i - 1) for i in range(1, 17)]


def collection(name, parent):
    result = bpy.data.collections.new(name)
    parent.children.link(result)
    return result


def material(name, color):
    result = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    result.diffuse_color = color
    return result


def box(name, rect, bottom, top, parent, color, properties=None):
    x1, y1, x2, y2 = rect
    x1, x2, y1, y2 = x1-CX, x2-CX, y1-CY, y2-CY
    vertices = [(x1,y1,bottom), (x2,y1,bottom), (x2,y2,bottom), (x1,y2,bottom),
                (x1,y1,top), (x2,y1,top), (x2,y2,top), (x1,y2,top)]
    faces = [(0,3,2,1), (4,5,6,7), (0,1,5,4), (1,2,6,5),
             (2,3,7,6), (3,0,4,7)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    parent.objects.link(obj)
    obj.data.materials.append(color)
    for key, value in (properties or {}).items():
        obj[key] = value
    return obj


def point(stair, u, v):
    """Plan-space stair coordinates; u runs from door-side landing inward."""
    side = stair["side"]
    if side == "West":
        return (stair["x1"] + .2 + u, stair["y1"] + .2 + v)
    if side == "East":
        return (stair["x2"] - .2 - u, stair["y1"] + .2 + v)
    if side == "North":
        return (stair["x1"] + .2 + v, stair["y1"] + .2 + u)
    return (stair["x1"] + .2 + v, stair["y2"] - .2 - u)


def uv_rect(stair, u1, v1, u2, v2):
    a, b = point(stair, u1, v1), point(stair, u2, v2)
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))


def clip(rect, hole):
    """Return non-overlapping pieces of rect outside an axis-aligned hole."""
    x1, y1, x2, y2 = rect
    a, b, c, d = hole
    ix1, iy1, ix2, iy2 = max(x1, a), max(y1, b), min(x2, c), min(y2, d)
    if ix1 >= ix2 - 1e-5 or iy1 >= iy2 - 1e-5:
        return [rect]
    pieces = [(x1, y1, ix1, y2), (ix2, y1, x2, y2),
              (ix1, y1, ix2, iy1), (ix1, iy2, ix2, y2)]
    return [r for r in pieces if r[2]-r[0] > .005 and r[3]-r[1] > .005]


def ramp(name, stair, u1, u2, v1, v2, z1, z2, parent, color, tags):
    """Continuous collision-friendly slope beneath the visible tread strips."""
    uv = [(u1, v1), (u2, v1), (u2, v2), (u1, v2)]
    top = [(*point(stair, u, v), z1 if u == u1 else z2) for u, v in uv]
    verts = [(x-CX, y-CY, z) for x, y, z in top]
    verts += [(x, y, z-.07) for x, y, z in verts]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    if stair["side"] in ("East", "North"):
        faces = [tuple(reversed(face)) for face in faces]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    parent.objects.link(obj)
    obj.data.materials.append(color)
    for key, value in tags.items():
        obj[key] = value
    return obj


def camera(name, at, target, scale, parent):
    data = bpy.data.cameras.new(name)
    data.type = 'ORTHO'
    data.ortho_scale = scale
    obj = bpy.data.objects.new(name, data)
    obj.location = at
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z', 'Y').to_euler()
    parent.objects.link(obj)
    return obj


def render(path, cam):
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def build():
    bpy.ops.wm.open_mainfile(filepath=str(V1))
    root = bpy.data.collections["CRYO_BUILDING_BLOCKOUT_V1"]
    root.name = "CRYO_BUILDING_STAIRS_V2"
    stair_group = collection("FOUR_STAIRS__20_LANDINGS_19_TRANSITIONS", root)
    route_group = collection("F4_ROOM1_TO_WEST_STAIR__PLAN_REFERENCE", root)
    cam_group = collection("CAMERAS_V2", root)
    slab_mat = bpy.data.materials["M_Blockout_Slab"]
    stair_mat = material("M_Stair_Walkable_Grey", (.53, .59, .61, 1))
    tread_mat = material("M_Stair_Tread_Edge", (.28, .35, .38, 1))
    route_mat = material("M_F4_Authorized_Route", (.18, .65, .55, 1))
    door_mat = material("M_Access_Locked_Door_Placeholder", (.09, .13, .16, 1))

    # All v1 stair cores were solid visual placeholders. The frozen wall plan
    # around them remains intact; only these four placeholder boxes disappear.
    for label, _ in LEVELS:
        for stair in STAIRS:
            bpy.data.objects.remove(bpy.data.objects[f"{label}_{stair['id']}_StairCore"], do_unlink=True)

    # The three plan floor cells beneath stair cores must have real openings on
    # every level. The v1 Blender file has independently editable floor cells
    # on each level, so clip each level directly.
    holes = [uv_rect(s, 0, 0, 6.9, 3.8) for s in STAIRS]
    floor_objects = [o for o in list(bpy.data.objects) if o.get("kind") == "frozen_floor_cell"]
    cut_pieces = 0
    for old in floor_objects:
        cx, cy = old.location.x + CX, old.location.y + CY
        sx, sy = old.dimensions.x, old.dimensions.y
        pieces = [(cx-sx/2, cy-sy/2, cx+sx/2, cy+sy/2)]
        for hole in holes:
            pieces = [q for piece in pieces for q in clip(piece, hole)]
        props = {"kind": "frozen_floor_cell_clipped_for_stairs", "source": "floor_layout.json.floor_cells", "level": old.get("level", "")}
        stem = old.name
        ztop = old.location.z + old.dimensions.z/2
        parent = old.users_collection[0]
        bpy.data.objects.remove(old, do_unlink=True)
        for index, piece in enumerate(pieces, 1):
            box(f"{stem}_V2_Cut_{index:02d}", piece, ztop-SLAB, ztop, parent, slab_mat, props)
            cut_pieces += 1
    print(f"V2: clipped {len(floor_objects)} source floor cells to {cut_pieces} pieces", flush=True)

    # Landings are added to every level, stair flights to each of the 19
    # adjacent level pairs. Nothing crosses a level without a physical slope.
    for label, index in LEVELS:
        z = index * STOREY
        floor_col = collection(f"STAIRS_{label}", stair_group)
        for stair in STAIRS:
            sid = stair["id"]
            tags = {"stair_id": sid, "level": label, "walkable": True,
                    "geometry_status": "PROVISIONAL_GAME_GREYBOX"}
            box(f"{label}_{sid}_EntryLanding", uv_rect(stair, 0, 0, 1.8, 3.8),
                z-.10, z, floor_col, stair_mat, dict(tags, segment="landing"))
            # The existing frozen stair-wall opening is 0.2m thick. A small
            # threshold physically joins its corridor floor to this landing.
            entry_doors = [d for d in DATA["doors"]
                           if d["kind"] == "stair" and d.get("tag", "").startswith(sid)]
            if stair["side"] in ("West", "East"):
                for n, door in enumerate(entry_doors):
                    box(f"{label}_{sid}_Threshold_{n+1}", (door["x"]-.9, door["y"]-.11, door["x"]+.9, door["y"]+.11),
                        z-.10, z, floor_col, stair_mat, dict(tags, segment="door_threshold", door_id=door["id"]))
            else:
                door = entry_doors[0]
                box(f"{label}_{sid}_Threshold", (door["x"]-.9, door["y"]-.11, door["x"]+.9, door["y"]+.11),
                    z-.10, z, floor_col, stair_mat, dict(tags, segment="door_threshold", door_id=door["id"]))
            if label == "16F":
                continue
            box(f"{label}_{sid}_TurnLanding", uv_rect(stair, 5.1, 0, 6.9, 3.8),
                z+STOREY/2-.10, z+STOREY/2, floor_col, stair_mat,
                dict(tags, segment="half_level_turn"))
            # Flight A climbs inward. Flight B climbs back to the same end,
            # where the next storey's entry landing is already present.
            ramp(f"{label}_{sid}_SlopeA", stair, 1.8, 5.1, 0, 1.8,
                 z, z+STOREY/2, floor_col, stair_mat, dict(tags, segment="slope_a"))
            ramp(f"{label}_{sid}_SlopeB", stair, 1.8, 5.1, 2.0, 3.8,
                 z+STOREY, z+STOREY/2, floor_col, stair_mat, dict(tags, segment="slope_b"))
            # 11 CAD-sized 0.3m visual treads per flight; the 12th rise is
            # absorbed at the half/full landing. The slopes stay continuous.
            for step in range(11):
                u1 = 1.8 + step*.3
                u2 = u1 + .3
                h_a = z + (step+1)*(STOREY/2)/12
                h_b = z + STOREY - step*(STOREY/2)/12
                box(f"{label}_{sid}_TreadA_{step+1:02d}", uv_rect(stair, u1, 0, u2, 1.8),
                    h_a-.035, h_a, floor_col, tread_mat, dict(tags, segment="tread_a"))
                box(f"{label}_{sid}_TreadB_{step+1:02d}", uv_rect(stair, u1, 2.0, u2, 3.8),
                    h_b-.035, h_b, floor_col, tread_mat, dict(tags, segment="tread_b"))
        print(f"V2: completed {label} stair modules", flush=True)

    # V1 preserves the frozen door gaps but has no actual door leaves. Seal
    # every gap except 4F Room 1 and its SW-to-West emergency entry; chip
    # permissions are represented by placeholder geometry, not game logic.
    open_4f_doors = {"D001", "D077"}
    for label, index in LEVELS:
        z = index*STOREY
        parent = bpy.data.collections[label]
        for door in DATA["doors"]:
            if label == "4F" and door["id"] in open_4f_doors:
                continue
            half = door["width"]/2
            if door["orientation"] == "H":
                rect = (door["x"]-half, door["y"]-.035, door["x"]+half, door["y"]+.035)
            else:
                rect = (door["x"]-.035, door["y"]-half, door["x"]+.035, door["y"]+half)
            box(f"{label}_{door['id']}_LockedDoor_Placeholder", rect, z, z+2.4,
                parent, door_mat, {"door_id": door["id"], "door_kind": door["kind"],
                                   "level": label, "locked_placeholder": True,
                                   "final_design": False, "chip_logic_implemented": False})

    # Route markers come from frozen CAD route nodes and edges. They are
    # evidence only, not new corridor geometry or gameplay permissions.
    nodes = DATA["routes"]["nodes"]
    route = ["SW-01", "SW_C0_0", "SW_C0_Outer", "SW_StairApproach",
             "SW_StairLandingCorner", "West_StairLanding"]
    for i, name in enumerate(route):
        n = nodes[name]
        box(f"Route_{i:02d}_{name}", (n["x"]-.18, n["y"]-.18, n["x"]+.18, n["y"]+.18),
            3*STOREY+.02, 3*STOREY+.05, route_group, route_mat,
            {"route_node": name, "reference_only": True})

    root["status"] = "V2_FOUR_STAIRS_GREYBOX__NOT_FINAL_ART_OR_GAMEPLAY"
    root["v1_source_sha256"] = hashlib.sha256(V1.read_bytes()).hexdigest()
    root["frozen_json_sha256"] = hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()
    root["stair_count"] = 4
    root["stair_level_count"] = 20
    root["stair_transition_count"] = 19
    root["f4_hero_route"] = route
    root["1f_external_exit"] = "TBD__NOT_PLACED"
    root["door_permissions"] = "TBD__VISUAL_FACES_ONLY"

    cams = {
        "four_stairs": camera("CAM_V2_FourStairs_4F", (-15, -60, 43), (0, 0, 13), 185, cam_group),
        "west_section": camera("CAM_V2_WestStair_Stack", (-105, -85, 31), (-92, 0, 23), 125, cam_group),
        "f4_route": camera("CAM_V2_F4_Route", (-110, -45, 59), (-70, -17, 12), 95, cam_group),
    }
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x = 1600
    sc.render.resolution_y = 900
    sc.render.resolution_percentage = 100
    sc.display.shading.color_type = 'MATERIAL'
    sc.display.shading.show_shadows = True
    sc.display.shading.show_cavity = True
    sc.display.shading.cavity_type = 'WORLD'
    below = bpy.data.collections["UNDERGROUND_B1_B4__HIDEABLE"]
    roof = bpy.data.collections["ROOF__PROVISIONAL"]
    machine = bpy.data.collections["MACHINE_SPINE__INACCESSIBLE_PLACEHOLDER"]
    below.hide_render = True
    roof.hide_render = True
    machine.hide_render = True
    # The first view isolates the frozen 4F plan and its four stair positions.
    for label, _ in LEVELS:
        bpy.data.collections[label].hide_render = label != "4F"
        bpy.data.collections[f"STAIRS_{label}"].hide_render = label != "4F"
    render(OUT / "evidence/four_stairs_4f_v2.png", cams["four_stairs"])
    # Vertical stack: leave west staircase visible and reveal every landing.
    for label, _ in LEVELS:
        bpy.data.collections[label].hide_render = True
        bpy.data.collections[f"STAIRS_{label}"].hide_render = False
    route_group.hide_render = True
    render(OUT / "evidence/west_stair_stack_v2.png", cams["west_section"])
    # 4F route reuses the same frozen corridor and D001 room anchor.
    for label, _ in LEVELS:
        bpy.data.collections[label].hide_render = label != "4F"
        bpy.data.collections[f"STAIRS_{label}"].hide_render = label != "4F"
    route_group.hide_render = False
    render(OUT / "evidence/f4_room1_to_west_stair_v2.png", cams["f4_route"])
    for label, _ in LEVELS:
        bpy.data.collections[label].hide_render = False
        bpy.data.collections[f"STAIRS_{label}"].hide_render = False
    route_group.hide_render = True
    roof.hide_render = False
    machine.hide_render = False
    below.hide_render = True
    sc.camera = cams["f4_route"]

    validation = {
        "schema": "cryo_building_stairs_v2",
        "status": "BUILT_REOPEN_CHECK_PENDING",
        "source_v1": str(V1.relative_to(ROOT)).replace('\\', '/'),
        "source_v1_sha256": root["v1_source_sha256"],
        "frozen_layout": str(DATA_PATH.relative_to(ROOT)).replace('\\', '/'),
        "frozen_sha256": root["frozen_json_sha256"],
        "cad_geometry_imported": False,
        "levels": len(LEVELS),
        "stairs_per_level": len(STAIRS),
        "stair_transitions_per_shaft": len(LEVELS)-1,
        "cut_floor_pieces": cut_pieces,
        "room1_f4_route_nodes": route,
        "room1_anchor_provisional": "SW-01",
        "door_status": "placeholder only; permissions not implemented",
        "locked_door_placeholders": len(LEVELS)*len(DATA["doors"])-len(open_4f_doors),
        "open_4f_door_ids": sorted(open_4f_doors),
        "1f_exit_status": "not located in frozen plan; route ends at 1F west stair landing",
        "limitations": ["Stair shape and level height are provisional", "No final railings or door animation",
                        "No Godot navigation or collision runtime test", "No 1F exterior exit connection",
                        "Other sectors/floors must remain permission locked in game"],
    }
    (OUT / "validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "cryo_building_stairs_v2.blend"))


if __name__ == "__main__":
    build()
