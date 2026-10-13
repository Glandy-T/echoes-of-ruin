"""Extract the selected source hair unchanged; add two editable front locks.

Blender 5.0.1, --background --factory-startup --disable-autoexec.
No source rig or animation is assumed. This is a static source-scale review.
"""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Vector, Matrix

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'source/original/source/Long hair.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),use_scripts=False)
bpy.context.preferences.filepaths.save_version=0
sc=bpy.context.scene

# The source uses node-group colors, while its viewport swatches are all grey.
for m in bpy.data.materials:
    if not m.use_nodes: continue
    nodes=m.node_tree.nodes
    n=next((n for n in nodes if n.type=='GROUP' and 'Color' in n.inputs),None)
    n=n or next((n for n in nodes if n.type=='BSDF_PRINCIPLED'),None)
    n=n or next((n for n in nodes if n.type=='EMISSION'),None)
    if n:
        socket=n.inputs.get('Color') or n.inputs.get('Base Color')
        if socket: m.diffuse_color=tuple(min(1,max(0,v)) for v in socket.default_value)

def evaluated_copy(source,name):
    dg=bpy.context.evaluated_depsgraph_get()
    mesh=bpy.data.meshes.new_from_object(source.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg)
    ob=bpy.data.objects.new(name,mesh);sc.collection.objects.link(ob)
    mesh.transform(Matrix.Translation((-.6,0,0))@source.matrix_world)
    return ob

back=evaluated_copy(bpy.data.objects['Plain.001'],'Hair_Back_SOURCE_UNCHANGED')
body=evaluated_copy(bpy.data.objects['Body.001'],'REFERENCE_SourceBody')
eyes=evaluated_copy(bpy.data.objects['Open eyes.003'],'REFERENCE_SourceEyes')
keep={back,body,eyes}
for ob in list(bpy.data.objects):
    if ob not in keep: bpy.data.objects.remove(ob,do_unlink=True)
for collection in list(bpy.data.collections):
    if not collection.objects and not collection.children:bpy.data.collections.remove(collection)
hair_mat=bpy.data.materials['shared_hair_brown']
back['source']='Jan Blaha / swifterik, Long hair variants, CC BY 4.0'
back['source_object']='Plain.001 (rightmost straight back-hair variant)'
back['geometry_changes']='Mirror evaluated; translated -0.6m on X. Source shape unchanged.'

# Preview only: match the hoodie color in the user's Sketchfab screenshot.
# The downloaded .blend uses a blue material on this same rightmost character.
hoodie=bpy.data.materials.new('REFERENCE_RustHoodie');hoodie.diffuse_color=(.31,.075,.025,1)
body.data.materials[1]=hoodie

# Each horizontal cross-section is a shallow six-sided strip, not a hair card.
# Root sits inside the existing side hair above the ear, leaving the face open.
# Coordinates are measured in the source character's centered world space.
rows=[
 (.072,.025,1.375,.008,.008),
 (.077,.007,1.339,.019,.011),
 (.080,-.001,1.286,.025,.012),
 (.079,-.011,1.232,.029,.013),
 (.078,-.025,1.181,.030,.012),
 (.074,-.040,1.135,.027,.011),
 (.071,-.052,1.100,.022,.009),
 (.070,-.053,1.087,.012,.006),
]
profile=[(-.5,0),(-.28,-.5),(.25,-.52),(.5,0),(.25,.5),(-.28,.5)]

def front_lock(side):
    verts=[]
    for i,(x,y,z,w,d) in enumerate(rows):
        # Small, deliberate left/right length difference avoids a mirrored tip.
        dz= -.012*(i/(len(rows)-1))**2 if side<0 else 0
        for u,v in profile:
            verts.append((side*(x+u*w),y+v*d,z+dz+(.004*u if i==len(rows)-1 else 0)))
    faces=[]
    for i in range(len(rows)-1):
        for j in range(6):faces.append((i*6+j,i*6+(j+1)%6,(i+1)*6+(j+1)%6,(i+1)*6+j))
    faces += [tuple(reversed(range(6))),tuple((len(rows)-1)*6+j for j in range(6))]
    me=bpy.data.meshes.new('FrontLock_Mesh');me.from_pydata(verts,[],faces);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
    name='Hair_Front.L' if side>0 else 'Hair_Front.R'
    ob=bpy.data.objects.new(name,me);sc.collection.objects.link(ob);me.materials.append(hair_mat)
    ob['purpose']='New front section, separate editable mesh; static, not rigged.'
    ob['design']='Ear-front to upper chest; original back hair preserved.'
    return ob

fronts=[front_lock(1),front_lock(-1)]
hair_objects=[back]+fronts

# A separate, non-overlapping draft UV set; source UV remains available on back.
for ob in hair_objects:
    if ob==back and ob.data.uv_layers:ob.data.uv_layers.active.name='UV_Source_Preserved'
    ob.data.uv_layers.new(name='UV_Pixel_Draft');ob.data.uv_layers.active_index=len(ob.data.uv_layers)-1
    ob.data.uv_layers.active.active_render=True
bpy.ops.object.select_all(action='DESELECT')
for ob in hair_objects:ob.select_set(True)
bpy.context.view_layer.objects.active=back
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(70),island_margin=.025,area_weight=0.0,correct_aspect=True,scale_to_bounds=False)
bpy.ops.uv.pack_islands(rotate=True,margin=.025)
bpy.ops.object.mode_set(mode='OBJECT')
# The mirrored inner-head polygons 129/130 fold under smart projection.
# Give these hidden surfaces separate convex islands without changing geometry.
# Reserve a bottom strip explicitly, avoiding selection-dependent UV repacking.
for ob in hair_objects:
    for loop in ob.data.uv_layers['UV_Pixel_Draft'].data:
        loop.uv=(.07+.86*loop.uv.x,.12+.86*loop.uv.y)
uv=back.data.uv_layers['UV_Pixel_Draft']
for slot,pid in enumerate((129,130)):
    poly=back.data.polygons[pid]
    radius=.02
    for j,li in enumerate(poly.loop_indices):
        angle=2*math.pi*j/poly.loop_total
        uv.data[li].uv=(.08+slot*.1+radius*math.cos(angle),.05+radius*math.sin(angle))

asset_col=bpy.data.collections.new('HAIR_ASSET__3_SEPARATE_MESHES');sc.collection.children.link(asset_col)
ref_col=bpy.data.collections.new('REFERENCE_ONLY__NOT_PLAYER_BODY');sc.collection.children.link(ref_col)
for ob in hair_objects+[body,eyes]:
    for c in list(ob.users_collection):c.objects.unlink(ob)
    (asset_col if ob in hair_objects else ref_col).objects.link(ob)

def aim(ob,pt):ob.rotation_euler=(Vector(pt)-ob.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('ReviewCamera');cam=bpy.data.objects.new('ReviewCamera',cd);sc.collection.objects.link(cam);sc.camera=cam
cd.type='ORTHO'
sc.render.engine='BLENDER_WORKBENCH';sh=sc.display.shading
sh.light='STUDIO';sh.studiolight_rotate_z=.3;sh.color_type='MATERIAL';sh.show_shadows=True
sh.show_cavity=False;sh.show_specular_highlight=False;sh.background_type='WORLD';sc.world.color=(.68,.68,.68)
sc.view_settings.view_transform='Standard';sc.view_settings.look='Medium High Contrast'
sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False

def render(name,location,target,ortho,width=800,height=1000,front=True):
    for o in fronts:o.hide_render=not front
    cam.location=location;aim(cam,target);cd.ortho_scale=ortho
    sc.render.resolution_x=width;sc.render.resolution_y=height
    sc.render.filepath=str(ROOT/(name+'.png'));bpy.ops.render.render(write_still=True)

render('01_source_original',(.28,-3,1.31),(0,.015,1.245),.60,front=False)
render('02_front_locks',(.28,-3,1.31),(0,.015,1.245),.60)
render('03_front', (0,-3,1.29),(0,.015,1.245),.60)
render('04_side',(3,-.08,1.29),(0,.015,1.245),.60)
render('05_back',(.30,3,1.20),(0,.05,1.10),.88)

for o in [body,eyes]:o.hide_render=True
render('06_hair_isolated',(.40,-3,1.38),(0,.075,1.07),1.02)
for o in [body,eyes]:o.hide_render=False
for o in fronts:o.hide_render=False

# Actual 3D side-by-side render, separate from the editable asset scene.
comparison=bpy.data.scenes.new('COMPARISON__ORIGINAL_AND_FRONT_LOCKS')
comparison.world=sc.world
comparison.render.engine='BLENDER_WORKBENCH'
cs=comparison.display.shading
for prop in ['light','studiolight_rotate_z','color_type','show_shadows','show_cavity','show_specular_highlight','background_type']:
    setattr(cs,prop,getattr(sh,prop))
comparison.view_settings.view_transform=sc.view_settings.view_transform
comparison.view_settings.look=sc.view_settings.look
for dx,include_front in [(-.245,False),(.245,True)]:
    for src in [body,eyes,back]+(fronts if include_front else []):
        cp=src.copy();cp.name=('BEFORE_' if dx<0 else 'AFTER_')+src.name
        comparison.collection.objects.link(cp);cp.location.x+=dx
    font=bpy.data.curves.new('ReviewLabel','FONT');font.body='ORIGINAL' if dx<0 else '+ FRONT LOCKS'
    font.align_x='CENTER';font.size=.022
    lab=bpy.data.objects.new(font.body,font);comparison.collection.objects.link(lab)
    lab.location=(dx,-.06,1.535);lab.rotation_euler=(math.pi/2,0,0)
    labelmat=bpy.data.materials.get('Label_Dark') or bpy.data.materials.new('Label_Dark');labelmat.diffuse_color=(.055,.055,.055,1)
    font.materials.append(labelmat)
comparecam=bpy.data.objects.new('CompareCamera',cd.copy());comparison.collection.objects.link(comparecam)
comparecam.location=(0,-3,1.30);aim(comparecam,(0,0,1.25));comparecam.data.ortho_scale=1.0;comparison.camera=comparecam
comparison.render.resolution_x=1400;comparison.render.resolution_y=940;comparison.render.resolution_percentage=100
comparison.render.image_settings.file_format='PNG';comparison.render.filepath=str(ROOT/'00_comparison.png')
bpy.ops.render.render(write_still=True,scene=comparison.name)

cam.location=(.28,-3,1.31);aim(cam,(0,.015,1.245));cd.ortho_scale=.60

# Saved working file opens on the modified source-scale hair, not the game body.
sc.name='SOURCE_SCALE_HAIR_REVIEW__STATIC'
bpy.ops.object.select_all(action='DESELECT')
for o in hair_objects:o.select_set(True)
bpy.context.view_layer.objects.active=back
for area in bpy.context.screen.areas if bpy.context.screen else []:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_distance=.85
        area.spaces.active.region_3d.view_location=(0,0,1.22)
        area.spaces.active.shading.type='SOLID';area.spaces.active.shading.color_type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'hair_front_locks_v4.blend'))
summary={'blender':bpy.app.version_string,'source_object':'Plain.001','source_shape_preserved':True,
 'scope':'Static source-character review. Not yet fitted to the 165cm pistachio body; no rig or animation.',
 'reference_body_display_change':'Downloaded blue hoodie displayed rust to match user screenshot; not a proposed player outfit.',
 'hair_objects':[]}
for o in hair_objects:
    o.data.calc_loop_triangles()
    summary['hair_objects'].append({'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'triangles':len(o.data.loop_triangles),'uv_layers':[uv.name for uv in o.data.uv_layers]})
(ROOT/'build_report.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
print(json.dumps(summary,indent=2))
