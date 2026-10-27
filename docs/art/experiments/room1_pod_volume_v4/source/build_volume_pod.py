"""Build the minimal physical-volume revision for the Room 1 v4 pod.

This deliberately preserves the approved v4.1 shell, lid, bed, head-window
pane and the frame-60 lid motion.  It adds only a real, separately UVed
window rim / inner seal and a shallow rear housing for the foot display.
Run with Blender 5 from any working directory:

  blender --background --python build_volume_pod.py
"""
from pathlib import Path
import json, struct
import bpy, bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "room1_pixellab_pod_trial_v3" / "room1_pixellab_pod_trial_v3.blend"
TEXTURE_ROOT = ROOT / "textures"
OUT_BLEND = ROOT / "room1_pod_volume_v4.blend"
OUT_ASSETS = ROOT.parents[3] / "assets" / "art" / "room1_pod_volume_v4"

TEXTURES = {
    "lid": ("lid.png", (128, 256)), "shell_side": ("shell_side.png", (256, 80)),
    "shell_end": ("shell_end.png", (128, 80)), "interior": ("interior.png", (128, 256)),
    "mattress": ("mattress.png", (128, 256)), "glass": ("glass.png", (128, 256)),
    "display": ("display.png", (128, 48)), "section": ("section.png", (128, 64)),
}
UV_BY_KEY = {
    "lid": "UV_TRIAL_V3_LID_XY", "shell_side": "UV_TRIAL_V3_SHELL_SIDE",
    "shell_end": "UV_TRIAL_V3_SHELL_END", "interior": "UV_TRIAL_V3_INTERIOR_XY",
    "mattress": "UV_TRIAL_V3_MATTRESS_XY", "glass": "UV_TRIAL_V3_GLASS_XY",
    "display": "UV_SCREEN_0_1", "section": "UV_POD_V4_SECTION",
}
COMPONENTS = {
    "ONE_PIECE_COVER_head_window": ("lid", "interior", "glass"),
    "Reference_led_fixed_shell": ("shell_side", "shell_end", "interior", "section"),
    "Sleeping_surface": ("mattress",), "Foot_info_display_surface": ("display",),
    "pod_v4_window_frame": ("section",), "pod_v4_window_inner_seal": ("section",),
    "pod_v4_display_housing": ("section",), "pod_v4_lid_inner_backing": ("section",),
    "pod_v4_basin_seal_lip": ("section",),
}

def fail(message): raise RuntimeError(message)

def image_material(key):
    filename, expected_size = TEXTURES[key]
    path = TEXTURE_ROOT / filename
    if not path.is_file(): fail(f"Missing final v4 texture: {path}")
    image = bpy.data.images.load(str(path), check_existing=False)
    if tuple(image.size) != expected_size: fail(f"Unexpected {filename} size {tuple(image.size)}")
    image.colorspace_settings.name = "sRGB"; image.pack()
    mat = bpy.data.materials.new("POD_V4_" + key); mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links; nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial"); bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    tex = nodes.new("ShaderNodeTexImage"); tex.image = image; tex.interpolation = "Closest"; tex.extension = "EXTEND"
    uv = nodes.new("ShaderNodeUVMap"); uv.uv_map = UV_BY_KEY[key]
    bsdf.inputs["Roughness"].default_value = .82 if key != "glass" else .28
    bsdf.inputs["Specular IOR Level"].default_value = .12 if key != "glass" else .35
    links.new(uv.outputs["UV"], tex.inputs["Vector"]); links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if key == "glass":
        links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        if hasattr(mat, "surface_render_method"): mat.surface_render_method = "DITHERED"
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mat["pod_v4_texture_key"] = key; mat["pod_v4_uv"] = UV_BY_KEY[key]
    return mat

def material_key(material):
    name = material.name.lower() if material else ""
    for key in TEXTURES:
        if ("_" + key + "_") in name or name.endswith("_" + key): return key
    return None

def set_v4_materials(materials):
    for obj_name in ("ONE_PIECE_COVER_head_window", "Reference_led_fixed_shell", "Sleeping_surface", "Foot_info_display_surface"):
        obj = bpy.data.objects.get(obj_name)
        if not obj: fail("Missing source object " + obj_name)
        for index, old in enumerate(obj.data.materials):
            key = material_key(old)
            if key and key in materials: obj.data.materials[index] = materials[key]

def orient_head_end_uv():
    """Mirror only the positive-Y (head) end so shared 12 reads correctly.

    The source end atlas uses U=X for both ends.  It reads correctly looking
    toward +Y at the foot/display end, but reverses when viewed outward from
    the +Y head end.  Reversing head-end U leaves the foot's already-readable
    12 untouched and does not alter the shared PNG.
    """
    shell=bpy.data.objects['Reference_led_fixed_shell']; mesh=shell.data
    uv=mesh.uv_layers.get(UV_BY_KEY['shell_end'])
    if not uv: fail('Fixed shell lacks shell-end UV')
    changed=0
    for poly in mesh.polygons:
        mat=mesh.materials[poly.material_index]
        if mat and mat.name=='POD_V4_shell_end' and poly.center.y>0:
            for li in poly.loop_indices: uv.data[li].uv.x=1.0-uv.data[li].uv.x
            changed+=1
    if changed==0: fail('No positive-Y head end faces received UV orientation')
    return changed

def section_uv(mesh):
    layer = mesh.uv_layers.get(UV_BY_KEY["section"]) or mesh.uv_layers.new(name=UV_BY_KEY["section"])
    # Per polygon, U is local edge length direction and V is a deliberately
    # narrow 8px atlas band (roughly 0.35..0.47 in the 64px map).  The added
    # 14–38mm sections must read as a few broad pixel value steps, not as a
    # 64px strip compressed into a hairline.  This also avoids projecting
    # vertical faces into a collapsed XY texture line.
    for poly in mesh.polygons:
        n = len(poly.loop_indices)
        for j, li in enumerate(poly.loop_indices):
            layer.data[li].uv = ((.08 if j in (0, 3) else .92), (.35 if j < 2 else .47))
    return layer

def mesh_object(name, vertices, faces, parent, material):
    mesh = bpy.data.meshes.new(name + "_mesh"); mesh.from_pydata(vertices, [], faces); mesh.update()
    # `from_pydata` preserves caller winding.  Make every new closed volume
    # consistently outward instead of relying on the boundary-loop direction.
    bm=bmesh.new(); bm.from_mesh(mesh); bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.to_mesh(mesh); bm.free()
    mesh.materials.append(material); section_uv(mesh)
    obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj)
    # Vertices are authored in the named parent's local coordinate space.
    # Keep the child local transform at identity so lid additions inherit the
    # existing lift/side-slide/45-degree motion instead of cancelling it with
    # a parent-inverse compensation matrix.
    obj.parent = parent
    return obj

def boundary_loop(mesh, face_indices):
    wanted = set(face_indices); counts = {}
    for fi in wanted:
        for a, b in mesh.polygons[fi].edge_keys:
            k = tuple(sorted((a, b))); counts[k] = counts.get(k, 0) + 1
    edges = [edge for edge, count in counts.items() if count == 1]
    if not edges: fail("Could not derive head-window outer boundary")
    nexts = {}
    for a, b in edges: nexts.setdefault(a, []).append(b); nexts.setdefault(b, []).append(a)
    start = min(nexts); loop, previous, current = [start], None, start
    while True:
        choices = [v for v in nexts[current] if v != previous]
        nxt = choices[0]
        if nxt == start: break
        loop.append(nxt); previous, current = current, nxt
        if len(loop) > len(edges) + 1: fail("Invalid head-window boundary loop")
    return [mesh.vertices[index].co.copy() for index in loop]

def scaled(points, centre, amount): return [centre + (point - centre) * amount for point in points]

def ring_volume(name, outer, inner, z_shift_top, depth, parent, material):
    """A closed thin rim inside the existing window contour; no silhouette growth."""
    n = len(outer); top_outer = [Vector((p.x, p.y, p.z + z_shift_top)) for p in outer]
    top_inner = [Vector((p.x, p.y, p.z + z_shift_top)) for p in inner]
    bottom_outer = [p - Vector((0,0,depth)) for p in top_outer]
    bottom_inner = [p - Vector((0,0,depth)) for p in top_inner]
    verts = top_outer + top_inner + bottom_outer + bottom_inner; faces=[]
    for i in range(n):
        j=(i+1)%n
        faces += [(i,j,n+j,n+i), (2*n+i,3*n+i,3*n+j,2*n+j),
                  (i,2*n+i,2*n+j,j), (n+i,n+j,3*n+j,3*n+i)]
    return mesh_object(name, verts, faces, parent, material)

def add_window_frame(material):
    lid = bpy.data.objects["ONE_PIECE_COVER_head_window"]; mesh=lid.data
    # Evidence-authoritative outer pane polygons.  The original 8.6–11.7mm
    # two-sided glass is deliberately untouched.
    outer = boundary_loop(mesh, [58,59,60,61,62]); centre=sum(outer, Vector()) / len(outer)
    # Both rims stay inward from the pane perimeter so closed external bounds
    # remain unchanged.  A 42mm visual rim and a deeper 28mm inner shoulder.
    top_inner = scaled(outer, centre, .900)
    ring_volume("pod_v4_window_frame", outer, top_inner, .004, .018, lid.parent, material)
    seal_outer = scaled(outer, centre, .895); seal_inner = scaled(outer, centre, .835)
    ring_volume("pod_v4_window_inner_seal", seal_outer, seal_inner, -.019, .014, lid.parent, material)

def add_display_housing(material):
    shell=bpy.data.objects["Reference_led_fixed_shell"]; display=bpy.data.objects["Foot_info_display_surface"]
    world = [display.matrix_world @ v.co for v in display.data.vertices]
    center=sum(world, Vector())/4; normal=(world[1]-world[0]).cross(world[2]-world[0]).normalized()
    # Select the normal pointing into the fixed shell, so the housing never
    # protrudes from the approved exterior outline.
    shell_center=shell.matrix_world.translation
    if (center + normal*.04 - shell_center).length > (center - normal*.04 - shell_center).length: normal.negate()
    # local display plane axes; order-independent dimensions from x horizontal
    axis_u=Vector((1,0,0)); axis_u=(axis_u-normal*axis_u.dot(normal)).normalized(); axis_v=normal.cross(axis_u).normalized()
    screen_u=max(abs((p-center).dot(axis_u)) for p in world); screen_v=max(abs((p-center).dot(axis_v)) for p in world)
    # The bezel surrounds rather than covers the pre-existing LCD plane.  The
    # front opening is 2mm larger than the screen in both axes; the new tray
    # retreats inward after a 1mm raised outer bezel.
    outer_u,outer_v=screen_u+.012,screen_v+.012; inner_u,inner_v=screen_u+.002,screen_v+.002
    signs=((-1,-1),(1,-1),(1,1),(-1,1)); front_outer=[center+sx*outer_u*axis_u+sy*outer_v*axis_v-normal*.001 for sx,sy in signs]
    front_inner=[center+sx*inner_u*axis_u+sy*inner_v*axis_v-normal*.001 for sx,sy in signs]
    back_outer=[p+normal*.038 for p in front_outer]; back_inner=[p+normal*.038 for p in front_inner]
    verts=[shell.matrix_world.inverted()@p for p in front_outer+front_inner+back_outer+back_inner]
    faces=[]
    for i in range(4):
        j=(i+1)%4
        faces += [(i,j,4+j,4+i), (i,8+i,8+j,j), (4+i,4+j,12+j,12+i), (8+i,12+i,12+j,8+j)]
    faces += [(12,13,14,15)]
    mesh_object("pod_v4_display_housing", verts, faces, shell, material)

def append_box(vertices, faces, minimum, maximum):
    base=len(vertices); x0,y0,z0=minimum; x1,y1,z1=maximum
    vertices += [Vector((x0,y0,z0)),Vector((x1,y0,z0)),Vector((x1,y1,z0)),Vector((x0,y1,z0)),Vector((x0,y0,z1)),Vector((x1,y0,z1)),Vector((x1,y1,z1)),Vector((x0,y1,z1))]
    faces += [(base,base+3,base+2,base+1),(base+4,base+5,base+6,base+7),(base,base+1,base+5,base+4),(base+1,base+2,base+6,base+5),(base+2,base+3,base+7,base+6),(base+3,base,base+4,base+7)]

def add_lid_inner_backing(material):
    """Closed 28mm backing fitted to source inner face 117, not guessed box."""
    lid=bpy.data.objects['ONE_PIECE_COVER_head_window']; face=lid.data.polygons[117]
    if face.normal.z>-.99 or len(face.vertices)!=4: fail('Cover face 117 no longer matches the measured inner centre plane')
    source=[lid.data.vertices[i].co.copy() for i in face.vertices]; centre=sum(source,Vector())/len(source)
    # 6% radial inset retains a 16mm lateral margin and 33mm longitudinal
    # margin inside the actual supporting polygon, so no rail crosses the
    # sloped cover side.  The top embeds 1mm into the cover material (opposite
    # the inward-facing normal); depth then follows the inward (-Z) normal,
    # eliminating the former 6mm air gap.
    top=[centre+(v-centre)*.94-face.normal.normalized()*.001 for v in source]
    bottom=[v+face.normal.normalized()*.028 for v in top]; n=len(top)
    verts=top+bottom; faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    for i in range(n):
        j=(i+1)%n; faces.append((i,j,n+j,n+i))
    obj=mesh_object('pod_v4_lid_inner_backing',verts,faces,lid.parent,material)
    obj['source_inner_face']=117; obj['inset_factor']=.94; obj['support_contact_offset_m']=-.001; obj['inward_depth_m']=.028
    return {'source_face':117,'source_vertices_m':[[round(c,6) for c in v] for v in source],'top_vertices_m':[[round(c,6) for c in v] for v in top],'inset_factor':.94,'inward_depth_m':.028}

def add_basin_seal_lip(material):
    """Closed inner shoulder embedded into the actual source opening rim."""
    shell=bpy.data.objects['Reference_led_fixed_shell']; source_indices=(32,33,34,35,36,37,38,39)
    outer=[shell.data.vertices[i].co.copy() for i in source_indices]
    if any(abs(v.z-.345)>1e-5 for v in outer): fail('Source opening rim height changed')
    centre=sum(outer,Vector())/len(outer)
    # The source rim's long sides are x=±.465; a 20mm radial inset leaves the
    # bed's x±.44/y±.955 footprint clear.  25mm downward slope gives a visible
    # ~32mm section while the outer top embeds 2mm into original rim geometry.
    inner=[]
    for v in outer:
        radial=v-centre; radial.z=0.0; inner.append(v-radial.normalized()*.020-Vector((0,0,.025)))
    outer_embedded=[v-Vector((0,0,.002)) for v in outer]
    outer_bottom=[v-Vector((0,0,.017)) for v in outer_embedded]
    inner_bottom=[v-Vector((0,0,.015)) for v in inner]
    n=len(outer); verts=outer_embedded+inner+outer_bottom+inner_bottom; faces=[]
    for i in range(n):
        j=(i+1)%n
        faces += [(i,j,n+j,n+i),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i),(2*n+i,3*n+i,3*n+j,2*n+j)]
    obj=mesh_object('pod_v4_basin_seal_lip',verts,faces,shell,material)
    obj['source_rim_indices']=list(source_indices); obj['outer_embed_m']=.002; obj['radial_inset_m']=.020; obj['inner_drop_m']=.025
    return {'source_rim_vertex_indices':list(source_indices),'outer_embed_m':.002,'radial_inset_m':.020,'inner_drop_m':.025}

def triangle_uv_area(a,b,c):
    return abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))/2

def repair_degenerate_shell_interior(material):
    """Give only zero-area vertical interior faces an X×Z section map.

    The v3 interior XY mapping is retained for every usable source face.  The
    fixed shell has two constant-Y vertical inner faces (polygons 85/86), so
    their original XY UV collapses to a line.  They are the only source
    surfaces reclassified here; a whole-shell remap would destroy approved
    side/end UV.
    """
    shell=bpy.data.objects['Reference_led_fixed_shell']; mesh=shell.data
    old_uv=mesh.uv_layers.get(UV_BY_KEY['interior'])
    if not old_uv: fail('Fixed shell lacks original interior UV')
    section_uv_layer=mesh.uv_layers.get(UV_BY_KEY['section']) or mesh.uv_layers.new(name=UV_BY_KEY['section'])
    if material.name not in [m.name for m in mesh.materials]: mesh.materials.append(material)
    section_index=next(i for i,m in enumerate(mesh.materials) if m==material)
    changed=[]
    for poly in mesh.polygons:
        current=mesh.materials[poly.material_index]
        if current != material and (not current or current.name!='POD_V4_interior'): continue
        loops=list(poly.loop_indices); collapsed=False
        for i in range(1,len(loops)-1):
            if triangle_uv_area(old_uv.data[loops[0]].uv,old_uv.data[loops[i]].uv,old_uv.data[loops[i+1]].uv)<1e-10:
                collapsed=True; break
        if not collapsed: continue
        coords=[mesh.vertices[mesh.loops[li].vertex_index].co for li in loops]
        min_x,max_x=min(v.x for v in coords),max(v.x for v in coords); min_z,max_z=min(v.z for v in coords),max(v.z for v in coords)
        if max_x-min_x<1e-7 or max_z-min_z<1e-7: fail(f'Cannot give usable XZ UV to shell interior polygon {poly.index}')
        for li,co in zip(loops,coords):
            # This is a relatively tall inner wall, so it uses most of the
            # 64px section texture rather than the 8px narrow-seal atlas band.
            section_uv_layer.data[li].uv=(.08+.84*(co.x-min_x)/(max_x-min_x), .08+.84*(co.z-min_z)/(max_z-min_z))
        poly.material_index=section_index; changed.append(poly.index)
    if changed != [85, 86]: fail(f'Unexpected degenerate shell-interior set: {changed}')
    return changed

def is_exportable(obj): return obj.name in COMPONENTS and obj.type == "MESH"

def keep_only_uv(mesh, name):
    if not mesh.uv_layers.get(name): fail(f"{mesh.name} lacks required {name}")
    for other in [uv.name for uv in mesh.uv_layers if uv.name != name]: mesh.uv_layers.remove(mesh.uv_layers[other])
    mesh.uv_layers.active=mesh.uv_layers[name]

def export_piece(obj, key, mat, depsgraph):
    evaluated=obj.evaluated_get(depsgraph); mesh=bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph, preserve_all_data_layers=True)
    # Generated section objects are one-material; source objects are split by actual slots.
    wanted=[p.index for p in mesh.polygons if material_key(mesh.materials[p.material_index]) == key]
    if not wanted: bpy.data.meshes.remove(mesh); return None
    bm=bmesh.new(); bm.from_mesh(mesh); bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in wanted], context="FACES"); bm.to_mesh(mesh); bm.free()
    keep_only_uv(mesh, UV_BY_KEY[key]); mesh.materials.clear(); mesh.materials.append(mat)
    for p in mesh.polygons: p.material_index=0
    piece=bpy.data.objects.new("pod_v4_"+key, mesh); bpy.context.scene.collection.objects.link(piece); piece.matrix_world=evaluated.matrix_world.copy(); return piece

def bounds(objects):
    pts=[obj.matrix_world@Vector(c) for obj in objects for c in obj.bound_box]
    return {"min_m":[round(min(p[i] for p in pts),6) for i in range(3)],"max_m":[round(max(p[i] for p in pts),6) for i in range(3)]}

def glb_json(path):
    with path.open("rb") as f:
        magic,version,_=struct.unpack("<4sII",f.read(12)); size,kind=struct.unpack("<I4s",f.read(8)); data=f.read(size)
    if magic!=b"glTF" or version!=2 or kind!=b"JSON": fail(f"Bad GLB {path}")
    return json.loads(data.decode("utf8").rstrip(" \0\t\r\n"))

def export_state(name, frame, materials):
    scene=bpy.context.scene; scene.frame_set(frame); dg=bpy.context.evaluated_depsgraph_get(); pieces=[]
    for obj in [o for o in bpy.data.objects if is_exportable(o)]:
        for key in COMPONENTS[obj.name]:
            piece=export_piece(obj,key,materials[key],dg)
            if piece: pieces.append(piece)
    for obj in bpy.context.selected_objects: obj.select_set(False)
    for obj in pieces: obj.select_set(True)
    bpy.context.view_layer.objects.active=pieces[0]
    output=OUT_ASSETS/("pod_closed_v4.glb" if name=="closed" else "pod_open_v4.glb")
    bpy.ops.export_scene.gltf(filepath=str(output), export_format="GLB", use_selection=True, export_texcoords=True, export_normals=True, export_materials="EXPORT", export_image_format="AUTO", export_cameras=False, export_lights=False, export_animations=False, export_yup=True, export_apply=False, export_unused_images=False, export_unused_textures=False)
    record={"file":output.name,"frame":frame,"bounds_m":bounds(pieces),"objects":[p.name for p in pieces]}
    for piece in pieces: bpy.data.objects.remove(piece,do_unlink=True)
    data=glb_json(output); prim=[p for m in data.get("meshes",[]) for p in m.get("primitives",[])]
    if not prim or any("TEXCOORD_0" not in p.get("attributes",{}) for p in prim): fail(output.name+" missing TEXCOORD_0")
    record.update({"primitive_count":len(prim),"material_names":[m.get("name") for m in data.get("materials",[])],"embedded_images":all("bufferView" in i for i in data.get("images",[]))})
    return record

def mesh_report(obj):
    edge_counts={}
    for poly in obj.data.polygons:
        for e in poly.edge_keys: edge_counts[tuple(sorted(e))]=edge_counts.get(tuple(sorted(e)),0)+1
    uv=obj.data.uv_layers.get(UV_BY_KEY["section"]); areas=[]
    if uv:
        for p in obj.data.polygons:
            u=[uv.data[i].uv for i in p.loop_indices]; areas.append(abs(sum(u[i].x*u[(i+1)%len(u)].y-u[(i+1)%len(u)].x*u[i].y for i in range(len(u)))*.5))
    return {"vertices":len(obj.data.vertices),"polygons":len(obj.data.polygons),"boundary_edges":sum(v==1 for v in edge_counts.values()),"uv_area_min":round(min(areas),6) if areas else None,"uv_area_max":round(max(areas),6) if areas else None}

def main():
    if not SOURCE.is_file(): fail("Missing source blend "+str(SOURCE))
    OUT_ASSETS.mkdir(parents=True,exist_ok=True); bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); bpy.context.scene.frame_set(1)
    materials={key:image_material(key) for key in TEXTURES}; set_v4_materials(materials)
    head_end_uv_faces=orient_head_end_uv()
    add_window_frame(materials["section"]); add_display_housing(materials["section"])
    backing_fit=add_lid_inner_backing(materials["section"]); basin_fit=add_basin_seal_lip(materials["section"])
    repaired_shell_faces=repair_degenerate_shell_interior(materials["section"])
    # Explicitly preserve source motion hierarchy for both added lid features.
    lid_parent=bpy.data.objects.get("Whole_lid_motion")
    if bpy.data.objects["pod_v4_window_frame"].parent != lid_parent or bpy.data.objects["pod_v4_window_inner_seal"].parent != lid_parent: fail("Lid additions lost motion parent")
    bpy.context.scene["pod_v4_geometry_scope"]="Minimal physical rim/seal + display housing. Existing shell/lid/bed/pane topology and frame-60 motion retained."
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
    reports={name:mesh_report(bpy.data.objects[name]) for name in ("pod_v4_window_frame","pod_v4_window_inner_seal","pod_v4_display_housing","pod_v4_lid_inner_backing","pod_v4_basin_seal_lip")}
    component_map={name:{"texture_keys":list(keys),"uv_layers":[UV_BY_KEY[key] for key in keys],"notes":("Existing GLASS_UV range retained; source pane is an 8.6–11.7mm two-sided shell." if name=="ONE_PIECE_COVER_head_window" else "New physically closed section component; section uses the narrow 8px V atlas band." if name.startswith("pod_v4_") else "Existing source geometry; only material replacement and export splitting.")} for name,keys in COMPONENTS.items()}
    result={"source":str(SOURCE),"additions":{"window_rim_width_m":.042,"window_rim_depth_m":.018,"inner_seal_depth_m":.014,"display_housing_depth_m":.038,"lid_inner_backing_depth_m":.028,"basin_lip_radial_inset_m":.020,"basin_lip_vertical_drop_m":.025},"existing_glass_preserved":{"outer_faces":[58,59,60,61,62],"inner_faces":[148,149,150,151,152],"uv":"UV_TRIAL_V3_GLASS_XY"},"source_uv_repair":{"fixed_shell_polygon_reclassified_to_section":repaired_shell_faces,"reason":"original planar XY UV creates 24 zero-area fan triangles on the two constant-Y vertical interior faces; replacement uses X×Z section UV."},"source_fit":{"lid_inner_backing":backing_fit,"basin_seal_lip":basin_fit,"head_end_shell_end_uv_flipped_faces":head_end_uv_faces},"new_meshes":reports,"exports":[export_state("closed",1,materials),export_state("open",60,materials)]}
    (ROOT/"source"/"geometry_volume_readback.json").write_text(json.dumps(result,indent=2),encoding="utf8")
    (ROOT/"source"/"geometry_components.json").write_text(json.dumps({"materials":{key:{"material":"POD_V4_"+key,"texture":TEXTURES[key][0],"uv_layer":UV_BY_KEY[key]} for key in TEXTURES},"components":component_map,"export_policy":"Each GLB primitive is material-split and retains exactly its named active UV as TEXCOORD_0."},indent=2),encoding="utf8")

if __name__ == "__main__": main()
