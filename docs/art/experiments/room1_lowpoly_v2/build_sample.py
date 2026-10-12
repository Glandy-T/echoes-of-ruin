"""Original architectural art trial v2. No CAD topology or v1 meshes imported.
Run with Blender 5.0.1 --background --factory-startup --python build_sample.py.
"""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
for name in ('textures','evidence'):
    (ROOT/name).mkdir(parents=True,exist_ok=True)
DATA=json.loads((ROOT/'engineering_reference.json').read_text(encoding='utf-8'))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1600
scene.render.resolution_y=1000
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='Standard'
scene.view_settings.look='None'
scene.view_settings.exposure=0
scene.view_settings.gamma=1
world=bpy.data.worlds.new('Neutral_review_world')
world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.09,.13,.16,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.3
scene.world=world

def collection(name):
    c=bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c
floorcol=collection('01_ART_FLOOR_MODULES_CANDIDATE')
wallcol=collection('02_ART_WALL_CASSETTES_CANDIDATE')
placeholder=collection('03_ENGINEERING_ENVELOPE_ONLY_NOT_POD_DESIGN')
review=collection('04_REVIEW_CAMERAS_LIGHTS')

def srgb(v):
    v=v/255
    return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def rgba(rgb):
    return tuple(srgb(v) for v in rgb)+(1,)

PALETTES={
    'wall':[(181,199,192),(157,181,178),(208,217,201),(130,163,164),(192,208,198)],
    'floor':[(100,129,136),(85,114,124),(120,146,147),(74,101,112),(109,137,139)],
}
TEXTURE_RECTS={}
def paint(kind,w,h):
    """Hand-placed rectangles form sparse material clusters. No random noise."""
    grid=[[0 for x in range(w)] for y in range(h)]
    rects=[]
    def rect(x,y,width,height,index):
        rects.append([x,y,width,height,index])
        for yy in range(max(y,0),min(y+height,h)):
            for xx in range(max(x,0),min(x+width,w)):
                grid[yy][xx]=index
    if kind=='wall':
        # Lower-value return edge and a pixel-stepped soft pigment patch.
        rect(0,0,2,h,1)
        rect(2,0,1,h,4)
        rect(3,h-3,w-6,2,2)
        rect(w-2,0,2,h,1)
        for x,y,ww,hh in [(11,141,35,6),(14,147,38,7),(19,154,34,8),(24,162,23,5)]:
            rect(x,y,ww,hh,4)
        for x,y,ww,hh in [(59,28,23,4),(62,32,20,5),(66,37,14,3)]:
            rect(x,y,ww,hh,1)
        # A few grouped ceramic coating accents, not scratches or dirt.
        rect(14,150,8,2,2)
        rect(22,152,5,2,2)
        rect(70,31,6,2,3)
        rect(51,102,4,2,4)
    else:
        # Quiet compressed mineral tone clusters with broad clear walking area.
        for x,y,ww,hh in [(9,18,22,3),(13,21,24,3),(18,24,21,3),(22,27,12,2),
                          (56,83,23,3),(59,86,21,4),(64,90,14,3)]:
            rect(x,y,ww,hh,4)
        for x,y,ww,hh in [(13,21,7,2),(20,23,5,1),(66,86,8,2)]:
            rect(x,y,ww,hh,2)
        for x,y,ww,hh in [(51,48,17,2),(55,50,16,2),(60,52,8,2)]:
            rect(x,y,ww,hh,1)
        rect(61,50,4,1,3)
        rect(18,96,5,2,1)
        rect(22,98,3,1,1)
    palette=PALETTES[kind]
    image=bpy.data.images.new('ORIGINAL_'+kind+'_clusters',width=w,height=h,alpha=False)
    image.pixels.foreach_set([v for row in grid for index in row for v in tuple(c/255 for c in palette[index])+(1,)])
    image.filepath_raw=str(ROOT/'textures'/f'{kind}_clusters_{w}x{h}.png')
    image.file_format='PNG'
    image.save()
    # Re-load the authored sRGB PNG so shader input uses decoded linear color.
    path=image.filepath_raw
    name=image.name
    bpy.data.images.remove(image)
    image=bpy.data.images.load(path,check_existing=False)
    image.name=name
    TEXTURE_RECTS[kind]=rects
    return image
wallimage=paint('wall',96,192)
floorimage=paint('floor',96,120)
(ROOT/'textures'/'pixel_sources.json').write_text(json.dumps({'status':'original provisional artwork','coordinates':'bottom-left texel origin','palettes_srgb':PALETTES,'rectangles':TEXTURE_RECTS},indent=2),encoding='utf-8')

def mat(name,rgb,image=None):
    """Blender-only three-level diffuse trial; not claimed as reference shader."""
    m=bpy.data.materials.new(name)
    m.diffuse_color=rgba(rgb)
    m.use_nodes=True
    nodes=m.node_tree.nodes
    nodes.clear()
    links=m.node_tree.links
    diffuse=nodes.new('ShaderNodeBsdfDiffuse')
    diffuse.inputs['Color'].default_value=(1,1,1,1)
    diffuse.inputs['Roughness'].default_value=1
    lit=nodes.new('ShaderNodeShaderToRGB')
    links.new(diffuse.outputs[0],lit.inputs[0])
    ramp=nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation='CONSTANT'
    levels=[(.0,.58),(.18,.80),(.50,1.0)]
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    for i,(position,value) in enumerate(levels):
        elem=ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(position)
        elem.position=position
        elem.color=(value,value,value,1)
    links.new(lit.outputs['Color'],ramp.inputs['Fac'])
    mix=nodes.new('ShaderNodeMixRGB')
    mix.blend_type='MULTIPLY'
    mix.inputs[0].default_value=1
    links.new(ramp.outputs['Color'],mix.inputs[1])
    mix.inputs[2].default_value=rgba(rgb)
    if image:
        tex=nodes.new('ShaderNodeTexImage')
        tex.image=image
        tex.interpolation='Closest'
        tex.extension='EXTEND'
        links.new(tex.outputs['Color'],mix.inputs[2])
    emission=nodes.new('ShaderNodeEmission')
    links.new(mix.outputs['Color'],emission.inputs['Color'])
    output=nodes.new('ShaderNodeOutputMaterial')
    links.new(emission.outputs[0],output.inputs['Surface'])
    m['status']='provisional art/shading candidate; Blender EEVEE only'
    return m

wallmat=mat('ART_engineering_ceramic_pixel_clusters',(181,199,192),wallimage)
floormat=mat('ART_min mineral_composite_pixel_clusters',(100,129,136),floorimage)
edgemat=mat('ART_panel_edge_plain',(155,180,176))
flooredge=mat('ART_floor_joint_return',(74,101,112))
backmat=mat('ART_recessed_joint_backing',(44,66,75))
trim=mat('ART_flush_jamb_and_corner_return',(109,145,150))
lower=mat('ART_cleanable_lower_wall',(62,92,102))
border=mat('ART_floor_perimeter_material_band',(79,108,117))
podmat=mat('ENVELOPE_ONLY_neutral_pod_no_product_details',(152,165,167))
clay=mat('REVIEW_untextured_uniform_clay',(174,186,183))

def relocate(obj,col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)

def planar_uv(obj,axes=None,image_size=(96,192),density=64):
    for old in list(obj.data.uv_layers):
        obj.data.uv_layers.remove(old)
    uv=obj.data.uv_layers.new(name='UV_ART_64texels_per_m')
    uv.active_render=True
    mins=Vector([min(v.co[i] for v in obj.data.vertices) for i in range(3)])
    for p in obj.data.polygons:
        normal_axis=max(range(3),key=lambda i:abs(p.normal[i]))
        use=axes or [(1,2),(0,2),(0,1)][normal_axis]
        for li in p.loop_indices:
            co=obj.data.vertices[obj.data.loops[li].vertex_index].co-mins
            uv.data[li].uv=(co[use[0]]*density/image_size[0],co[use[1]]*density/image_size[1])

def box(name,mincorner,size,material,col,bevel=0,edge=None,axes=None,imsize=(96,192)):
    loc=Vector(mincorner)+Vector(size)/2
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    obj=bpy.context.object
    obj.name=name
    obj.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    relocate(obj,col)
    obj.data.materials.append(material)
    if edge:
        obj.data.materials.append(edge)
    if bevel:
        modifier=obj.modifiers.new('ART_small_edge_return','BEVEL')
        modifier.width=bevel
        modifier.segments=1
        modifier.affect='EDGES'
        modifier.material=1 if edge else 0
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    planar_uv(obj,axes,imsize)
    obj['purpose']='original architectural module candidate'
    return obj

# Continuous subfloor and top sheets occupy the same v1 crop. No raised walkway.
box('Floor_continuous_substrate',(.2,5.5,-.1),(4.5,3.8,.087),backmat,floorcol)
for col in range(3):
    for row in range(2):
        a,b=.2+col*1.5,5.5+row*1.9
        start_x=max(a+.004,.384)
        end_y=min(b+1.896,9.116)
        obj=box(f'Floor_sheet_{col+1}_{row+1}',(start_x,b+.004,-.014),(a+1.496-start_x,end_y-b-.004,.014),floormat,floorcol,.003,flooredge,axes=(0,1),imsize=(96,120))
        obj['purpose']='replaceable floor sheet, 8mm installation joint and 3mm edge break; top Z=0'
# Flat perimeter strip uses a separate material, not a raised lip.
box('Floor_perimeter_left_material',(.2,5.5,-.012),(.18,3.8,.012),border,floorcol)
box('Floor_perimeter_rear_material',(.38,9.12,-.012),(4.32,.18,.012),border,floorcol)

# Original cassette wall shell: all geometry stays within the 0.20 m wall envelope.
# Face normals/coordinates refer to the actual inherited interior boundary.
box('Rear_wall_recessed_support',(.2,9.34,0),(4.5,.16,3.4),backmat,wallcol)
box('Left_wall_recessed_support',(0,5.5,0),(.16,3.8,3.4),backmat,wallcol)
for i in range(3):
    a=.2+i*1.5
    box(f'Rear_upper_cassette_{i+1}',(a+.035,9.300,.44),(1.43,.035,2.96),wallmat,wallcol,.009,edgemat,axes=(0,2))
    box(f'Rear_flush_vertical_joint_{i}',(a+.005,9.300,.40),(.025,.04,3.0),trim,wallcol)
    box(f'Rear_lower_replaceable_strip_{i+1}',(a+.008,9.300,0),(1.484,.04,.38),lower,wallcol,.006,trim,axes=(0,2))
box('Rear_flush_end_return',(4.67,9.30,.40),(.03,.04,3.0),trim,wallcol)
box('Rear_horizontal_sealed_joint',(.2,9.300,.396),(4.5,.04,.022),trim,wallcol)
for i in range(2):
    a=5.5+i*1.9
    # 1.9m bay uses a 1.43m main cassette + narrow cut-to-fit edge sheet.
    box(f'Left_upper_cassette_{i+1}',(.165,a+.035,.44),(.035,1.43,2.96),wallmat,wallcol,.009,edgemat,axes=(1,2))
    box(f'Left_cut_edge_cassette_{i+1}',(.165,a+1.50,.44),(.035,.365,2.96),edgemat,wallcol,.009,trim,axes=(1,2))
    box(f'Left_vertical_joint_{i}',(.16,a+.005,.40),(.04,.025,3.0),trim,wallcol)
    box(f'Left_lower_replaceable_strip_{i+1}',(.16,a+.008,0),(.04,1.884,.38),lower,wallcol,.006,trim,axes=(1,2))
box('Left_horizontal_sealed_joint',(.16,5.5,.396),(.04,3.8,.022),trim,wallcol)
box('Left_front_edge_return',(.16,5.5,.40),(.04,.025,3.0),trim,wallcol)

# L-section cap closes two exposed cassette edges; chamfer retreats INTO wall.
profile=[(.14,9.12),(.14,9.36),(.38,9.36),(.38,9.30),(.23,9.30),(.2,9.33),(.2,9.12)]
profile.reverse()  # CCW profile gives outward cap and side normals.
n=len(profile)
verts=[(x,y,z) for z in (0,3.4) for x,y in profile]
faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
mesh=bpy.data.meshes.new('Wall_corner_L_return_mesh')
mesh.from_pydata(verts,[],faces)
mesh.update()
corner=bpy.data.objects.new('Wall_corner_L_return_recessed_chamfer',mesh)
wallcol.objects.link(corner)
corner.data.materials.append(trim)
planar_uv(corner)
corner['purpose']='L-section edge closure; diagonal cut retreats into the corner, never reduces clear space'

# One connected neutral form. No lid, head window, layer seams or CAD topology.
p=DATA['pod']
pod=box('P11_ENVELOPE_ONLY_2p30x1p05x1p00',(p['x'],p['y'],0),(p['w'],p['d'],p['h']),podmat,placeholder,.035)
pod['purpose']='neutral scale placeholder ONLY; not a cryopod design candidate'

def camera(name,target,offset,scale):
    data=bpy.data.cameras.new(name)
    data.type='ORTHO'
    data.ortho_scale=scale
    obj=bpy.data.objects.new(name,data)
    review.objects.link(obj)
    target=Vector(target)
    obj.location=target+Vector(offset)
    obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
    return obj
cam=camera('Camera_A_fixed_architectural_candidate',(2.45,7.5,1.35),(4.5,-9,5.15),6.2)
close=camera('Camera_C_wall_floor_material_inspection',(3.8,8.85,.90),(3.4,-5.3,3.0),2.95)
scene.camera=cam
for name,loc,energy,size in [('Review_key',(5,4.5,6),500,4),('Review_fill',(2,6,4),100,3)]:
    data=bpy.data.lights.new(name,'AREA')
    data.energy=energy
    data.size=size
    obj=bpy.data.objects.new(name,data)
    review.objects.link(obj)
    obj.location=loc
    obj.rotation_euler=(Vector((2,7.5,1))-obj.location).to_track_quat('-Z','Y').to_euler()

def capture(name,camera,override=None):
    scene.camera=camera
    scene.view_layers[0].material_override=override
    scene.render.filepath=str(ROOT/'evidence'/name)
    bpy.ops.render.render(write_still=True)
capture('A_target_camera.png',cam)
capture('B_untextured_architecture.png',cam,clay)
capture('C_material_close.png',close)
scene.camera=cam
scene.view_layers[0].material_override=None
scene.render.filepath='//evidence/A_target_camera.png'
scene['authority_commit']=DATA['authority_commit']
scene['design_status']='v2 architectural art trial / REVIEW REQUIRED'
scene['engineering_reference_only']='size, position, wall envelope, top elevation, candidate camera; no CAD geometry imported'
for image in (wallimage,floorimage):
    image.pack()
    image.filepath='//textures/'+Path(image.filepath).name
for area in bpy.context.screen.areas if bpy.context.screen else []:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='CAMERA'
        area.spaces.active.shading.type='RENDERED'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'room1_lowpoly_sample_v2.blend'))
manifest={'status':'REVIEW_REQUIRED','authority_commit':DATA['authority_commit'],
          'textures':{'wall':[96,192],'floor':[96,120]},'texel_density_provisional':64,
          'shading_trial':'EEVEE Diffuse -> ShaderToRGB -> constant 3-level ramp -> pixel color multiply -> Emission; not portable to Godot',
          'render_resolution':[1600,1000],'camera_A_same_as_v1':True,
          'mesh_count':sum(o.type=='MESH' for o in scene.objects),
          'triangle_count':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in scene.objects if o.type=='MESH'),
          'original_designs':['6 modular floor sheets','upper wall cassettes','flush joints and cleanable lower strips','recessed corner L return'],
          'not_validated':['final art acceptance','Godot runtime','global pixel grid','motion stability','boarding','final cryopod design']}
(ROOT/'sample_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('V2_SAMPLE_SAVED',ROOT)
