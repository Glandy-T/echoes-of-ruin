"""Original single-pod silhouette revision; reference image is visual guidance only.
Blender 5.0.1: --background --factory-startup --python build_pod.py
No third-party mesh or engineering CAD is imported. Static form review only.
"""
import bpy
import bmesh
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'evidence'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1440
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = -.3
scene.world = bpy.data.worlds.new('Neutral_review_world')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.14,.17,.19,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .45

def collection(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c

design = collection('01_ORIGINAL_FORM_v3_PENDING_REVIEW')
review = collection('02_REVIEW_STAGE_ONLY')

def material(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color,1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color,1)
    bsdf.inputs['Roughness'].default_value = .92
    bsdf.inputs['Specular IOR Level'].default_value = .12
    return m

shellmat = material('PLAIN_shell_color_NOT_APPROVED',(.49,.56,.55))
innermat = material('PLAIN_inner_liner',(.27,.34,.36))
lidmat = material('PLAIN_single_rigid_cover',(.63,.67,.62))
windowmat = material('HEAD_WINDOW_area_ONLY_opaque_review',(.17,.33,.38))
bedmat = material('PLAIN_interior_support',(.38,.43,.44))
groundmat = material('REVIEW_floor',(.12,.16,.18))
linemat = material('REVIEW_envelope_mark',(.35,.47,.48))

def mesh_obj(name, verts, faces, mats):
    mesh = bpy.data.meshes.new(name+'_Mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    design.objects.link(obj)
    for m in mats:
        mesh.materials.append(m)
    for face in mesh.polygons:
        face.use_smooth = False
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    obj['status'] = 'STATIC SILHOUETTE CANDIDATE / USER REVIEW REQUIRED'
    return obj

def ring(width, length, z, cut):
    # Eight straight edges: broad sides/ends, one modest bevel at each corner.
    w, d = width/2, length/2
    return [(w-cut,-d,z),(w,-d+cut,z),(w,d-cut,z),(w-cut,d,z),
            (-w+cut,d,z),(-w,d-cut,z),(-w,-d+cut,z),(-w+cut,-d,z)]

outer = [ring(.89,2.10,0,.10),ring(1.05,2.30,.12,.14),
         ring(1.05,2.30,.55,.14),ring(.96,2.16,.74,.12)]
inner_top = ring(.82,2.01,.74,.10)
inner_bottom = ring(.76,1.94,.37,.09)
N = 8
verts = [p for row in outer+[inner_top,inner_bottom] for p in row]
faces = [tuple(reversed(range(N)))]
for j in range(5):
    for i in range(N):
        nxt = (i+1)%N
        faces.append((j*N+i,j*N+nxt,(j+1)*N+nxt,(j+1)*N+i))
faces.append(tuple(range(5*N,6*N)))
body = mesh_obj('Original_planar_shell',verts,faces,[shellmat,innermat,shellmat,innermat])
for p in body.data.polygons:
    if p.index == 0:
        p.material_index = 3
    elif 1+3*N <= p.index < 1+4*N:
        p.material_index = 2
    elif p.index >= 1+4*N:
        p.material_index = 1

rows = [ring(.72,1.88,.375,.09),ring(.75,1.91,.43,.10)]
verts = [p for row in rows for p in row]
faces = [tuple(reversed(range(N))),tuple(range(N,2*N))]
faces += [(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
bed = mesh_obj('Plain_interior_support',verts,faces,[bedmat])

# Broad planar roof, a sloped shoulder on each side, small edge bevels.
# Longitudinal shape is straight; short flat end transitions replace round caps.
cross_section = [(-.48,.77),(-.435,.85),(-.32,.98),(-.29,1),
                 (.29,1),(.32,.98),(.435,.85),(.48,.77)]
stations = [(-1.08,.82,.82),(-.96,1,1),(.48,1,1),(.94,1,1),(1.08,.82,.82)]
verts = [(x*width,y,.77+(z-.77)*height)
         for y,width,height in stations for x,z in cross_section]
faces, glass = [], []
for j in range(len(stations)-1):
    for i in range(N-1):
        a = j*N+i
        faces.append((a,a+1,a+1+N,a+N))
        if j == 2 and 2 <= i <= 4:
            glass.append(len(faces)-1)
faces += [tuple(reversed(range(N))),tuple(range(4*N,5*N))]
lid = mesh_obj('ONE_RIGID_LID_head_window',verts,faces,[lidmat,windowmat,innermat,windowmat])
for i in glass:
    lid.data.polygons[i].material_index = 1
bpy.context.view_layer.objects.active = lid
lid.select_set(True)
solid = lid.modifiers.new('One_piece_cover_wall_0p022m','SOLIDIFY')
solid.thickness = .022
solid.offset = -1
solid.material_offset = 2
solid.material_offset_rim = 2
bpy.ops.object.modifier_apply(modifier=solid.name)
lid['whole_lid_requirement'] = 'single rigid lid; lift then side-slide/down motion retained as intent; animation deferred until silhouette approval'
lid['window_region'] = 'head only: +Y .48 to .94; opaque blue review marker, not a glass shader'
body['closed_design_envelope_m'] = '1.05 W x 2.30 L x 1.00 H including lid'

# Preliminary seams follow structural plane changes and window boundaries.
# Packing, paint-map orientation and texel density await approved silhouette.
for obj in (body,bed,lid):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for e in bm.edges:
        e.seam = (len({f.material_index for f in e.link_faces})>1
                  or any(len(f.verts)>4 for f in e.link_faces)
                  or (e.is_manifold and e.calc_face_angle()>math.radians(35)))
    bm.to_mesh(obj.data)
    bm.free()
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    obj.data.uv_layers.new(name='UV_DRAFT_pending_form_approval')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED',margin=.025)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj['UV_status'] = 'DRAFT only; final paint layout and distortion review deferred until form approval'

def box(name,lo,size,mat):
    bpy.ops.mesh.primitive_cube_add(size=1,location=Vector(lo)+Vector(size)/2)
    o = bpy.context.object
    o.name = name
    o.dimensions = size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for col in list(o.users_collection):
        col.objects.unlink(o)
    review.objects.link(o)
    o.data.materials.append(mat)
    return o

box('REVIEW_FLOOR_not_room_design',(-1.8,-1.7,-.035),(3.2,3.4,.035),groundmat)
box('REVIEW_next_pod_near_edge_0p70_gap',(1.225,-1.35,.001),(.009,2.7,.003),linemat)
box('REVIEW_original_closed_side_edge',(.525,-1.35,.001),(.006,2.7,.003),linemat)
data = bpy.data.cameras.new('Camera_MATCH_v2')
data.type = 'ORTHO'
data.ortho_scale = 3.8
cam = bpy.data.objects.new('Camera_MATCH_v2',data)
review.objects.link(cam)
target = Vector((.13,0,.48))
cam.location = target + Vector((-4,-5,3.5))
cam.rotation_euler = (target-cam.location).to_track_quat('-Z','Y').to_euler()
scene.camera = cam
for name,location,energy,size in [('Key',(-3,-4,6),480,4),('Fill',(3,2,4),280,3)]:
    data = bpy.data.lights.new(name,'AREA')
    data.energy, data.size = energy, size
    obj = bpy.data.objects.new(name,data)
    review.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector((0,0,.5))-obj.location).to_track_quat('-Z','Y').to_euler()

scene['design_stage'] = 'v3 STATIC FORM REVIEW / final UV and motion on hold pending silhouette review'
scene['reference'] = 'User screenshot Scifi - Cryogenic Sleep: straight side walls, flat roof and restrained chamfered shoulders; original mesh not imported'
scene['scope'] = 'one pod only; no room, CAD or Godot scene modified'
scene.render.filepath = str(OUT/'01_closed.png')
bpy.ops.render.render(write_still=True)
scene.render.filepath = '//evidence/01_closed.png'
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
bpy.context.view_layer.objects.active = body
for area in bpy.context.screen.areas if bpy.context.screen else []:
    if area.type == 'VIEW_3D':
        area.spaces.active.region_3d.view_perspective = 'CAMERA'
        area.spaces.active.shading.type = 'MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'room1_pod_form_v3.blend'))
print('SAVED_FORM_v3',ROOT)
