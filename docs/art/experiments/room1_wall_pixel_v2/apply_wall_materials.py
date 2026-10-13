"""Apply wall-only pixel art and emission masks to a new review .blend.

Source geometry, floor, pods, door, lights and source cameras are retained.
New planar wall UVs are appended; the existing packed UVs are retained.
"""
from pathlib import Path
import json
import sys
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'room1_wall_pixel_v1/room1_wall_pixel_v1.blend'
OUT=ROOT/'evidence'
OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene

def snapshot_objects():
    return {o.name:{'matrix':[list(row) for row in o.matrix_world],
        'vertices':[list(v.co) for v in o.data.vertices] if o.type=='MESH' else None,
        'polygons':[list(p.vertices) for p in o.data.polygons] if o.type=='MESH' else None,
        'uvs':{l.name:[list(d.uv) for d in l.data] for l in o.data.uv_layers} if o.type=='MESH' else None,
        'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else None,
        'hide_render':o.hide_render,
        } for o in bpy.data.objects}

before=snapshot_objects()
manifest=json.loads((ROOT/'textures/manifest.json').read_text())
UV='UV_WALL_PIXEL_V2_PLANAR'

def linear_color(hexcode):
    rgb=[int(hexcode[i:i+2],16)/255. for i in (1,3,5)]
    return tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb)+(1,)

BLUE_WHITE='#CCDDE4'
SOFT_WHITE='#EAEBDF'

def load_image(filename,noncolor=False):
    image=bpy.data.images.load(str(ROOT/'textures'/filename),check_existing=False)
    image.colorspace_settings.name='Non-Color' if noncolor else 'sRGB'
    image.pack()
    image.filepath='//textures/'+filename
    return image

def make_material(key):
    mat=bpy.data.materials.new('WALL_PIXEL_V2_'+key)
    mat.use_nodes=True
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    shader=nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value=.95
    shader.inputs['Specular IOR Level'].default_value=.08
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map=UV
    tex=nodes.new('ShaderNodeTexImage');tex.image=load_image(key+'_albedo.png')
    tex.interpolation='Closest';tex.extension='EXTEND'
    mask=nodes.new('ShaderNodeTexImage');mask.image=load_image(key+'_emission.png',True)
    mask.interpolation='Closest';mask.extension='EXTEND'
    strength=nodes.new('ShaderNodeMath');strength.operation='MULTIPLY'
    strength.inputs[1].default_value=.65
    color=nodes.new('ShaderNodeRGB');color.name='DIFFUSER_COLOR'
    color.label='Wide diffuser tint: pale blue-white trial'
    color.outputs[0].default_value=linear_color(BLUE_WHITE)
    luminance=nodes.new('ShaderNodeRGBToBW')
    normalize=nodes.new('ShaderNodeMath');normalize.operation='DIVIDE'
    reference=linear_color(BLUE_WHITE)
    normalize.inputs[1].default_value=.2126*reference[0]+.7152*reference[1]+.0722*reference[2]
    lit_face=nodes.new('ShaderNodeMixRGB');lit_face.blend_type='MULTIPLY'
    lit_face.inputs[0].default_value=1
    mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX'
    links.new(uv.outputs['UV'],tex.inputs['Vector'])
    links.new(uv.outputs['UV'],mask.inputs['Vector'])
    links.new(tex.outputs['Color'],luminance.inputs[0])
    links.new(luminance.outputs[0],normalize.inputs[0])
    links.new(color.outputs[0],lit_face.inputs[1])
    links.new(normalize.outputs[0],lit_face.inputs[2])
    links.new(mask.outputs['Color'],mix.inputs[0])
    links.new(tex.outputs['Color'],mix.inputs[1])
    links.new(lit_face.outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],shader.inputs['Base Color'])
    links.new(color.outputs[0],shader.inputs['Emission Color'])
    links.new(mask.outputs['Color'],strength.inputs[0])
    links.new(strength.outputs[0],shader.inputs['Emission Strength'])
    mat['STATUS']='Wall v2: wide 22.5cm diffuser; pale gray cyan-white trial; native pixel history and integrated trim.'
    mat['LIGHTING_LIMIT']='Eevee material emission only; no added light objects, no final emergency room illumination/Godot implementation.'
    return mat

materials={key:make_material(key) for key in manifest['maps']}

def set_diffuser_tint(hexcode):
    for mat in materials.values():
        mat.node_tree.nodes['DIFFUSER_COLOR'].outputs[0].default_value=linear_color(hexcode)
        mat['DIFFUSER_TINT_TRIAL']=hexcode

set_diffuser_tint(BLUE_WHITE)
specs={
 'Wall_rear_left':('rear',0,0.,21.,Vector((0,-1,0))),
 'Wall_rear_right':('rear',0,0.,21.,Vector((0,-1,0))),
 'Wall_rear_door_header':('rear',0,0.,21.,Vector((0,-1,0))),
 'Wall_front':('front',0,0.,21.,Vector((0,1,0))),
 'Wall_left':('left',1,.2,9.1,Vector((1,0,0))),
 'Wall_right':('right',1,.2,9.1,Vector((-1,0,0))),
}

def render(cam,name):
    scene.camera=bpy.data.objects[cam]
    scene.render.filepath=str(OUT/name)
    bpy.ops.render.render(write_still=True)

if '--reuse-baseline' not in sys.argv or not (OUT/'00_v1_wall_baseline.png').exists():
    render('CAM_01_full_room_overview_REVIEW','00_v1_wall_baseline.png')
changed=[]
for name,(key,axis,offset,length,inner_normal) in specs.items():
    obj=bpy.data.objects[name];mesh=obj.data
    layer=mesh.uv_layers.new(name=UV);layer.active_render=True
    for polygon in mesh.polygons:
        for idx in polygon.loop_indices:
            vertex=obj.matrix_world @ mesh.vertices[mesh.loops[idx].vertex_index].co
            layer.data[idx].uv=((vertex[axis]-offset)/length,vertex.z/3.4)
    slot=len(mesh.materials);mesh.materials.append(materials[key])
    faces=[]
    for polygon in mesh.polygons:
        normal=(obj.matrix_world.to_3x3() @ polygon.normal).normalized()
        if normal.dot(inner_normal)>.99:
            polygon.material_index=slot;faces.append(polygon.index)
    obj['wall_pixel_v2']='Interior face only; append planar UV, retain geometry and source packed UV.'
    changed.append({'object':name,'texture':key,'interior_face_indices':faces})

after=snapshot_objects()
geometry_ok=all(before[name]['matrix']==after[name]['matrix'] and
    before[name]['vertices']==after[name]['vertices'] and
    before[name]['polygons']==after[name]['polygons'] and
    before[name]['hide_render']==after[name]['hide_render'] for name in before)
uv_ok=all(after[name]['uvs'].get(k)==v for name in before if before[name]['uvs']
    for k,v in before[name]['uvs'].items())
nonwall_ok=all(before[name]==after[name] for name in before if name not in specs)
if not (geometry_ok and uv_ok and nonwall_ok):
    raise RuntimeError('Wall-only scope readback failed')

# Reuse the v1 material inspection camera for a like-for-like comparison.
scene['STATUS']='Room1 wall pixel v2: confirmed material/trim/light-strip design, awaiting visual review.'
scene['SCOPE']='Wall interior materials and appended UV only; floor/pods/door/source geometry/lights/cameras retained.'
scene['LIGHT_STRIP']='Continuous upper 22.5cm recessed diffuser, pale gray cyan-white trial; material self emission; final illumination TBD.'
scene.camera=bpy.data.objects['CAM_01_full_room_overview_REVIEW']
scene.render.filepath='//evidence/01_wall_overview.png'
destination=ROOT/'room1_wall_pixel_v2.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(destination))
for camera,filename in [
 ('CAM_01_full_room_overview_REVIEW','01_wall_overview.png'),
 ('CAM_02_low_angle_CANDIDATE','02_wall_low_angle.png'),
 ('CAM_WALL_V1_detail_REVIEW','03_wall_detail.png')]:
    render(camera,filename)
set_diffuser_tint(SOFT_WHITE)
render('CAM_01_full_room_overview_REVIEW','04_white_light_comparison.png')
render('CAM_WALL_V1_detail_REVIEW','05_white_light_detail.png')
set_diffuser_tint(BLUE_WHITE)
scene.camera=bpy.data.objects['CAM_01_full_room_overview_REVIEW']
scene.render.filepath='//evidence/01_wall_overview.png'
bpy.ops.wm.save_as_mainfile(filepath=str(destination))
(ROOT/'structural_readback.json').write_text(json.dumps({
 'source':str(SOURCE.name),'source_object_count':len(before),
 'source_geometry_transforms_visibility_unchanged':geometry_ok,
 'source_uv_layers_unchanged':uv_ok,'all_nonwall_objects_unchanged':nonwall_ok,
 'floor_pods_door_lights_and_source_cameras_unchanged':nonwall_ok,
 'new_objects':[],
 'wall_material_changes':changed,
 'scope':'Structural readback and review images only; not Godot runtime/lighting validation.'
},indent=2),encoding='utf-8')
print('WALL_CANDIDATE_SAVED',destination)
