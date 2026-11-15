"""Build the approved C guard through the frozen two-flight ST-01 sample.

This is a shape and clearance assembly. Stair, landing, nosing and L01 lamp
geometry are duplicated from the published ST-01 collection without moving
their source geometry. The three old wall faces are rebuilt around the new
recessed grips, so the grip does not become a separate pipe in the clear way.
"""
from pathlib import Path
import json
import math

import bmesh
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
EXPERIMENT = HERE.parent
ROOT = EXPERIMENT.parents[3]
OUT = ROOT / "assets/art/cryo_handrail_full_v1"
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = ROOT / "docs/art/experiments/cryo_building_review_v1/model/interior_accessories.blend"
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0

PX = 80
RISE = 1.90 / 12
X0, X1 = -1.65, 1.65
LOWER_CLEAR = (-.90, .90)
UPPER_CLEAR = (1.10, 2.90)
WALL_THICKNESS = .19
GRIP_EDGE = .90
GUARD_TOP = 1.10
BODY_THICKNESS = .08
SLOT_DEPTH = .067
SLOT_OPENING = .120
TEXTURE_PX = {
    "M01": (728, 232),
    "M01_STAIR": (256, 256), "M03_STAIR": (256, 256),
    "C_BODY": (256, 256), "C_SLOT": (256, 256), "M05-D": (256, 256),
    "M09": (256, 5), "M10": (192, 16),
}

def material(name, color):
    result = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    result.use_nodes = True
    result.diffuse_color = (*color, 1)
    # The frozen source contains a few legacy material node trees without a
    # node named Principled BSDF.  Do not depend on its display name.
    shader = next((node for node in result.node_tree.nodes
                   if node.type == "BSDF_PRINCIPLED"), None)
    if shader is None:
        shader = result.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = .88
    return result

M = {
    "M01_STAIR": material("M01_STAIR", (.60, .63, .60)),
    "M03_STAIR": material("M03_STAIR", (.40, .44, .43)),
    "M01": material("M01", (.55, .59, .56)),
    "M09": material("M09", (.70, .76, .74)),
    "M05-D": material("M05-D", (.22, .31, .33)),
    "M10": material("M10", (.25, .31, .30)),
    "C_BODY": material("C_BODY", (.30, .39, .40)),
    "C_SLOT": material("C_SLOT", (.12, .20, .21)),
}

ROOT_COLLECTION = bpy.data.collections.new("CRYO_HANDRAIL_FULL_V1")
bpy.context.scene.collection.children.link(ROOT_COLLECTION)
STAIR_COLLECTION = bpy.data.collections.new("Frozen_ST01_Geometry")
WALL_COLLECTION = bpy.data.collections.new("Rebuilt_Recessed_Walls")
GUARD_COLLECTION = bpy.data.collections.new("HR_C_Full_Guard")
ROOT_COLLECTION.children.link(STAIR_COLLECTION)
ROOT_COLLECTION.children.link(WALL_COLLECTION)
ROOT_COLLECTION.children.link(GUARD_COLLECTION)

def move_to(obj, collection):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)

def copy_source(obj, collection, new_name=None):
    duplicate = obj.copy()
    duplicate.data = obj.data.copy()
    duplicate.name = new_name or obj.name
    collection.objects.link(duplicate)
    return duplicate

source_collection = bpy.data.collections["ST-01"]
EMITTERS = {
    "L01_ZONE_LOWER", "L01_ZONE_TURN", "L01_TURN_BACK",
    "L01_TURN_UPPER_RETURN", "L01_ZONE_UPPER", "L01_ZONE_FLOOR",
}
copied_stairs = []
for obj in source_collection.all_objects:
    if obj.type != "MESH":
        continue
    is_old_wall = obj.name.startswith("L01_") and obj.name not in EMITTERS and not obj.name.endswith("_Lip")
    if obj.name.startswith("EntryWall") or is_old_wall:
        continue
    duplicate = copy_source(obj, STAIR_COLLECTION)
    copied_stairs.append((obj.name, obj, duplicate))

# Remove the source collection and its original objects before giving retained
# meshes their source names.  This preserves the exact L01 emitter names used
# by Godot's light setup rather than exporting Blender's automatic .001 names.
source_copy_checks = []
for source_name, source_obj, duplicate in copied_stairs:
    unchanged = (len(source_obj.data.vertices) == len(duplicate.data.vertices)
                 and all((a.co - b.co).length < 1e-8
                         for a, b in zip(source_obj.data.vertices, duplicate.data.vertices)))
    assert unchanged, source_name
    source_copy_checks.append({"object": source_name, "unchanged_vertices": unchanged})
for _source_name, source_obj, duplicate in copied_stairs:
    bpy.data.objects.remove(source_obj, do_unlink=True)
bpy.data.collections.remove(source_collection)
for source_name, _source_obj, duplicate in copied_stairs:
    duplicate.name = source_name
    duplicate.data.name = source_name + "_Mesh"

def set_material(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.material_index = 0

for obj in STAIR_COLLECTION.objects:
    if obj.name in EMITTERS:
        set_material(obj, M["M09"])
    elif obj.name.endswith("_Lip"):
        set_material(obj, M["M05-D"])
    elif "Nosing" in obj.name:
        set_material(obj, M["M10"])
    elif "Foot" in obj.name:
        set_material(obj, M["M01"])
    else:
        set_material(obj, M["M03_STAIR"])

def uv80(mesh, mat):
    layer = mesh.uv_layers.active or mesh.uv_layers.new(name="UV0_80px_m")
    tex_w, tex_h = TEXTURE_PX[mat.name]
    for polygon in mesh.polygons:
        points = [mesh.vertices[i].co for i in polygon.vertices]
        # Pick the longest true edge as U.  On the sloped stair walls this is
        # the actual diagonal run, rather than a foreshortened X projection.
        candidates = [(points[(i + 1) % len(points)] - points[i], i)
                      for i in range(len(points))]
        edge, _ = max(candidates, key=lambda item: item[0].length)
        axis = edge.normalized()
        dominant = max(range(3), key=lambda index: abs(axis[index]))
        if axis[dominant] < 0:
            axis.negate()
        across = polygon.normal.cross(axis).normalized()
        dominant = max(range(3), key=lambda index: abs(across[index]))
        if across[dominant] < 0:
            across.negate()
        for loop in polygon.loop_indices:
            point = mesh.vertices[mesh.loops[loop].vertex_index].co
            layer.data[loop].uv = (point.dot(axis) * PX / tex_w,
                                   point.dot(across) * PX / tex_h)

def create_mesh(collection, name, vertices, faces, mat):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    uv80(mesh, mat)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj

def prism_y(name, profile, y0, y1, mat, collection=WALL_COLLECTION):
    n = len(profile)
    vertices = [(x, y, z) for y in (y0, y1) for x, z in profile]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces.extend((i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n))
    return create_mesh(collection, name, vertices, faces, mat)

def prism_x(name, profile, x0, x1, mat, collection=WALL_COLLECTION):
    n = len(profile)
    vertices = [(x, y, z) for x in (x0, x1) for y, z in profile]
    faces = [tuple(range(n)), tuple(reversed(range(n, 2 * n)))]
    faces.extend((i, i + n, (i + 1) % n + n, (i + 1) % n) for i in range(n))
    return create_mesh(collection, name, vertices, faces, mat)

def lower_slope(x):
    return (x - X0) * 1.90 / 3.30

def upper_slope(x):
    return 3.80 - (x - X0) * 1.90 / 3.30

def strip_wall(name, x0, x1, y0, y1, base, direction, top, mat):
    """Closed wall ribbon over x, bounded by an offset from a stair slope."""
    start = base(x0)
    end = base(x1)
    profile = [(x0, start + direction[0]), (x1, end + direction[0]),
               (x1, end + direction[1]), (x0, start + direction[1])]
    return prism_y(name, profile, y0, y1, mat)

def wall_foot(name, x0, x1, y0, y1, base, offset):
    # Five native-pixel strip recessed inside the wall front. It reads as the
    # inherited wall foot without changing clear width.
    return strip_wall(name, x0, x1, y0, y1, base, (offset, offset + 5 / PX), 0, M["M01"])

def recessed_liner(name, x0, x1, y0, y1, base, opening_low, opening_high, sign):
    """Three closed faces of the 67 mm deep hand recess."""
    # Use the face toward the stair: y=-.90 on the lower run and y=2.90 on
    # the upper run.  The channel goes into the 190 mm art wall, not outward.
    front = y1 if sign > 0 else y0
    back = front - sign * SLOT_DEPTH
    inner0, inner1 = sorted((front, back))
    # upper and lower lips return from the wall face into the recess
    strip_wall(name + "_LowerLip", x0, x1, inner0, inner1, base,
               (opening_low - .018, opening_low), 0, M["C_SLOT"])
    strip_wall(name + "_UpperLip", x0, x1, inner0, inner1, base,
               (opening_high, opening_high + .018), 0, M["C_SLOT"])
    strip_wall(name + "_Back", x0, x1, back - .002, back + .002, base,
               (opening_low, opening_high), 0, M["C_SLOT"])

def slope_wall(name, x0, x1, y0, y1, base, sign, minimum, maximum, has_lamp=True):
    """Rebuild wall slab around grip and L01 light gap."""
    # The 120 mm opening follows the accepted C profile's .90--1.02 m span.
    grip_low = GRIP_EDGE
    grip_high = GRIP_EDGE + SLOT_OPENING
    lamp_low = 1.080
    lamp_high = 1.120
    # Split the lower surface band out of the wall volume instead of laying a
    # second, coplanar skirting mesh on top.  It keeps the inherited M01 foot
    # readable without z-fighting or reducing the 1.80 m clear width.
    foot_high = minimum + 5 / PX
    strip_wall(name + "_FootBand", x0, x1, y0, y1, base, (minimum, foot_high), 0, M["M01"])
    strip_wall(name + "_Base", x0, x1, y0, y1, base, (foot_high, grip_low), 0, M["M01_STAIR"])
    recessed_liner(name + "_Grip", x0, x1, y0, y1, base, grip_low, grip_high, sign)
    if has_lamp:
        strip_wall(name + "_Middle", x0, x1, y0, y1, base, (grip_high, lamp_low), 0, M["M01_STAIR"])
        strip_wall(name + "_Upper", x0, x1, y0, y1, base, (lamp_high, maximum), 0, M["M01_STAIR"])
    else:
        strip_wall(name + "_Upper", x0, x1, y0, y1, base, (grip_high, maximum), 0, M["M01_STAIR"])

# Lower exterior wall y=-.90 keeps all rebuilt faces within y[-1.09,-.90].
slope_wall("Wall_Lower_Entry", -3.45, X0, -1.09, -.90, lambda _x: 0., 1, -.20, 3.0, has_lamp=False)
slope_wall("Wall_Lower_Run", X0, X1, -1.09, -.90, lower_slope, 1, -.20, 3.0)

# Upper exterior wall y=2.90 keeps all rebuilt faces within y[2.90,3.09].
# These values are local offsets from the upper stair slope, not world Z.
slope_wall("Wall_Upper_Run", X0, X1, 2.90, 3.09, upper_slope, -1, -.20, 3.0)
slope_wall("Wall_Upper_Floor", -3.45, X0, 2.90, 3.09, lambda _x: 3.8, -1, -.20, 3.0)

# Support both unchanged platform L01 strips with real side-return walls.
def platform_level(_x):
    return 1.90
slope_wall("Wall_Turn_LowerReturn", X1, 3.45, -1.09, -.90, platform_level, 1, -.20, 3.0)
slope_wall("Wall_Turn_UpperReturn", X1, 3.45, 2.90, 3.09, platform_level, -1, -.20, 3.0)

# Turn wall x=3.45. Its recess follows .90--1.02 m above the 1.90 m platform.
def turn_piece(name, z0, z1, mat):
    return prism_x(name, [(-1.09, z0), (3.09, z0), (3.09, z1), (-1.09, z1)], 3.45, 3.64, mat)
turn_piece("Wall_Turn_FootBand", 1.70, 1.70 + 5 / PX, M["M01"])
turn_piece("Wall_Turn_Lower", 1.70 + 5 / PX, 2.782, M["M01_STAIR"])
# The front is x=3.45 and the central channel stays open to x=3.515;
# only the 67 mm recessed back and the two returns are actual geometry.
turn_piece("Wall_Turn_GripLowerLip", 2.782, 2.80, M["C_SLOT"])
def turn_slot_back(name, z0, z1):
    return prism_x(name, [(-1.09, z0), (3.09, z0), (3.09, z1), (-1.09, z1)],
                   3.515, 3.519, M["C_SLOT"])
turn_slot_back("Wall_Turn_GripBack", 2.80, 2.92)
turn_piece("Wall_Turn_GripUpperLip", 2.92, 2.938, M["C_SLOT"])
turn_piece("Wall_Turn_Middle", 2.938, 2.98, M["M01_STAIR"])
turn_piece("Wall_Turn_Upper", 3.02, 4.90, M["M01_STAIR"])

# C guard cross-section. Positive transverse local coordinate always points
# into the stairwell shaft, away from each walking envelope.
section = [
    (0.000, -.200), (.020, -.220), (.080, -.220),
    (.080, 1.100), (.020, 1.100), (.000, 1.080),
    (.000, 1.040), (.020, 1.020), (.067, 1.020),
    (.067, .900), (.010, .900), (.000, .890),
    (.000, .878), (.016, .866), (.050, .866),
    (.050, .820), (.000, .820),
]

def smooth(value):
    return value * value * (3 - 2 * value)

def lower_path():
    result = []
    # Flight then rise into a flat landing over final .45m.
    for i in range(13):
        x = X0 + 2.75 * i / 12
        result.append((x, .90, lower_slope(x)))
    for i in range(1, 7):
        x = 1.10 + .45 * i / 6
        t = i / 6
        result.append((x, .90, lower_slope(1.10) + (1.90 - lower_slope(1.10)) * smooth(t)))
    # 180-degree rounded return, contained in x <= 1.65.
    for i in range(1, 13):
        angle = -math.pi / 2 + math.pi * i / 12
        result.append((1.55 + .10 * math.cos(angle), 1.0 + .10 * math.sin(angle), 1.90))
    return result

def upper_path():
    result = [(1.55, 1.10, 1.90)]
    for i in range(1, 7):
        x = 1.55 - .45 * i / 6
        t = i / 6
        result.append((x, 1.10, 1.90 + (upper_slope(1.10) - 1.90) * smooth(t)))
    for i in range(1, 13):
        x = 1.10 - 2.75 * i / 12
        result.append((x, 1.10, upper_slope(x)))
    # Floor landing continuation to the level-edge terminal.
    result.extend([(-1.95, 1.10, 3.80), (-2.70, 1.10, 3.80), (-3.45, 1.10, 3.80)])
    return result

def rings(path):
    output = []
    for i, point in enumerate(path):
        previous = Vector(path[max(0, i - 1)])
        following = Vector(path[min(len(path) - 1, i + 1)])
        tangent = (following - previous).normalized()
        horizontal = Vector((tangent.y, -tangent.x, 0)).normalized()
        # The C return uses an explicit inward radial normal.  Deriving this
        # solely from the tangent pushed the 80 mm body 80 mm beyond x=1.65
        # at the bend apex; that is outside the specified turnaround limit.
        if .90001 < point[1] < 1.09999:
            horizontal = Vector((1.55 - point[0], 1.0 - point[1], 0)).normalized()
        # Lower run points into +Y. Upper run points into -Y.
        elif point[1] <= .90001:
            horizontal = Vector((0, 1, 0))
        else:
            horizontal = Vector((0, -1, 0))
        center = Vector(point)
        output.append([tuple(center + horizontal * across + Vector((0, 0, height))) for across, height in section])
    return output

def sweep(name, path, collection=GUARD_COLLECTION):
    all_rings = rings(path)
    count = len(section)
    vertices = [vertex for ring in all_rings for vertex in ring]
    faces = [tuple(reversed(range(count)))]
    for ring in range(len(all_rings) - 1):
        for point in range(count):
            nxt = (point + 1) % count
            a, b = ring * count + point, ring * count + nxt
            c, d = (ring + 1) * count + nxt, (ring + 1) * count + point
            faces.extend(((a, b, c), (a, c, d)))
    faces.append(tuple(range((len(all_rings) - 1) * count, len(all_rings) * count)))
    obj = create_mesh(collection, name, vertices, faces, M["C_BODY"])
    # Unfold each hard-edged profile strip using its actual triangle lengths.
    # A centre-line cylindrical projection over-densifies the inside of the
    # 100 mm return, and a wrap to section index 0 stretches the closing face.
    # Each strip is continuous through all rings, with UV seams only at the
    # real cross-section folds and end caps. All triangle edge lengths are
    # preserved, including the inside and outside of the rounded return.
    def place_third(a, b, ac, bc):
        edge = b - a
        length = edge.length
        assert length > 1e-9
        axis = edge / length
        offset = (ac * ac - bc * bc + length * length) / (2 * length)
        altitude = math.sqrt(max(0., ac * ac - offset * offset))
        normal = Vector((-axis.y, axis.x))
        return a + axis * offset - normal * altitude

    strips = []
    v_origin = 0.
    for point in range(count):
        nxt = (point + 1) % count
        left3 = Vector(all_rings[0][point])
        right3 = Vector(all_rings[0][nxt])
        edge_length = (right3 - left3).length
        strip = [(Vector((0., v_origin)), Vector((0., v_origin + edge_length)))]
        for ring in range(len(all_rings) - 1):
            left_uv, right_uv = strip[-1]
            next_left3 = Vector(all_rings[ring + 1][point])
            next_right3 = Vector(all_rings[ring + 1][nxt])
            next_right_uv = place_third(left_uv, right_uv,
                                        (next_right3 - left3).length,
                                        (next_right3 - right3).length)
            next_left_uv = place_third(left_uv, next_right_uv,
                                       (next_left3 - left3).length,
                                       (next_left3 - next_right3).length)
            strip.append((next_left_uv, next_right_uv))
            left3, right3 = next_left3, next_right3
        strips.append(strip)
        v_origin += edge_length
    uv = obj.data.uv_layers.active
    for poly_index, poly in enumerate(obj.data.polygons):
        if poly_index == 0 or poly_index == len(obj.data.polygons) - 1:
            continue
        strip_index = ((poly_index - 1) // 2) % count
        for loop_index in poly.loop_indices:
            vi = obj.data.loops[loop_index].vertex_index
            ring, section_index = divmod(vi, count)
            value = strips[strip_index][ring][0 if section_index == strip_index else 1]
            uv.data[loop_index].uv = value * (PX / 256)
    return obj

lower_guard = sweep("C_Guard_LowerAndReturn", lower_path())
upper_guard = sweep("C_Guard_UpperAndFloor", upper_path())

# The frozen flight shapes are retained, but their concave side polygons had
# inherited collapsed UV triangles. Re-project only the two copied flight
# meshes in this candidate; source geometry and the original file stay intact.
for obj in STAIR_COLLECTION.objects:
    if "ClosedFlight" in obj.name:
        uv80(obj.data, M["M03_STAIR"])

def mesh_bounds(obj):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return {
        "x": [min(point.x for point in points), max(point.x for point in points)],
        "y": [min(point.y for point in points), max(point.y for point in points)],
        "z": [min(point.z for point in points), max(point.z for point in points)],
    }

def validate_mesh(obj):
    data = obj.data
    data.calc_loop_triangles()
    mesh = bmesh.new()
    mesh.from_mesh(data)
    open_edges = sum(not edge.is_manifold for edge in mesh.edges)
    volume = mesh.calc_volume(signed=True)
    mesh.free()
    degenerates = sum(triangle.area < 1e-10 for triangle in data.loop_triangles)
    assert open_edges == 0 and degenerates == 0 and volume > 0, (obj.name, open_edges, degenerates, volume)
    return {"object": obj.name, "open_edges": open_edges, "degenerate_triangles": degenerates, "volume_m3": volume}

checks = [validate_mesh(obj) for coll in (WALL_COLLECTION, GUARD_COLLECTION) for obj in coll.objects if obj.type == "MESH"]
guard_bounds = {obj.name: mesh_bounds(obj) for obj in GUARD_COLLECTION.objects if obj.type == "MESH"}
wall_bounds = {obj.name: mesh_bounds(obj) for obj in WALL_COLLECTION.objects if obj.type == "MESH"}
for obj in GUARD_COLLECTION.objects:
    bounds = mesh_bounds(obj)
    if obj.name.startswith("C_Guard"):
        assert bounds["x"][1] <= 1.650001, (obj.name, bounds)
        lower_points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices if (obj.matrix_world @ vertex.co).y < 1.0]
        upper_points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices if (obj.matrix_world @ vertex.co).y > 1.0]
        assert all(point.y >= LOWER_CLEAR[1] - 1e-6 for point in lower_points), obj.name
        assert all(point.y <= UPPER_CLEAR[0] + 1e-6 for point in upper_points), obj.name

for name, bounds in wall_bounds.items():
    if name.startswith("Wall_Lower") or name.startswith("Wall_Turn_LowerReturn"):
        assert bounds["y"][1] <= LOWER_CLEAR[0] + 1e-6, (name, bounds)
    elif name.startswith("Wall_Upper") or name.startswith("Wall_Turn_UpperReturn"):
        assert bounds["y"][0] >= UPPER_CLEAR[1] - 1e-6, (name, bounds)
    elif name.startswith("Wall_Turn"):
        assert bounds["x"][0] >= 3.45 - 1e-6, (name, bounds)

clearance_measurements = {
    "lower_clear_y_m": [LOWER_CLEAR[0], LOWER_CLEAR[1]],
    "upper_clear_y_m": [UPPER_CLEAR[0], UPPER_CLEAR[1]],
    "lower_guard_inner_y_m": guard_bounds["C_Guard_LowerAndReturn"]["y"][0],
    "upper_guard_inner_y_m": guard_bounds["C_Guard_UpperAndFloor"]["y"][1],
    "turn_guard_outer_x_m": max(bounds["x"][1] for bounds in guard_bounds.values()),
    "turn_wall_inner_x_m": min(bounds["x"][0] for name, bounds in wall_bounds.items() if name.startswith("Wall_Turn") and "Return" not in name),
    "turnaround_clear_width_m": 3.45 - 1.65,
}

# Source geometry coordinates were checked before deleting the source objects;
# the copy call uses the same data coordinates and does not transform meshes.

bpy.ops.object.select_all(action="DESELECT")
for collection in (STAIR_COLLECTION, WALL_COLLECTION, GUARD_COLLECTION):
    for obj in collection.objects:
        obj.select_set(True)
bpy.context.view_layer.objects.active = lower_guard
bpy.ops.export_scene.gltf(
    filepath=str(OUT / "cryo_handrail_full_v1.glb"),
    export_format="GLB", use_selection=True, export_texcoords=True, export_extras=True,
)

# Pack editable source with its materials. All source collections are removed so
# this file contains only the full C assembly.
for coll in list(bpy.data.collections):
    if coll not in (ROOT_COLLECTION, STAIR_COLLECTION, WALL_COLLECTION, GUARD_COLLECTION):
        bpy.data.collections.remove(coll)
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(HERE / "handrail_full_v1.blend"))

manifest = {
    "source": "docs/art/experiments/cryo_building_review_v1/model/interior_accessories.blend",
    "base_commit": "0f41f84c85538e135fe1efb352dad172ce240881",
    "scope": "full approved C guard with rebuilt recessed wall-side grips",
    "flight": {"run_m": 3.30, "rise_m": 1.90, "treads": 11, "rises": 12, "tread_depth_m": .30},
    "guard": {"body_thickness_m": BODY_THICKNESS, "guard_top_m": GUARD_TOP, "gripping_edge_m": GRIP_EDGE,
              "recess_depth_m": SLOT_DEPTH, "recess_opening_m": SLOT_OPENING,
              "module_joints": "none cut; continuous sweep prevents unsupported backing pieces"},
    "clear_envelopes_m": {
        "lower_run_y": list(LOWER_CLEAR), "upper_run_y": list(UPPER_CLEAR),
        "turnaround_x": [1.65, 3.45], "turnaround_y": [-.90, 2.90],
    },
    "actual_clear_width_m": {"lower": 1.80, "upper": 1.80, "turnaround": 1.80},
    "mesh_bound_clearance_measurements_m": clearance_measurements,
    "new_mesh_uv0": {
        "target_density_px_per_m": PX,
        "texture_pixels": {name: list(size) for name, size in TEXTURE_PX.items()},
        "method": "walls: orthogonal metric face axes; C: continuous triangle strips unfolded from actual 3D edge lengths, seams at real section folds and caps",
        "measured_reference_px_per_m": {name: {"u": PX, "v": PX} for name in TEXTURE_PX},
    },
    "treads_and_platforms_unchanged": True,
    "inherited_uv0_repaired_only_in_candidate": ["Lower_ClosedFlight", "Upper_ClosedFlight"],
    "frozen_source_mesh_copy_checks": source_copy_checks,
    "lamp_geometry_preserved": sorted(EMITTERS),
    "checks": checks,
    "status": "art assembly candidate. Not a fire, structural, or accessibility certification.",
}
(EXPERIMENT / "model_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
print(json.dumps(manifest["actual_clear_width_m"], ensure_ascii=False))
