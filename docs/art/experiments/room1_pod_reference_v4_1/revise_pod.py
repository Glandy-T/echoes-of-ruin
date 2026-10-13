"""Load v4 intact, limit its existing motion and inset the requested foot display.
Blender 5.0.1 --background --factory-startup --python revise_pod.py
"""
import bpy,bmesh,json,math,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'room1_pod_reference_v4'
sys.path.insert(0,str(BASE))
from model_tools import material,camera
OUT=ROOT/'evidence'; OUT.mkdir(parents=True,exist_ok=True)
UV=ROOT/'uv'; UV.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE/'room1_pod_reference_v4.blend'))
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene
scene.frame_set(1)
body=bpy.data.objects['Reference_led_fixed_shell']
lid=bpy.data.objects['ONE_PIECE_COVER_head_window']
rig=bpy.data.objects['Whole_lid_motion']

# Keep v4 positions through frame 60; hold that user-selected pose thereafter.
source_poses=json.loads((BASE/'motion_poses.json').read_text(encoding='utf-8'))
rig.animation_data_clear()
poses=[]
for f in range(1,109):
    p=dict(source_poses[min(f,60)-1]); p['frame']=f
    rig.location=(p['x'],0,p['pivot_z'])
    rig.rotation_euler=(0,math.radians(p['angle_deg']),0)
    rig.keyframe_insert(data_path='location',frame=f)
    rig.keyframe_insert(data_path='rotation_euler',frame=f)
    poses.append(p)
scene.timeline_markers.clear()
for name,f in [('CLOSED',1),('LIFTED',30),('OPEN_45deg_USER_SCREENSHOT',60)]:
    scene.timeline_markers.new(name,frame=f)
(ROOT/'motion_poses.json').write_text(json.dumps(poses,indent=2),encoding='utf-8')
lid['motion_status']='v4.1: full-open endpoint is former v4 frame 60, 45 degrees; no further side standing/stow motion'

# Replace only the broad planar quadrilateral on the FOOT sloping fascia.
# Four outer corners are from v4's actual authored face, not a new body profile.
y0,z0,w0=-1.12,.36+(.665-.36)*.39,.255*.97
y1,z1,w1=-.973,.665,.255
corners=[Vector((-w0,y0,z0)),Vector((w0,y0,z0)),
         Vector((w1,y1,z1)),Vector((-w1,y1,z1))]
bm=bmesh.new(); bm.from_mesh(body.data)
layer=bm.loops.layers.uv.active
target=None
for face in bm.faces:
    if len(face.verts)==4 and all(any((v.co-c).length<1e-5 for c in corners) for v in face.verts):
        target=face; break
if target is None:
    raise RuntimeError('Expected unchanged v4 foot fascia face was not found; refusing to alter another surface')
outer=[min(target.verts,key=lambda v:(v.co-c).length) for c in corners]
base_uv=[]
for v in outer:
    base_uv.append(next(loop[layer].uv.copy() for loop in target.loops if loop.vert==v))
surface_mat=target.material_index
center=Vector((0,(y0+y1)/2,(z0+z1)/2))
u=Vector((1,0,0))
v=Vector((0,y1-y0,z1-z0)).normalized()
normal=u.cross(v).normalized()
outer_width,outer_height=.488,.217
screen_width,screen_height=.470,.195
depth=.004
def rect(width,height,d):
    return [center+u*x+v*y-normal*d for x,y in
            [(-width/2,-height/2),(width/2,-height/2),(width/2,height/2),(-width/2,height/2)]]
rim_coords=rect(outer_width,outer_height,0)
screen_coords=rect(screen_width,screen_height,depth)
rim=[bm.verts.new(p) for p in rim_coords]
inside=[bm.verts.new(p) for p in screen_coords]
def surface_uv(p):
    # Project the shallow inset back onto the original fascia UV patch.
    projected=p+normal*((center-p).dot(normal))
    t=(projected.y-y0)/(y1-y0)
    w=w0*(1-t)+w1*t
    s=(projected.x+w)/(2*w)
    low=base_uv[0].lerp(base_uv[1],s)
    high=base_uv[3].lerp(base_uv[2],s)
    return low.lerp(high,t)
bm.faces.remove(target)
for i in range(4):
    n=(i+1)%4
    for verts in [(outer[i],outer[n],rim[n],rim[i]),(rim[i],rim[n],inside[n],inside[i])]:
        face=bm.faces.new(verts)
        face.material_index=surface_mat
        for loop in face.loops:
            loop[layer].uv=surface_uv(loop.vert.co)
for edge in bm.edges:
    if edge.verts[0] in inside and edge.verts[1] in inside:
        edge.seam=True
bm.normal_update()
bm.to_mesh(body.data); bm.free()
body.data.update()

# Dedicated two-triangle screen face, four unique UV corners for later UI/paint.
display_mesh=bpy.data.meshes.new('Foot_info_display_surface_mesh')
display_mesh.from_pydata([tuple(p) for p in screen_coords],[],[(0,1,2,3)])
display_mesh.update()
display=bpy.data.objects.new('Foot_info_display_surface',display_mesh)
bpy.data.collections['01_REFERENCE_LED_FIXED_SHELL'].objects.link(display)
screenmat=material('Info_display_BLANK_no_final_UI',(.055,.095,.11))
display.data.materials.append(screenmat)
uv=display_mesh.uv_layers.new(name='UV_SCREEN_0_1')
for loop,co in zip(display_mesh.polygons[0].loop_indices,[(0,0),(1,0),(1,1),(0,1)]):
    uv.data[loop].uv=co
uv.active_render=True
display['design']='Enlarged shallow foot fascia inset; 0.470 x 0.195 m display, 4 mm depth; size provisional'
display['future_content']='Dedicated material and UV: numbers, status, typography and emission added in pixel texture/Godot later'
display['status']='User requested information display location; neutral blank geometry candidate'

# Export existing UVs without repacking body, lid or mattress islands.
objects=(body,lid,bpy.data.objects['Sleeping_surface'],display)
colors=['#bac6c8','#8ba2ad','#a3b6b0','#bcb49b','#89959d']
for obj in objects:
    layer=obj.data.uv_layers.active
    size=[512,212] if obj==display else [1024,1024]
    faces=[{'material':p.material_index,'uv':[list(layer.data[i].uv) for i in p.loop_indices]} for p in obj.data.polygons]
    (UV/(obj.name+'.json')).write_text(json.dumps({'object':obj.name,'template_pixels':size,'faces':faces},indent=2),encoding='utf-8')
    width,height=size
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',f'<rect width="{width}" height="{height}" fill="#202932"/>']
    for face in faces:
        coords=' '.join(f'{a*width:.3f},{(1-b)*height:.3f}' for a,b in face['uv'])
        svg.append(f'<polygon points="{coords}" fill="{colors[face["material"]%len(colors)]}" stroke="#273942" stroke-width="1"/>')
    svg.append('</svg>')
    (UV/(obj.name+'.svg')).write_text('\n'.join(svg),encoding='utf-8')

stage=bpy.data.collections['03_REVIEW_STAGE_not_room']
main=bpy.data.objects['Camera_oblique']
motion=bpy.data.objects['Camera_motion_opposite_side']
close=camera('Camera_display_close',tuple(center),(1.25,-2.3,1.3),1.12,stage)
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1440;scene.render.resolution_y=1000
scene.render.resolution_percentage=100
for f,c,name in [(1,main,'01_closed.png'),(60,motion,'02_open_45deg.png'),(1,close,'03_display_close.png')]:
    scene.frame_set(f);scene.camera=c
    scene.render.filepath=str(OUT/name)
    bpy.ops.render.render(write_still=True)
scene.frame_set(1);scene.camera=main
original_mats={o.name:list(o.data.materials) for o in objects}
checker=bpy.data.materials.get('UV_CHECKER_NOT_PRODUCTION')
if checker is None:
    checker=material('UV_CHECKER_NOT_PRODUCTION',(.5,.5,.5))
    checker_image=bpy.data.images.new('UV_checker_guide_only_v4_1',width=1024,height=1024)
    checker_image.generated_type='COLOR_GRID'
    checker_image.pack();checker_image.use_fake_user=True
    tex=checker.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image=checker_image;tex.interpolation='Closest'
    checker.node_tree.links.new(tex.outputs['Color'],checker.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
checker.use_fake_user=True
for obj in objects:
    for i in range(len(obj.data.materials)):
        obj.data.materials[i]=checker
scene.render.filepath=str(OUT/'04_uv_checker.png')
bpy.ops.render.render(write_still=True)
for obj in objects:
    for i,m in enumerate(original_mats[obj.name]):
        obj.data.materials[i]=m
scene.frame_set(1);scene.camera=main
scene.render.filepath='//evidence/01_closed.png'
scene['status']='v4.1: v4 body retained; user-selected 45deg open stop and shallow foot information display'
scene['scope']='Only the lid endpoint and the local foot display inset changed. Final display UI/texture pending.'
bpy.ops.object.select_all(action='DESELECT')
display.select_set(True);bpy.context.view_layer.objects.active=display
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'room1_pod_reference_v4_1.blend'))
print('SAVED_V4_1',ROOT)
