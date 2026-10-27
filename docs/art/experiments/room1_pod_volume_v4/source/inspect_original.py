"""Read-only geometry evidence probe for Room 1 pod v3.

Run with Blender 5.0.1 in background mode.  The script does not save, alter,
or export the loaded blend; it prints a JSON-compatible evidence structure.
"""

import bpy
import bmesh
import json
from mathutils import Vector


POD_OBJECTS = (
    "Reference_led_fixed_shell",
    "ONE_PIECE_COVER_head_window",
    "Sleeping_surface",
    "Foot_info_display_surface",
    "Whole_lid_motion",
)


def bounds(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return {
        "min_m": [round(min(corner[i] for corner in corners), 6) for i in range(3)],
        "max_m": [round(max(corner[i] for corner in corners), 6) for i in range(3)],
    }


def edge_face_counts(mesh):
    probe = bmesh.new()
    probe.from_mesh(mesh)
    counts = {}
    for edge in probe.edges:
        key = str(len(edge.link_faces))
        counts[key] = counts.get(key, 0) + 1
    probe.free()
    return counts


def probe_frame(frame):
    bpy.context.scene.frame_set(frame)
    result = {}
    for name in ("Whole_lid_motion", "ONE_PIECE_COVER_head_window"):
        obj = bpy.data.objects[name]
        result[name] = {
            "location_m": [round(value, 6) for value in obj.location],
            "rotation_euler_rad": [round(value, 6) for value in obj.rotation_euler],
            "world_bounds": bounds(obj),
        }
    return result


def glass_faces(cover):
    mesh = cover.data
    glass_index = next(
        index for index, material in enumerate(mesh.materials)
        if material and "glass" in material.name.lower()
    )
    result = []
    for polygon in mesh.polygons:
        if polygon.material_index != glass_index:
            continue
        result.append({
            "face_index": polygon.index,
            "vertices_local_m": [
                [round(value, 6) for value in mesh.vertices[index].co]
                for index in polygon.vertices
            ],
            "normal": [round(value, 5) for value in polygon.normal],
            "area_m2": round(polygon.area, 6),
        })
    return result


def main():
    shell = bpy.data.objects["Reference_led_fixed_shell"]
    cover = bpy.data.objects["ONE_PIECE_COVER_head_window"]
    display = bpy.data.objects["Foot_info_display_surface"]
    bpy.context.scene.frame_set(1)

    probe = bmesh.new()
    probe.from_mesh(shell.data)
    display_hole_boundary = [
        [[round(value, 6) for value in vertex.co] for vertex in edge.verts]
        for edge in probe.edges if len(edge.link_faces) == 1
    ]
    probe.free()

    evidence = {
        "source_blend": "../../room1_pixellab_pod_trial_v3/room1_pixellab_pod_trial_v3.blend",
        "coordinate_system": "Blender X width, Y length, Z height",
        "read_only": True,
        "frame_states": {"1": probe_frame(1), "60": probe_frame(60)},
        "mesh_summary": {
            name: {
                "vertices": len(bpy.data.objects[name].data.vertices),
                "edges": len(bpy.data.objects[name].data.edges),
                "polygons": len(bpy.data.objects[name].data.polygons),
                "edge_face_counts": edge_face_counts(bpy.data.objects[name].data),
                "world_bounds_frame_1": bounds(bpy.data.objects[name]),
            }
            for name in POD_OBJECTS if bpy.data.objects[name].type == "MESH"
        },
        "cover_parent": cover.parent.name if cover.parent else None,
        "display_hole_boundary_local_m": display_hole_boundary,
        "display_surface_frame_1_bounds": bounds(display),
        "glass_faces": glass_faces(cover),
        "glass_uv_planar_xy": {
            "formula": "U=(X+0.575)/1.15; V=(Y+1.15)/2.30",
            "local_bounds_m": {"min": [-0.447, 0.45132, -0.071402], "max": [0.447, 0.822357, 0.106]},
            "uv_bounds": {"min": [0.111304, 0.696226], "max": [0.888696, 0.857547]},
        },
    }
    print(json.dumps(evidence, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
