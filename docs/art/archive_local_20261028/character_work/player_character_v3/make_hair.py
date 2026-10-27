"""Low-poly long hair component for the 165 cm protagonist.

The module deliberately makes a thick back-and-side hair shell rather than
front-facing strips.  The face opening is centred on local/world -Y, matching
the project character's forward direction.  `build_hair` only creates meshes;
it never changes the source body or armature.
"""
from math import cos, sin, radians
import bpy
import bmesh
from mathutils import Vector


def _head_measurements(body, rig):
    """Derive head position and scale from current, already-normalised body."""
    head_group = body.vertex_groups.get("head")
    if head_group is None:
        raise ValueError("Body needs a vertex group named 'head'.")
    head_index = head_group.index
    points = []
    for vert in body.data.vertices:
        if any(g.group == head_index and g.weight >= 0.45 for g in vert.groups):
            points.append(body.matrix_world @ vert.co)
    if len(points) < 8:
        raise ValueError("The head vertex group has too few weighted vertices.")
    lo = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    hi = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    center = (lo + hi) * 0.5
    rx = max((hi.x - lo.x) * 0.58, 0.045)
    ry = max((hi.y - lo.y) * 0.64, 0.040)
    height = max(hi.z - lo.z, 0.10)
    return center, rx, ry, height, lo, hi


def _make_shell(name, center, rx, ry, height, collection, material):
    """Create one UV-unwrapped, open-front, back hair mass.

    The 50 degree face aperture leaves the forehead and nose silhouette open.
    Rings taper at the bottom, producing a contained shoulder-blade length
    block rather than dangling individual strands.
    """
    # z offset from head centre, x/y size multipliers.  Last rings end around
    # upper back; it is intentionally all head-bound until a lower hair bone
    # is agreed and tested.
    profile = [
        (0.55, 0.20, 0.18), (0.45, 0.74, 0.70), (0.24, 1.03, 0.98),
        (-0.05, 1.12, 1.10), (-0.35, 1.18, 1.15), (-0.70, 1.24, 1.20),
        (-1.10, 1.30, 1.25), (-1.43, 1.20, 1.16), (-1.65, 0.95, 0.90),
    ]
    # Actual long dimension follows head size; lower end target is normally
    # z 1.05--1.10 for the 165cm base, matching shoulder blade / upper-back.
    vertical = height * 1.05
    angular_steps = 12
    # This spans the scalp from the right temple through the *back* to the
    # left temple.  The omitted 50 degrees are centred on -Y (the face).
    first_angle, last_angle = 295.0, 605.0
    verts, uvs, faces = [], [], []
    for row, (z_factor, x_factor, y_factor) in enumerate(profile):
        z = center.z + z_factor * vertical
        for column in range(angular_steps + 1):
            t = column / angular_steps
            angle = radians(first_angle + (last_angle - first_angle) * t)
            # A small outward offset keeps the shell clear of the head.
            x = center.x + rx * x_factor * cos(angle)
            y = center.y + ry * y_factor * sin(angle) + 0.008
            verts.append((x, y, z))
            uvs.append((t, row / (len(profile) - 1)))
    cols = angular_steps + 1
    for row in range(len(profile) - 1):
        for col in range(angular_steps):
            a = row * cols + col
            faces.append((a, a + 1, a + cols + 1, a + cols))
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            mesh.uv_layers.active.data[loop_index].uv = uvs[mesh.loops[loop_index].vertex_index]
    mesh.materials.append(material)
    hair = bpy.data.objects.new(name, mesh)
    collection.objects.link(hair)
    for poly in mesh.polygons:
        poly.use_smooth = False
    solid = hair.modifiers.new("Hair_shell_thickness_8mm", 'SOLIDIFY')
    solid.thickness = 0.008
    solid.offset = 0.0
    solid.use_even_offset = True
    return hair


def _make_temple_lock(name, center, rx, ry, height, side, collection, material):
    """Short side lock framing the cheek without crossing the face."""
    x = center.x + side * rx * 0.94
    # Character faces world -Y.  These stay at the side / slightly behind it.
    y = center.y - ry * 0.56
    z_top = center.z + height * 0.32
    z_bottom = center.z - height * 0.48
    width = max(rx * 0.15, 0.012)
    depth = max(ry * 0.18, 0.010)
    verts = [
        (x - side * width, y, z_top), (x + side * width, y, z_top),
        (x + side * width * 0.75, y, z_bottom), (x - side * width * 0.75, y, z_bottom),
        (x - side * width, y + depth, z_top), (x + side * width, y + depth, z_top),
        (x + side * width * 0.75, y + depth, z_bottom), (x - side * width * 0.75, y + depth, z_bottom),
    ]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    uv = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for index, loop_index in enumerate(poly.loop_indices):
            uv.data[loop_index].uv = ((index & 1), 1 if index > 1 else 0)
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def _bind_to_head(obj, rig):
    modifier = obj.modifiers.new("Armature_head_only", 'ARMATURE')
    modifier.object = rig
    group = obj.vertex_groups.new(name="head")
    group.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')


def _validate(objects):
    results = {}
    for obj in objects:
        mesh = obj.data
        mesh.calc_loop_triangles()
        bm = bmesh.new()
        bm.from_mesh(mesh)
        uv = mesh.uv_layers.active
        uv_values = [loop.uv for loop in uv.data]
        results[obj.name] = {
            "vertices": len(mesh.vertices), "triangles": len(mesh.loop_triangles),
            "boundary_edges": sum(edge.is_boundary for edge in bm.edges),
            "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
            "zero_area_faces": sum(face.calc_area() < 1e-10 for face in bm.faces),
            "uv_layer": uv.name if uv else None,
            "uv_range": [[min(v[i] for v in uv_values), max(v[i] for v in uv_values)] for i in range(2)],
            "material_slots": [m.name for m in mesh.materials],
        }
        bm.free()
    return results


def build_hair(body, rig, collection, material):
    """Build the editable 3-object long-hair component.

    Contract: `body` and `rig` are in normalised world scale; `body` has the
    original `head` vertex group.  Returns [back_shell, left_temple, right_temple].
    All vertices are weighted 100% to existing `head`; no bones are added.
    """
    center, rx, ry, height, _lo, _hi = _head_measurements(body, rig)
    shell = _make_shell("Hair_BackShell", center, rx, ry, height, collection, material)
    left = _make_temple_lock("Hair_Temple_L", center, rx, ry, height, 1, collection, material)
    right = _make_temple_lock("Hair_Temple_R", center, rx, ry, height, -1, collection, material)
    objects = [shell, left, right]
    for obj in objects:
        _bind_to_head(obj, rig)
        obj["component"] = "protagonist_long_dark_hair"
        obj["binding"] = "100% existing head bone; lower hair physics is TBD"
        obj["uv_status"] = "explicit non-overlapping UV coordinates, 0..1"
        obj["material_status"] = "replaceable single material slot"
    shell["style_note"] = "Open face aperture; compact upper-back length hair mass."
    return objects

