"""Reference-led cryopod reconstruction, authored from simple profiles.
The user's GLB is observed separately; this builder never loads its mesh.
Blender 5.0.1 --background --factory-startup --python build_pod.py
"""
import bpy, math, sys, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from model_tools import material,mesh,box,unwrap,camera
OUT=ROOT/'evidence'
OUT.mkdir(exist_ok=True)
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
scene.view_settings.exposure=-.35
scene.world=bpy.data.worlds.new('Review_world')
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.14,.16,.18,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
def collection(name):
    c=bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c
fixed=collection('01_REFERENCE_LED_FIXED_SHELL')
moving=collection('02_ONE_PIECE_LID')
stage=collection('03_REVIEW_STAGE_not_room')
grey=material('Shell_neutral_grey',(.48,.51,.52))
frame=material('Frame_neutral_grey',(.58,.60,.60))
inner=material('Interior_neutral_grey',(.25,.29,.30))
bedmat=material('Mattress_placeholder',(.36,.40,.41))
window=material('Head_window_review_region',(.17,.30,.35))
floor=material('Review_floor',(.12,.15,.17))

def ring(w,l,z,cut=.06):
    x,y=w/2,l/2
    return [(x-cut,-y,z),(x,-y+cut,z),(x,y-cut,z),(x-cut,y,z),
            (-x+cut,y,z),(-x,y-cut,z),(-x,-y+cut,z),(-x+cut,-y,z)]

# The low basin fits between the long lower skirts and the end hoods.
rows=[ring(.92,2.10,.085),ring(1.01,2.13,.15),ring(1.05,2.17,.31),
      ring(1.05,2.17,.345),ring(.93,2.04,.345),ring(.88,1.98,.205)]
N=8
verts=[p for row in rows for p in row]
faces=[tuple(reversed(range(N)))]; regions=[3]
for j in range(len(rows)-1):
    for i in range(N):
        n=(i+1)%N
        faces.append((j*N+i,j*N+n,(j+1)*N+n,(j+1)*N+i))
        regions.append(2 if j==3 else 1 if j==4 else 0)
faces.append(tuple(range(5*N,6*N))); regions.append(1)
body=mesh('Fixed_low_basin',verts,faces,fixed,[grey,inner,frame,grey],regions)

# End hoods reproduce the reference's front ramp and shorter rear end cap.
# The broad top and sloping shoulders are continuous with the closed lid.
outline=[(-.45,.145),(-.492,.18),(-.51,.27),(-.51,.38),(-.49,.435),
         (-.29,.652),(-.255,.665),(.255,.665),(.29,.652),(.49,.435),
         (.51,.38),(.51,.27),(.492,.18),(.45,.145)]
def hood(name,stations):
    # Each station: longitudinal coordinate, top-height fraction, width fraction.
    vs=[]
    for y,h,w in stations:
        for x,z in outline:
            # Changes at upper end leave the lower body relatively full width.
            zz=z if z<=.36 else .36+(z-.36)*h
            vs.append((x*w,y,zz))
    n=len(outline)
    fs=[tuple(reversed(range(n)))]; rs=[0 if name.startswith('Foot') else 1]
    for j in range(len(stations)-1):
        for i in range(n):
            k=(i+1)%n
            fs.append((j*n+i,j*n+k,(j+1)*n+k,(j+1)*n+i)); rs.append(0)
    fs.append(tuple(range((len(stations)-1)*n,len(stations)*n))); rs.append(1 if name.startswith('Foot') else 0)
    return mesh(name,vs,fs,fixed,[frame,inner],rs)
foot=hood('Foot_hood_long_sloped_end',[(-1.147,.27,.90),(-1.12,.39,.97),(-.973,1,1),(-.930,1,1)])
head=hood('Head_hood_short_end_cap',[(.994,1,1),(1.060,1,1),(1.13,.58,.97),(1.147,.40,.90)])

# Long support skirts with a visible underside clearance, not small greebles.
def skirt(name,x):
    yz=[(-1.10,0),(-1.10,.34),(1.085,.34),(1.085,0),(.83,0),
        (.81,.043),(.78,.055),(-.78,.055),(-.81,.043),(-.83,0)]
    vs=[(xx,y,z) for xx in (x-.024,x+.024) for y,z in yz]
    n=len(yz)
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    fs.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    return mesh(name,vs,fs,fixed,[grey])
skirt('Left_support_skirt',-.495)
skirt('Right_support_skirt',.495)
box('Front_lower_cross_member',(0,-1.074,.075),(.92,.065,.12),fixed,grey,.012)
bed=box('Sleeping_surface', (0,0,.23),(.88,1.91,.04),fixed,bedmat,.015)

# The cover is one rigid shell with a broad roof and steep chamfer shoulders.
# The reference's torso window is opaque; only its head window remains glazed.
section=[(-.515,.354),(-.512,.408),(-.487,.447),(-.447,.487),
         (-.295,.645),(-.269,.656),(.269,.656),(.295,.645),
         (.447,.487),(.487,.447),(.512,.408),(.515,.354)]
stations=[(-.926,0),(-.891,.006),(-.740,0),(.365,0),(.400,.006),
          (.452,0),(.822,0),(.921,.006),(.990,0)]
nv=len(section)
verts=[(x,y,z+lift) for y,lift in stations for x,z in section]
faces=[]; regions=[]
for j in range(len(stations)-1):
    for i in range(nv-1):
        a=j*nv+i
        faces.append((a,a+1,a+1+nv,a+nv))
        # The head pane wraps over roof and the two diagonal shoulders.
        regions.append(1 if j==5 and 3<=i<=7 else 0)
faces.extend([tuple(reversed(range(nv))),tuple(range((len(stations)-1)*nv,len(stations)*nv))])
regions.extend([0,0])
lid=mesh('ONE_PIECE_COVER_head_window',verts,faces,moving,[frame,window,inner,window],regions)
bpy.context.view_layer.objects.active=lid
lid.select_set(True)
solid=lid.modifiers.new('Cover_shell_thickness','SOLIDIFY')
solid.thickness=.012
solid.offset=-1
solid.material_offset=2
solid.material_offset_rim=2
bpy.ops.object.modifier_apply(modifier=solid.name)

# Consolidate fixed exterior into one editable object; retain mattress separately.
bpy.ops.object.select_all(action='DESELECT')
for obj in list(fixed.objects):
    if obj!=bed:
        obj.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.object.join()
body.name='Reference_led_fixed_shell'
objects=(body,lid,bed)
for obj in objects:
    unwrap(obj,ROOT/'uv')

# Whole-cover motion: short vertical unseal, then sideways/down around the body.
# This is an editable motion proposal, not a manufactured guide-rail solution.
rig=bpy.data.objects.new('Whole_lid_motion',None)
moving.objects.link(rig)
rig.empty_display_type='ARROWS'
rig.empty_display_size=.15
pivot=.55
for vertex in lid.data.vertices:
    vertex.co.z-=pivot
lid.parent=rig
poses=[]
for f in range(1,109):
    if f<=12:
        a=0; rise=0; x=0
    elif f<=30:
        a=0; rise=.13*(f-12)/18; x=0
    else:
        t=min(1,(f-30)/60)
        a=math.pi*.5*t
        rise=.13*math.cos(a)
        x=.78*math.sin(a)+.06*math.sin(2*a)
    rig.location=(x,0,pivot+rise)
    rig.rotation_euler=(0,a,0)
    rig.keyframe_insert(data_path='location',frame=f)
    rig.keyframe_insert(data_path='rotation_euler',frame=f)
    poses.append({'frame':f,'x':x,'pivot_z':pivot+rise,'angle_deg':math.degrees(a)})
for name,f in [('CLOSED',1),('LIFTED',30),('SIDE_DOWN',60),('OPEN',90)]:
    scene.timeline_markers.new(name,frame=f)
(ROOT/'motion_poses.json').write_text(json.dumps(poses,indent=2),encoding='utf-8')
lid['design']='One complete rigid canopy, head-only glazing. Torso glazing replaced with solid panel.'
lid['motion_status']='editable candidate; actual guide mechanism and boarding side pending review'
body['dimension_intent']='2.30 m length x 1.05 m width; about 0.67 m closed height from reference proportions'

box('Review_floor',(0,0,-.025),(3.8,3.4,.05),stage,floor)
cam=camera('Camera_oblique',(.12,0,.34),(4,-5,3.4),3.7,stage)
motioncam=camera('Camera_motion_opposite_side',(.12,0,.34),(-4,-5,3.4),3.7,stage)
sidecam=camera('Camera_side',(0,0,.335),(6,0,0),2.9,stage)
endcam=camera('Camera_foot_end',(0,-.15,.335),(0,-6,.4),1.55,stage)
for name,pos,energy,size in [('Key',(-3,-4,6),460,4),('Fill',(3,2,4),250,3)]:
    data=bpy.data.lights.new(name,'AREA')
    data.energy=energy; data.size=size
    obj=bpy.data.objects.new(name,data)
    stage.objects.link(obj)
    obj.location=pos
    obj.rotation_euler=(Vector((0,0,.3))-obj.location).to_track_quat('-Z','Y').to_euler()

scene.camera=cam
for f,name in [(1,'01_closed.png'),(30,'02_lifted.png'),(60,'03_side_down.png'),(90,'04_open.png')]:
    scene.camera=cam if f==1 else motioncam
    scene.frame_set(f)
    scene.render.filepath=str(OUT/name)
    bpy.ops.render.render(write_still=True)
scene.frame_set(1)
for c,name in [(sidecam,'05_side.png'),(endcam,'06_foot_end.png')]:
    scene.camera=c
    scene.render.filepath=str(OUT/name)
    bpy.ops.render.render(write_still=True)

# Surface mapping preview, not a production pixel texture.
checker_image=bpy.data.images.new('UV_checker_guide_only',width=1024,height=1024)
checker_image.generated_type='COLOR_GRID'
checker=material('UV_CHECKER_NOT_PRODUCTION',(.5,.5,.5))
node=checker.node_tree.nodes.new('ShaderNodeTexImage')
node.image=checker_image; node.interpolation='Closest'
checker.node_tree.links.new(node.outputs['Color'],checker.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
saved={o.name:list(o.data.materials) for o in objects}
for o in objects:
    for i in range(len(o.data.materials)):
        o.data.materials[i]=checker
scene.camera=cam
scene.render.filepath=str(OUT/'07_uv_checker.png')
bpy.ops.render.render(write_still=True)
for o in objects:
    for i,m in enumerate(saved[o.name]):
        o.data.materials[i]=m
checker_image.pack()
scene.frame_set(1)
# Same proportions/low angle as the separate reference observation render.
refcam=camera('Camera_reference_comparison',(0,0,.3618),(3.675,-6.9,1.3802),2.898,stage)
scene.camera=refcam
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'
scene.display.shading.studio_light='paint.sl'
scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='WORLD'
scene.display.shading.cavity_ridge_factor=1.4
scene.display.shading.cavity_valley_factor=1.2
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=0
scene.render.resolution_x=1400; scene.render.resolution_y=900
stage.objects['Review_floor'].hide_render=True
original_colors={m.name:tuple(m.diffuse_color) for m in (grey,frame,inner,bedmat,window)}
for m in (grey,frame):
    m.diffuse_color=(.34,.37,.39,1)
window.diffuse_color=(.16,.20,.23,1)
scene.render.filepath=str(OUT/'08_reference_angle.png')
bpy.ops.render.render(write_still=True)
for name,color in original_colors.items():
    bpy.data.materials[name].diffuse_color=color
stage.objects['Review_floor'].hide_render=False
scene.render.engine='BLENDER_EEVEE'
scene.view_settings.view_transform='Standard'; scene.view_settings.look='None'
scene.view_settings.exposure=-.35
scene.render.resolution_x=1440; scene.render.resolution_y=1000
scene.camera=cam
scene.frame_set(1)
scene.render.filepath='//evidence/01_closed.png'
scene['status']='REFERENCE-LED v4 / art and motion candidate, review required'
scene['source_credit']='Scifi - Cryogenic Sleep by Artboard Silvio Pinheiro (scrpinheiro), CC BY 4.0 per source GLB; design reconstructed with new low-poly topology; head-window and opening modified'
scene['scope']='Single pod only. No room layout, CAD, Godot scene or source GLB modified.'
for area in bpy.context.screen.areas if bpy.context.screen else []:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='CAMERA'
        area.spaces.active.shading.type='MATERIAL'
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'room1_pod_reference_v4.blend'))
print('SAVED_V4',ROOT)
