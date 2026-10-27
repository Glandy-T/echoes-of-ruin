"""Original low-poly cryopod silhouette / one-piece lid motion candidate.
No third-party model, CAD model, topology or v1/v2 art mesh is imported.
Blender 5.0.1: --background --factory-startup --python-exit-code 1 --python this.py
"""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'evidence'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1440
scene.render.resolution_y=1000
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.fps=24
scene.frame_start=1
scene.frame_end=108
scene.view_settings.view_transform='Standard'
scene.view_settings.look='None'
scene.view_settings.exposure=-.3
scene.world=bpy.data.worlds.new('Neutral_review_world')
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.14,.17,.19,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45

def collection(name):
    result=bpy.data.collections.new(name)
    scene.collection.children.link(result)
    return result
design=collection('01_ORIGINAL_POD_SILHOUETTE_CANDIDATE')
motion=collection('02_ONE_PIECE_LID_ANIMATED')
review=collection('03_REVIEW_ONLY')
def mat(name,color):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    node=m.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value=(*color,1)
    node.inputs['Roughness'].default_value=.92
    node.inputs['Specular IOR Level'].default_value=.12
    return m
shellmat=mat('PLAIN_shell_color_NOT_APPROVED',(.49,.56,.55))
innermat=mat('PLAIN_inner_liner',(.27,.34,.36))
lidmat=mat('PLAIN_single_rigid_cover',(.63,.67,.62))
windowmat=mat('HEAD_WINDOW_area_only_OPAQUE_REVIEW',(.17,.33,.38))
bedmat=mat('PLAIN_interior_support',(.38,.43,.44))
groundmat=mat('REVIEW_floor',(.12,.16,.18))
linemat=mat('REVIEW_envelope_mark',(.35,.47,.48))

def mesh_obj(name,verts,faces,col,materials):
    data=bpy.data.meshes.new(name+'_Mesh')
    data.from_pydata(verts,[],faces)
    data.update()
    obj=bpy.data.objects.new(name,data)
    col.objects.link(obj)
    for m in materials:
        data.materials.append(m)
    uv=data.uv_layers.new(name='UV_provisional_face_projection')
    for p in data.polygons:
        axis=max(range(3),key=lambda i:abs(p.normal[i]))
        a,b=[(1,2),(0,2),(0,1)][axis]
        for li in p.loop_indices:
            co=data.vertices[data.loops[li].vertex_index].co
            uv.data[li].uv=(co[a],co[b])
    obj['status']='USER_REVIEW_REQUIRED / original silhouette, not approved product design'
    return obj

def ring(width,length,z,cut):
    w,d=width/2,length/2
    return [(-w+cut,-d,z),(w-cut,-d,z),(w,-d+cut,z),(w,d-cut,z),
            (w-cut,d,z),(-w+cut,d,z),(-w,d-cut,z),(-w,-d+cut,z)]

# Single continuous basin: foot/base taper into broad shoulders; no stacked boxes.
outer=[ring(.90,2.02,0,.11),ring(1.00,2.23,.10,.13),
       ring(1.05,2.30,.55,.14),ring(1.03,2.27,.74,.14)]
inner_top=ring(.87,2.07,.74,.12)
inner_bottom=ring(.80,1.98,.33,.12)
verts=[v for r in outer+[inner_top,inner_bottom] for v in r]
faces=[tuple(reversed(range(8)))]
for j in range(3):
    for i in range(8):
        nxt=(i+1)%8
        faces.append((j*8+i,j*8+nxt,(j+1)*8+nxt,(j+1)*8+i))
for i in range(8):
    nxt=(i+1)%8
    faces.append((24+i,24+nxt,32+nxt,32+i))
for i in range(8):
    nxt=(i+1)%8
    faces.append((32+i,32+nxt,40+nxt,40+i))
faces.append(tuple(range(40,48)))
body=mesh_obj('Original_continuous_shell',verts,faces,design,[shellmat,innermat])
for p in body.data.polygons:
    if p.index>=33:
        p.material_index=1
body['external_closed_envelope_m']='1.05 W x 2.30 L x 1.00 H including lid'
body['engineering_placement_reference']='P11 min (1.25,6.50,0); prototype local center (0,0,0) maps to (1.775,7.65,0)'

# Simple fitted sleeping surface; no character, harness, pillow or medical equipment.
rings=[ring(.77,1.95,.335,.10),ring(.77,1.95,.42,.10)]
verts=[v for r in rings for v in r]
faces=[tuple(reversed(range(8))),tuple(range(8,16))]
faces += [(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
bed=mesh_obj('Plain_interior_support',verts,faces,design,[bedmat])

# Whole rigid cover. Head window is a face material region of the SAME mesh.
# z values are world-closed values minus the animation reference height .53.
xs=[-.50,-.41,-.26,0,.26,.41,.50]
zs=[.77,.88,.97,1.00,.97,.88,.77]
stations=[(-1.08,.88),(-.96,1.0),(.50,1.0),(.96,1.0),(1.08,.88)]
verts=[(x*factor,y,z-.53) for y,factor in stations for x,z in zip(xs,zs)]
faces=[]
glass_faces=[]
for j in range(len(stations)-1):
    for i in range(len(xs)-1):
        a=j*len(xs)+i
        faces.append((a,a+1,a+1+len(xs),a+len(xs)))
        if j==2 and 1<=i<=4:
            glass_faces.append(len(faces)-1)
faces.append(tuple(reversed(range(7))))
faces.append(tuple(range(28,35)))
lid=mesh_obj('ONE_RIGID_LID_with_head_window',verts,faces,motion,[lidmat,windowmat])
for index in glass_faces:
    lid.data.polygons[index].material_index=1
# End cheeks belong to the same rigid cover and seal its front/rear arch.
# Outward normals: front row is +Y before reversing, rear row is -Y.
import bmesh
bm=bmesh.new()
bm.from_mesh(lid.data)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(lid.data)
bm.free()
bpy.context.view_layer.objects.active=lid
lid.select_set(True)
solid=lid.modifiers.new('Cover_wall_thickness_0p022m','SOLIDIFY')
solid.thickness=.022
solid.offset=-1
bpy.ops.object.modifier_apply(modifier=solid.name)
lid['window_region']='head only, +Y .50 to .96 m; .82 m transverse width; opaque color used for review'
lid['motion']='one rigid assembly; lift then translate/rotate down +X side; no folding or split'

# A geometric motion hypothesis, NOT a manufactured rail/linkage design.
controller=bpy.data.objects.new('LID_MOTION_RIG_whole_cover',None)
motion.objects.link(controller)
controller.empty_display_type='ARROWS'
controller.empty_display_size=.2
lid.parent=controller
poses=[]
for frame in range(1,109):
    if frame<=12:
        angle=0
        rise=0
        side=0
    elif frame<=30:
        t=(frame-12)/18
        angle=0
        rise=.12*t
        side=0
    else:
        t=min(1,(frame-30)/60)
        angle=math.pi*.5*t
        rise=.12*math.cos(angle)
        # Slight outward guide excursion clears the integral end cheeks.
        side=.32*math.sin(angle)+.085*math.sin(2*angle)
    controller.location=(side,0,.53+rise)
    controller.rotation_euler=(0,angle,0)
    controller.keyframe_insert(data_path='location',frame=frame)
    controller.keyframe_insert(data_path='rotation_euler',frame=frame)
    poses.append({'frame':frame,'angle_deg':math.degrees(angle),'x':side,'reference_z':.53+rise})
scene.timeline_markers.new('CLOSED',frame=1)
scene.timeline_markers.new('LIFTED_0p12m',frame=30)
scene.timeline_markers.new('SIDE_SLIDING_MID',frame=60)
scene.timeline_markers.new('SIDE_STOWED',frame=90)

def flat_box(name,lo,size,material,col=review):
    bpy.ops.mesh.primitive_cube_add(size=1,location=Vector(lo)+Vector(size)/2)
    o=bpy.context.object
    o.name=name
    o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for old in list(o.users_collection):
        old.objects.unlink(o)
    col.objects.link(o)
    o.data.materials.append(material)
    return o
flat_box('REVIEW_FLOOR_not_room_design',(-1.8,-1.7,-.035),(3.2,3.4,.035),groundmat)
flat_box('REVIEW_next_pod_near_edge_0p70_gap',(1.225,-1.35,.001),(.009,2.7,.003),linemat)
flat_box('REVIEW_original_closed_side_edge',(.525,-1.35,.001),(.006,2.7,.003),linemat)

def camera(name,target,offset,ortho):
    data=bpy.data.cameras.new(name)
    data.type='ORTHO'
    data.ortho_scale=ortho
    o=bpy.data.objects.new(name,data)
    review.objects.link(o)
    target=Vector(target)
    o.location=target+Vector(offset)
    o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
    return o
cam=camera('Camera_oblique_review',(.13,0,.48),(-4,-5,3.5),3.8)
frontcam=camera('Camera_cross_section_review',(.35,0,.56),(0,-6,.8),2.6)
for name,location,energy,size in [('Key',(-3,-4,6),480,4),('Fill',(3,2,4),280,3)]:
    data=bpy.data.lights.new(name,'AREA')
    data.energy=energy
    data.size=size
    o=bpy.data.objects.new(name,data)
    review.objects.link(o)
    o.location=location
    o.rotation_euler=(Vector((0,0,.5))-o.location).to_track_quat('-Z','Y').to_euler()

def mesh_bvh(obj):
    verts=[obj.matrix_world@v.co for v in obj.data.vertices]
    faces=[p.vertices[:] for p in obj.data.polygons]
    return BVHTree.FromPolygons(verts,faces,all_triangles=False,epsilon=0.000001)

# Sample at half-frame steps to expose intermediate sweep, not just endpoints.
max_x=-math.inf
max_z=-math.inf
min_z=math.inf
collisions=[]
samples=[]
for n in range(1,181):
    f=1+(n-1)*.5
    scene.frame_set(int(f),subframe=f-int(f))
    bpy.context.view_layer.update()
    points=[lid.matrix_world@v.co for v in lid.data.vertices]
    xmax=max(v.x for v in points)
    zmax=max(v.z for v in points)
    zmin=min(v.z for v in points)
    max_x=max(max_x,xmax)
    max_z=max(max_z,zmax)
    min_z=min(min_z,zmin)
    pairs=mesh_bvh(body).overlap(mesh_bvh(lid))
    bedpairs=mesh_bvh(bed).overlap(mesh_bvh(lid))
    if pairs or bedpairs:
        collisions.append({'frame':f,'body_pairs':len(pairs),'bed_pairs':len(bedpairs)})
    samples.append({'frame':f,'lid_max_x_m':xmax,'lid_min_z_m':zmin,'lid_max_z_m':zmax})
scene.frame_set(90)
bpy.context.view_layer.update()
points=[lid.matrix_world@v.co for v in lid.data.vertices]
report={'status':'MOTION_CANDIDATE_NOT_APPROVED','body_external_closed_size_m':[1.05,2.30,1.0],
        'lift_m':.12,'side_stow_demonstration':'+X / side assignment TBD','sample_count':len(samples),
        'maximum_swept_x_m':max_x,'swept_protrusion_beyond_body_m':max_x-.525,
        'remaining_of_0p70m_gap_at_max_sweep':1.225-max_x,
        'final_stowed_max_x_m':max(v.x for v in points),'minimum_ground_clearance_m':min_z,
        'maximum_opening_height_m':max_z,'surface_intersection_frames':collisions,
        'method':'world mesh BVH surface intersections sampled every half frame; no mechanical or human validation',
        'limits':['not a physical rail mechanism','no swept volume continuous proof','no human boarding/turning validation','no neighboring lid simultaneous-opening validation','resting geometry/artwork awaits user review']}
(ROOT/'motion_measurements.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'motion_poses.json').write_text(json.dumps(poses,indent=2),encoding='utf-8')

if collisions:
    raise RuntimeError('Lid/body intersection detected. Review motion_measurements.json before rendering.')

scene.camera=cam
for frame,name in [(1,'01_closed.png'),(30,'02_lifted.png'),(60,'03_side_slide.png'),(90,'04_stowed.png')]:
    scene.frame_set(frame)
    scene.render.filepath=str(OUT/name)
    bpy.ops.render.render(write_still=True)
scene.camera=frontcam
scene.frame_set(90)
scene.render.filepath=str(OUT/'05_stowed_clearance.png')
bpy.ops.render.render(write_still=True)
scene.camera=cam
scene.frame_set(1)
scene.render.filepath='//evidence/01_closed.png'
scene['design_stage']='WHOLE LID MOTION / ORIGINAL SILHOUETTE CANDIDATE, USER REVIEW REQUIRED'
scene['source_reference']='user-provided Scifi - Cryogenic Sleep screenshot for broad silhouette only; source mesh not imported'
for area in bpy.context.screen.areas if bpy.context.screen else []:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='CAMERA'
        area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'room1_pod_whole_lid_motion_v1.blend'))
print(json.dumps(report,ensure_ascii=False,indent=2))
