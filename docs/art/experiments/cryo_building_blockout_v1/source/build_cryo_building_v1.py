"""Build Cryo Building Blockout v1 from frozen standard-floor coordinates.

This is intentionally an independent Blender blockout: it reads JSON dimensions,
rooms, walls, corridors and traffic nodes, but never imports or converts CAD.
"""
from pathlib import Path
import bpy
import json
import hashlib
import math
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[5]
OUT = ROOT / "docs/art/experiments/cryo_building_blockout_v1"
DATA_PATH = ROOT / "docs/cad/cryo_standard_floor/v3_trim/floor_layout.json"
BLEND_PATH = OUT / "cryo_building_blockout_v1.blend"
EVIDENCE = OUT / "evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)

with DATA_PATH.open(encoding="utf-8") as f:
    DATA = json.load(f)
P = DATA["parameters"]
ROOMS = DATA["rooms"]
WALLS = DATA["walls"]
CORRIDORS = DATA["corridors"]
ELEVATORS = DATA["elevator_nodes"]
STAIRS = DATA["stairs"]
FLOOR_CELLS = DATA["floor_cells"]
DOORS = DATA["doors"]
D001 = next(d for d in DOORS if d["id"] == "D001")

# Frozen-plan inputs, while all vertical and exterior treatment remains provisional.
LEVELS = [("B4", -4), ("B3", -3), ("B2", -2), ("B1", -1)] + [(f"{i}F", i - 1) for i in range(1, 17)]
STOREY = 3.8
WALL_HEIGHT = 3.4
SLAB = 0.10
CENTER_X = P["CenterX"]
CENTER_Y = P["CenterY"]
MAIN_W = P["MainWidth"]
MAIN_D = P["MainDepth"]
FLOOR_SOUTH = P["FloorSouth"]
FLOOR_NORTH = P["FloorNorth"]


def local_xy(x, y):
    return x - CENTER_X, y - CENTER_Y


def get_collection(name, parent=None):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        (parent.children if parent else bpy.context.scene.collection.children).link(col)
    return col


def mat(name, rgba):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = rgba
    return m


MATS = {}


def make_box(name, x1, y1, x2, y2, z0, z1, collection, material, tags=None):
    """Independent editable rectangular low-poly module in Blender coordinates."""
    x1, y1 = local_xy(x1, y1)
    x2, y2 = local_xy(x2, y2)
    bpy.ops.mesh.primitive_cube_add(location=((x1+x2)/2, (y1+y2)/2, (z0+z1)/2))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = (max(.02, x2-x1), max(.02, y2-y1), max(.02, z1-z0))
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)
    if tags:
        for key, value in tags.items():
            obj[key] = value
    return obj


def make_empty(name, x, y, z, collection, tags):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = 'CUBE'
    obj.empty_display_size = 1.0
    obj.location = (*local_xy(x, y), z)
    for key, value in tags.items():
        obj[key] = value
    collection.objects.link(obj)
    return obj


def look_at(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def new_camera(name, location, target, collection):
    cam = bpy.data.cameras.new(name)
    cam.type = 'ORTHO'
    cam.ortho_scale = 255
    obj = bpy.data.objects.new(name, cam)
    obj.location = location
    look_at(obj, target)
    collection.objects.link(obj)
    return obj


def set_hidden(collection, hidden):
    collection.hide_render = hidden
    collection.hide_viewport = hidden


def render_to(path, camera):
    sc = bpy.context.scene
    sc.camera = camera
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def build():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)

    root = get_collection("CRYO_BUILDING_BLOCKOUT_V1")
    above = get_collection("ABOVE_GROUND_16F", root)
    below = get_collection("UNDERGROUND_B1_B4__HIDEABLE", root)
    fixed = get_collection("FROZEN_PLAN_MODULES", root)
    anchors = get_collection("F4_ROOM1_SW01__PROVISIONAL_ANCHOR", root)
    cameras = get_collection("CAMERAS", root)
    cutaway = get_collection("SECTION_PRESENTATION_ONLY", root)

    MATS.update({
        "slab": mat("M_Blockout_Slab", (0.12, 0.17, 0.20, 1)),
        "wall": mat("M_Blockout_Wall", (0.35, 0.43, 0.46, 1)),
        "corridor": mat("M_Personnel_Route", (0.20, 0.34, 0.38, 1)),
        "core": mat("M_Machine_Core", (0.16, 0.18, 0.20, 1)),
        "door": mat("M_Closed_Door_Placeholder", (0.10, 0.13, 0.15, 1)),
        "anchor": mat("M_Room1_Anchor_Provisional", (0.75, 0.50, 0.08, 1)),
        "roof": mat("M_Roof_Provisional", (0.23, 0.28, 0.30, 1)),
    })

    # Project metadata and retained parameterization make later replacement safe.
    root["source_layout"] = str(DATA_PATH.relative_to(ROOT)).replace('\\', '/')
    root["cad_geometry_imported"] = False
    root["status"] = "SPATIAL_BLOCKOUT_ONLY__NOT_FINAL_ART_OR_PLAYABLE"
    root["storey_height_m_provisional"] = STOREY
    root["wall_height_m_provisional"] = WALL_HEIGHT
    root["standard_room_count_per_floor"] = len(ROOMS)
    root["floor_count"] = len(LEVELS)
    root["main_envelope_m"] = [MAIN_W, MAIN_D]

    # One independently-modelled frozen standard-floor template is instanced at every
    # level. This preserves the actual JSON wall/corridor/node positions while keeping
    # the building source editable and compact; it is not a copied CAD object.
    template = get_collection("STANDARD_FLOOR_TEMPLATE__JSON_DERIVED", fixed)
    for n, cell in enumerate(FLOOR_CELLS, 1):
        make_box(f"Template_FloorCell_{n:02d}", cell['x1'], cell['y1'], cell['x2'], cell['y2'], -SLAB, 0,
                 template, MATS["slab"], {"kind": "frozen_floor_cell", "source": "floor_layout.json.floor_cells", "provisional": True})
    for wall in WALLS:
        make_box(f"Template_{wall['id']}", wall['x1'], wall['y1'], wall['x2'], wall['y2'], 0, WALL_HEIGHT,
                 template, MATS["wall"], {"frozen_wall_id": wall['id'], "source": "floor_layout.json"})
    for corridor in CORRIDORS:
        make_box(f"Template_{corridor['id']}_Route", corridor['x1'], corridor['y1'], corridor['x2'], corridor['y2'], .005, .035,
                 template, MATS["corridor"], {"frozen_corridor_id": corridor['id'], "route": "personnel"})
    for node in ELEVATORS:
        make_box(f"Template_{node['id']}_TrafficCore", node['x1'], node['y1'], node['x2'], node['y2'], 0, WALL_HEIGHT,
                 template, MATS["core"], {"frozen_node_id": node['id'], "interior_omitted": True})
    for stair in STAIRS:
        make_box(f"Template_{stair['id']}_StairCore", stair['x1'], stair['y1'], stair['x2'], stair['y2'], 0, WALL_HEIGHT,
                 template, MATS["core"], {"frozen_stair_id": stair['id'], "interior_omitted": True})
    # Seal the non-hero door openings with simple placeholder faces. They do not
    # define final art, collision, access permission, or animation behavior.
    for door in DOORS:
        if door['id'] == 'D001':
            continue
        if door['orientation'] == 'H':
            make_box(f"Template_{door['id']}_ClosedDoor", door['x']-door['width']/2, door['y']-.035,
                     door['x']+door['width']/2, door['y']+.035, 0, 2.4, template, MATS["door"],
                     {"frozen_door_id": door['id'], "closed_placeholder": True, "gameplay_behavior": "TBD"})
        else:
            make_box(f"Template_{door['id']}_ClosedDoor", door['x']-.035, door['y']-door['width']/2,
                     door['x']+.035, door['y']+door['width']/2, 0, 2.4, template, MATS["door"],
                     {"frozen_door_id": door['id'], "closed_placeholder": True, "gameplay_behavior": "TBD"})

    for label, index in LEVELS:
        level_col = get_collection(label, above if index >= 0 else below)
        z = index * STOREY
        inst = bpy.data.objects.new(f"{label}_StandardFloor_JSON_Instance", None)
        inst.instance_type = 'COLLECTION'
        inst.instance_collection = template
        inst.location.z = z
        inst["level"] = label
        inst["source"] = "STANDARD_FLOOR_TEMPLATE__JSON_DERIVED"
        inst["room_count_nominal"] = len(ROOMS)
        inst["interiors_omitted"] = True
        level_col.objects.link(inst)
        make_empty(f"{label}_48_Room_LogicalEnvelopeMetadata", CENTER_X, CENTER_Y, z+1.7, level_col,
                   {"level": label, "room_count": len(ROOMS), "capacity_nominal": len(ROOMS)*20,
                    "interior_omitted": True, "source": "floor_layout.json.rooms"})
        if label != '4F':
            make_box(f"{label}_D001_ClosedDoor", D001['x']-D001['width']/2, D001['y']-.035,
                     D001['x']+D001['width']/2, D001['y']+.035, z, z+2.4, level_col, MATS["door"],
                     {"frozen_door_id": "D001", "closed_placeholder": True, "gameplay_behavior": "TBD"})

    # Simplified continuous machine spine / central transfer volume: placement derives from frozen parameters.
    bottom_z, top_z = -4*STOREY, 16*STOREY
    machine = get_collection("MACHINE_SPINE__INACCESSIBLE_PLACEHOLDER", root)
    make_box("Central_Machine_Spine_Provisional", P["CoreWest"], P["CoreSouth"], P["CoreEast"], P["CoreNorth"],
             bottom_z, top_z, machine, MATS["core"], {"inaccessible": True, "source": "frozen_parameter_core_bounds"})

    # Plain roof only: a temporary cap, not a facade or final roof design.
    roof = get_collection("ROOF__PROVISIONAL", root)
    make_box("Roof_Cap__Not_Final_Design", 0, FLOOR_SOUTH, MAIN_W, FLOOR_NORTH,
             16*STOREY, 16*STOREY+0.22, roof, MATS["roof"], {"provisional": True, "final_exterior": False})

    # 4F protagonist replacement space. Existing standardized walls make its D001 opening; anchor marks conversion point only.
    f4_z = 3*STOREY
    sw = next(r for r in ROOMS if r['id'] == 'SW-01')
    door = next(d for d in DATA['doors'] if d['id'] == 'D001')
    anchor = make_empty("F4_SW01_ROOM1_REPLACEABLE_ANCHOR", (sw['x1']+sw['x2'])/2, (sw['y1']+sw['y2'])/2, f4_z,
                        anchors, {"floor": "4F", "room": "SW-01", "status": "PROVISIONAL_REPLACEABLE",
                                  "room_bounds_m": [sw['x1'], sw['y1'], sw['x2'], sw['y2']],
                                  "door_id": "D001", "door_center_m": [door['x'], door['y']], "door_width_m": door['width'],
                                  "existing_godot_room_not_modified": True})
    anchor.empty_display_size = 3.0
    # thin floor outline makes the reserved 21x9.5 room visible in cutaway/plan without adding any interior.
    outline = make_box("F4_SW01_AnchorFloorOutline", sw['x1'], sw['y1'], sw['x2'], sw['y2'], f4_z+.04, f4_z+.08,
                       anchors, MATS["anchor"], {"purpose": "Room1 replacement footprint", "provisional": True})
    # The frozen segmented wall modules already retain the D001 opening. Use an empty
    # instead of geometry so the marker never plugs or implies a finished door.
    doorway = make_empty("F4_SW01_D001_DoorwayAnchor", door['x'], door['y'], f4_z+1.2, anchors,
                         {"doorway": "D001", "marker_only": True, "provisional": True,
                          "opening_width_m": door['width'], "opening_height_m": 2.4})
    doorway.empty_display_size = door['width']
    d001_panel = make_box("F4_SW01_D001_ClosedDoor__HIDE_TO_OPEN", door['x']-door['width']/2, door['y']-.035,
                          door['x']+door['width']/2, door['y']+.035, f4_z, f4_z+2.4, anchors, MATS["door"],
                          {"frozen_door_id": "D001", "closed_placeholder": True, "open_by_hiding_only": True,
                           "gameplay_behavior": "TBD", "not_godot_collision": True})

    # Section-only plane for a legible stack image; hidden in final source view/render.
    section_plane = make_box("Section_Ground_Reference", -25, FLOOR_SOUTH-20, MAIN_W+25, FLOOR_NORTH+20,
                             -4*STOREY-.3, -4*STOREY-.25, cutaway, MATS["slab"], {"presentation_only": True})
    section_plane.hide_render = True
    section_plane.hide_viewport = True

    exterior_cam = new_camera("CAM_Building_Exterior", (185, -185, 135), (0, 0, 27), cameras)
    exterior_cam.data.ortho_scale = 270
    section_cam = new_camera("CAM_Building_Section", (235, -270, 85), (0, 0, 18), cameras)
    section_cam.data.ortho_scale = 260
    f4_cam = new_camera("CAM_F4_SW01_Anchor", (-70, -88, 63), (-62, -30, f4_z+1.4), cameras)
    f4_cam.data.ortho_scale = 70

    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = 'WORLD'
    scene.display.shading.curvature_ridge_factor = 1.4
    scene.display.shading.curvature_valley_factor = 1.2
    scene.world.color = (0.025, 0.035, 0.045)

    # Exterior: basement hidden as required for the normal building overview.
    set_hidden(below, True)
    render_to(EVIDENCE / "building_exterior_v1.png", exterior_cam)
    # Structural section: show all stack levels; remove south-facing wall strips only for explanatory image.
    set_hidden(below, False)
    south_walls = [o for o in bpy.data.objects if o.get('frozen_wall_id') == 'W001']
    for o in south_walls: o.hide_render = True
    render_to(EVIDENCE / "building_section_all_levels_v1.png", section_cam)
    for o in south_walls: o.hide_render = False
    # F4: isolate only the floor relevant to future Room1 replacement, still intentionally no room interior/pods.
    for label, index in LEVELS:
        col = bpy.data.collections.get(label)
        col.hide_render = label != '4F'
    machine.hide_render = True
    roof.hide_render = True
    render_to(EVIDENCE / "f4_sw01_anchor_v1.png", f4_cam)
    for label, index in LEVELS:
        bpy.data.collections.get(label).hide_render = False
    set_hidden(below, True)
    machine.hide_render = False
    roof.hide_render = False
    scene.camera = exterior_cam

    validation = {
        "schema": "cryo_building_blockout_v1_validation",
        "status": "PASS_STATIC_SOURCE_AND_REOPEN_CHECK_PENDING",
        "source_layout": str(DATA_PATH.relative_to(ROOT)).replace('\\', '/'),
        "source_sha256": hashlib.sha256(DATA_PATH.read_bytes()).hexdigest(),
        "cad_geometry_imported": False,
        "standard_floor_count": len(LEVELS),
        "levels_bottom_to_top": [x[0] for x in LEVELS],
        "above_ground_count": 16,
        "below_ground_count": 4,
        "rooms_per_standard_floor": len(ROOMS),
        "frozen_floor_cells_per_standard_floor": len(FLOOR_CELLS),
        "passenger_shaft_voids_per_standard_floor": len(DATA.get("passenger_shaft_voids", [])),
        "freight_shafts_per_standard_floor": len(DATA.get("freight_shafts", [])),
        "nominal_rooms_building": len(ROOMS)*len(LEVELS),
        "nominal_pods_building": len(ROOMS)*20*len(LEVELS),
        "main_envelope_m": [MAIN_W, MAIN_D],
        "maximum_envelope_m": DATA.get("maximum_envelope_m"),
        "storey_height_m_provisional": STOREY,
        "wall_height_m_provisional": WALL_HEIGHT,
        "f4_anchor": {"room": "SW-01", "bounds": [sw['x1'], sw['y1'], sw['x2'], sw['y2']], "door": {"id": "D001", "x": door['x'], "y": door['y'], "width": door['width']}},
        "render_evidence": ["evidence/building_exterior_v1.png", "evidence/building_section_all_levels_v1.png", "evidence/f4_sw01_anchor_v1.png"],
        "limitations": ["Not playable", "Not final exterior", "No final materials or UV", "No room interiors or pods except F4 reserved footprint", "No cross-floor structural certification", "Frozen floor cells preserve plan decomposition but do not certify every freight/stair vertical opening"],
    }
    (OUT / "validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding='utf-8')
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))


if __name__ == "__main__":
    build()
