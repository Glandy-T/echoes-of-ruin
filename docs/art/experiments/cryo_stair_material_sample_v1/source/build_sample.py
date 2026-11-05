"""Build the standalone v1 stair material-review sample.

This is deliberately a cutaway: one rising flight, its entry and half-turn
landings, a representative left wall, and a simple inner rail.  It is not a
replacement for any frozen building stair core or a Godot scene.
"""
from pathlib import Path
import json
import math
import os
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[5]
ASSET = ROOT / "assets/art/cryo_stair_material_sample_v1"
BLEND = Path(__file__).resolve().parent.parent / "model/stair_material_sample_v1.blend"
GLB = ASSET / "stair_material_sample_v1.glb"

# Frozen-plan-derived review module dimensions, in metres.
FLIGHT_WIDTH = 1.8
FLIGHT_RUN = 3.3
FLIGHT_RISE = 1.9
TREADS = 11
TREAD = 0.3
ENTRY_Y = (-1.8, 0.0)
TURN_Y = (3.3, 5.1)
LANDING_X = (-2.0, 1.8)  # 3.8m full landing width; returning flight omitted.
PIXELS_PER_METRE = 80
MINERAL_METRES = (2.4, 3.2)  # native 192x256 at 80 px/m
WALL_METRES = (9.1, 2.9)     # native 728x232 at 80 px/m
QA = ASSET / "stair_material_sample_v1_static_qa.json"


def make_mesh(name, verts, faces, uvs=None):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    if uvs:
        layer = mesh.uv_layers.new(name="UV0")
        for polygon, polygon_uvs in zip(mesh.polygons, uvs):
            for loop_index, uv in zip(polygon.loop_indices, polygon_uvs):
                layer.data[loop_index].uv = uv
    return mesh


def box_mesh(name, x1, x2, y1, y2, z1, z2, image_metres, uv_origin=(0.0, 0.0)):
    verts = [(x1,y1,z1), (x2,y1,z1), (x2,y2,z1), (x1,y2,z1),
             (x1,y1,z2), (x2,y1,z2), (x2,y2,z2), (x1,y2,z2)]
    faces = [(0,3,2,1), (4,5,6,7), (0,1,5,4), (1,2,6,5),
             (2,3,7,6), (3,0,4,0)]
    # Last face is corrected below to retain a closed manifold cuboid.
    faces[-1] = (3,0,4,7)
    ox, oy = uv_origin
    # UV0 uses physical metres divided by this material's actual image axes.
    # This keeps every major surface at exactly 80 px/m even for non-square
    # inputs (192x256 mineral and 192x16 tread-edge strips).
    iw, ih = image_metres
    sx, sy, sz = (x2-x1)/iw, (y2-y1)/ih, (z2-z1)/ih
    sy_u = (y2-y1)/iw
    uvs = [((ox,oy),(ox+sx,oy),(ox+sx,oy+sy),(ox,oy+sy)),
           ((ox,oy),(ox+sx,oy),(ox+sx,oy+sy),(ox,oy+sy)),
           ((ox,oy),(ox+sx,oy),(ox+sx,oy+sz),(ox,oy+sz)),
           ((ox,oy),(ox+sy_u,oy),(ox+sy_u,oy+sz),(ox,oy+sz)),
           ((ox,oy),(ox+sx,oy),(ox+sx,oy+sz),(ox,oy+sz)),
           ((ox,oy),(ox+sy_u,oy),(ox+sy_u,oy+sz),(ox,oy+sz))]
    return make_mesh(name, verts, faces, uvs)


def object_box(name, bounds, collection, material, image_metres, tags, uv_origin=(0.0, 0.0)):
    obj = bpy.data.objects.new(name, box_mesh(name + "_Mesh", *bounds, image_metres, uv_origin))
    collection.objects.link(obj)
    obj.data.materials.append(material)
    for key, value in tags.items():
        obj[key] = value
    return obj


def image_material(name, filename, fallback, expected_metres):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next((node for node in mat.node_tree.nodes if node.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None:
        bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.95
    bsdf.inputs["Specular IOR Level"].default_value = 0.05
    path = ASSET / filename
    if path.is_file():
        image = bpy.data.images.load(str(path), check_existing=True)
        image.name = filename
        image.colorspace_settings.name = "sRGB"
        image_metres = (image.size[0] / PIXELS_PER_METRE, image.size[1] / PIXELS_PER_METRE)
        tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = image
        tex.interpolation = 'Closest'
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        mat["texture_source"] = str(path.relative_to(ROOT)).replace("\\", "/")
        mat["texture_status"] = "AUTHORED_INPUT"
    else:
        image_metres = expected_metres
        bsdf.inputs["Base Color"].default_value = fallback
        mat["texture_source"] = filename
        mat["texture_status"] = "TEMPORARY_CONSTANT__REBUILD_WHEN_INPUT_PRESENT"
    mat["uv0_density_px_per_m"] = PIXELS_PER_METRE
    mat["physical_image_width_m"] = image_metres[0]
    mat["physical_image_height_m"] = image_metres[1]
    return mat, image_metres


def plain_material(name, color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next(node for node in mat.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.95
    bsdf.inputs["Specular IOR Level"].default_value = 0.05
    mat["texture_status"] = "INTENTIONALLY_UNTEXTURED_PROVISIONAL"
    return mat


def cylinder_between(name, start, end, radius, collection, material, tags):
    delta = Vector(end) - Vector(start)
    midpoint = (Vector(start) + Vector(end)) / 2
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=radius, depth=delta.length,
                                        location=midpoint)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = delta.to_track_quat('Z', 'Y').to_euler()
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    for key, value in tags.items():
        obj[key] = value
    return obj


def closed_manifold(mesh):
    counts = {}
    for polygon in mesh.polygons:
        vertices = polygon.vertices
        for index, vertex in enumerate(vertices):
            edge = tuple(sorted((vertex, vertices[(index + 1) % len(vertices)])))
            counts[edge] = counts.get(edge, 0) + 1
    return bool(counts) and all(count == 2 for count in counts.values())


def build():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for item in list(bpy.data.collections):
        bpy.data.collections.remove(item)
    root = bpy.data.collections.new("STAIR_MATERIAL_SAMPLE_V1__CUTAWAY_ONLY")
    bpy.context.scene.collection.children.link(root)
    geo = bpy.data.collections.new("GEOMETRY__ONE_FLIGHT_ENTRY_TURN")
    root.children.link(geo)
    rail = bpy.data.collections.new("PROVISIONAL_INNER_HANDRAIL")
    root.children.link(rail)

    mineral_a, mineral_a_m = image_material("M_Stair_Mineral_A", "mineral_a.png", (0.34, 0.36, 0.36, 1), MINERAL_METRES)
    mineral_b, mineral_b_m = image_material("M_Stair_Mineral_B", "mineral_b.png", (0.29, 0.31, 0.31, 1), MINERAL_METRES)
    tread_edge, edge_m = image_material("M_Stair_Tread_Edge", "tread_edge.png", (0.42, 0.43, 0.42, 1), (2.4, 0.2))
    wall, wall_m = image_material("M_R24_Wall_Body", "wall_body.png", (0.25, 0.28, 0.29, 1), WALL_METRES)
    rail_mat = plain_material("M_Provisional_Handrail_Matte", (0.20, 0.22, 0.22, 1))
    tags = {"asset_role": "stair_material_sample", "sample_version": "v1",
            "scope": "REPRESENTATIVE_CUTAWAY_NOT_BUILDING_REPLACEMENT"}

    # Closed blocks make each tread and riser visibly physical; there is no
    # diagonal greybox ramp hidden through the step surfaces.
    object_box("EntryLanding__3p8m_full_width", (*LANDING_X, *ENTRY_Y, -0.18, 0.0), geo,
               mineral_a, mineral_a_m, dict(tags, segment="entry_landing", omitted_second_flight=True), (.071, .173))
    for i in range(TREADS):
        y1, y2 = i*TREAD, (i+1)*TREAD
        top = (i+1) * FLIGHT_RISE / 12
        phase = ((i * .137) % 1.0, (i * .211) % 1.0)
        obj = object_box(f"ClosedStep_{i+1:02d}__TreadAndRiser", (0.0, FLIGHT_WIDTH, y1, y2, 0.0, top),
                         geo, mineral_a, mineral_a_m,
                         dict(tags, segment="closed_tread_riser", step=i+1, top_height_m=top),
                         phase)
        # Approach is from entry y<0: y1 is the tread front/nosing.  The
        # 0.045m strip uses the authored image's top rows (Blender V near 1).
        edge = object_box(f"TreadEdge_{i+1:02d}__TopFront_045m", (0.0, FLIGHT_WIDTH, y1, y1+0.045, top, top+0.002),
                          geo, tread_edge, edge_m, dict(tags, segment="tread_edge", step=i+1,
                          physical_depth_m=0.045, authored_edge_band="image_top"))
        uv = edge.data.uv_layers["UV0"].data
        for loop in edge.data.polygons[1].loop_indices:  # top face only
            vertex = edge.data.vertices[edge.data.loops[loop].vertex_index]
            uv[loop].uv.x = vertex.co.x / edge_m[0]
            uv[loop].uv.y = 1.0 - (vertex.co.y - y1) / edge_m[1]
    object_box("TurnLanding__3p8m_full_width", (*LANDING_X, *TURN_Y, FLIGHT_RISE-0.18, FLIGHT_RISE),
               geo, mineral_a, mineral_a_m, dict(tags, segment="half_turn_landing", omitted_second_flight=True), (.613, .419))
    wall_obj = object_box("RepresentativeLowerLeftWall__R24Reuse", (-0.20, 0.0, -1.8, 1.1, -0.18, 2.72), geo,
               wall, wall_m, dict(tags, segment="representative_lower_backdrop_wall", structural_plan_change=False,
               upper_flight_wall="OMITTED_CUTAWAY"))
    # The inner x=0 face is a one-pass lower-wall crop: source base trim is
    # V=0 at z=-.18 and the protected upper area is never tiled vertically.
    wall_uv = wall_obj.data.uv_layers["UV0"].data
    for loop in wall_obj.data.polygons[3].loop_indices:
        vertex = wall_obj.data.vertices[wall_obj.data.loops[loop].vertex_index]
        wall_uv[loop].uv.x = (vertex.co.y + 1.8) * PIXELS_PER_METRE / 728
        wall_uv[loop].uv.y = (vertex.co.z + 0.18) * PIXELS_PER_METRE / 232

    # Minimal inner rail is intentionally provisional and untextured-detail-free.
    rail_tags = dict(tags, segment="provisional_inner_handrail", final_design=False)
    for y in (0.0, 1.65, 3.3):
        z = (min(y / FLIGHT_RUN, 1.0) * FLIGHT_RISE) + 0.90
        cylinder_between(f"InnerRailPost_{y:.2f}", (FLIGHT_WIDTH-0.08, y, z-0.90),
                         (FLIGHT_WIDTH-0.08, y, z), 0.025, rail, rail_mat, rail_tags)
    cylinder_between("InnerRail__Flight", (FLIGHT_WIDTH-0.08, 0.0, 0.90),
                     (FLIGHT_WIDTH-0.08, FLIGHT_RUN, FLIGHT_RISE+0.90), 0.032, rail, rail_mat, rail_tags)
    cylinder_between("InnerRail__TurnLanding", (FLIGHT_WIDTH-0.08, FLIGHT_RUN, FLIGHT_RISE+0.90),
                     (FLIGHT_WIDTH-0.08, TURN_Y[1], FLIGHT_RISE+0.90), 0.032, rail, rail_mat, rail_tags)

    root["status"] = "MATERIAL_REVIEW_SAMPLE__NO_GODOT_SCENE_OR_LIGHTMAP"
    root["coordinates"] = "x_width__y_run__z_up"
    root["flight_dimensions_m"] = [FLIGHT_WIDTH, FLIGHT_RUN, FLIGHT_RISE]
    root["treads"] = TREADS
    root["uv0_convention"] = "80px_per_m__actual_image_dimensions_are_read_at_build_time"
    root["omitted_geometry"] = "return_flight__roof__fixtures__upper_flight_wall__game_scene"
    for scene in bpy.data.scenes:
        scene.render.engine = 'BLENDER_WORKBENCH'
    BLEND.parent.mkdir(parents=True, exist_ok=True)
    ASSET.mkdir(parents=True, exist_ok=True)
    authored = [mineral_a, mineral_b, tread_edge, wall]
    fallbacks = [mat.name for mat in authored if mat.get("texture_status") != "AUTHORED_INPUT"]
    if fallbacks:
        raise RuntimeError("Final sample requires authored inputs: " + ", ".join(fallbacks))
    step_meshes = [obj.data for obj in bpy.data.objects if obj.get("segment") == "closed_tread_riser"]
    finite_uv = all(math.isfinite(value) for mesh in step_meshes for item in mesh.uv_layers["UV0"].data
                    for value in item.uv)
    closed_steps = all(closed_manifold(mesh) for mesh in step_meshes)
    images = {name: {"pixels": list(bpy.data.images[name].size),
                     "physical_metres": [bpy.data.images[name].size[0] / PIXELS_PER_METRE,
                                         bpy.data.images[name].size[1] / PIXELS_PER_METRE]}
              for name in ("mineral_a.png", "mineral_b.png", "tread_edge.png", "wall_body.png")}
    qa = {
        "schema": "cryo_stair_material_sample_v1_static_qa",
        "status": "STATIC_GEOMETRY_AND_UV_PASS__RUNTIME_UNVERIFIED",
        "scope": "one_rising_flight_entry_and_half_turn_landing__return_flight_roof_upper_wall_game_scene_omitted",
        "coordinates": "x_width__y_run__z_up",
        "dimensions_m": {"flight_width": FLIGHT_WIDTH, "flight_run": FLIGHT_RUN, "flight_rise": FLIGHT_RISE,
                         "treads": TREADS, "tread_depth": TREAD, "entry_landing": [3.8, 1.8],
                         "turn_landing": [3.8, 1.8], "lower_wall_y": [-1.8, 1.1], "lower_wall_z": [-.18, 2.72]},
        "images": images,
        "density_px_per_m": PIXELS_PER_METRE,
        "default_stair_material": mineral_a.name,
        "unassigned_candidate_material": mineral_b.name,
        "uv_phase_policy": {"step": "((index*0.137)%1, (index*0.211)%1)",
                            "entry_landing": [.071, .173], "turn_landing": [.613, .419],
                            "purpose": "deterministic_distinct_phase_without_changing_80px_per_m_density"},
        "fallback_materials": fallbacks,
        "intentionally_untextured": [rail_mat.name],
        "closed_step_meshes": len(step_meshes),
        "closed_step_meshes_manifold": closed_steps,
        "uv0_finite": finite_uv,
        "tread_edge": {"front": "lower_y_y1", "physical_depth_m": .045, "image_top_blender_v": 1.0},
        "wall": {"inner_face": "x=0", "vertical_tiling": False,
                 "u": "(y+1.8)*80/728", "v": "(z+0.18)*80/232"},
    }
    QA.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    # Establish the target blend directory before converting links to relative
    # form, then pack the images so this source remains portable by itself.
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    for filename in ("mineral_a.png", "mineral_b.png", "tread_edge.png", "wall_body.png"):
        image = bpy.data.images[filename]
        image.filepath = "//" + os.path.relpath(ASSET / filename, BLEND.parent).replace("\\", "/")
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(GLB), export_format='GLB', use_selection=False,
                              export_materials='EXPORT', export_texcoords=True,
                              export_normals=True, export_cameras=False, export_lights=False)
    print(f"Built {BLEND} and {GLB}", flush=True)


if __name__ == "__main__":
    build()
