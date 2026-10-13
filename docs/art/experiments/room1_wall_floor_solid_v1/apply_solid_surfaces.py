"""Material-only review copy; source geometry, transforms, UVs and lights remain.
Blender --background --factory-startup --python apply_solid_surfaces.py
"""
from pathlib import Path
import bpy
import json

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'room1_full_lowpoly_v1_1'/'room1_full_lowpoly_v1_1.blend'
OUT=ROOT/'evidence'
OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene

def snapshot():
    # Structural readback, not runtime or artistic acceptance.
    return {o.name:{'type':o.type,'matrix':list(sum((list(r) for r in o.matrix_world),[])),
        'vertices':[list(v.co) for v in o.data.vertices] if o.type=='MESH' else None,
        'polygons':[list(p.vertices) for p in o.data.polygons] if o.type=='MESH' else None,
        'uvs':{l.name:[list(d.uv) for d in l.data] for l in o.data.uv_layers} if o.type=='MESH' else None,
        } for o in bpy.data.objects}

before=snapshot()
settings=(scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage)

def render(cam,name):
    scene.camera=bpy.data.objects[cam]
    scene.render.filepath=str(OUT/name)
    bpy.ops.render.render(write_still=True)

render('CAM_01_full_room_overview_REVIEW','00_original_overview.png')

def material(name,mapname):
    image=bpy.data.images.load(str(ROOT/'textures'/mapname))
    image.colorspace_settings.name='sRGB'
    image.pack()
    image.filepath='//textures/'+mapname
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    shader=mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value=.9
    shader.inputs['Specular IOR Level'].default_value=.15
    texture=mat.node_tree.nodes.new('ShaderNodeTexImage')
    texture.image=image
    texture.interpolation='Closest'
    texture.extension='REPEAT'
    mat.node_tree.links.new(texture.outputs['Color'],shader.inputs['Base Color'])
    mat['STATUS']='Continuous single-color albedo, no panel seams or surface patterns; temporary review.'
    return mat

replacements={
    'ARCH_wall_flat_review_only':material('TRIAL_SOLID_wall_ivory','wall_solid.png'),
    'ARCH_floor_flat_review_only':material('TRIAL_SOLID_floor_slate','floor_solid.png'),
}
changed=[]
seen_meshes=set()
for obj in bpy.data.objects:
    if obj.type!='MESH' or obj.data in seen_meshes:
        continue
    seen_meshes.add(obj.data)
    for i,old in enumerate(obj.data.materials):
        if old and old.name in replacements:
            obj.data.materials[i]=replacements[old.name]
            changed.append({'object':obj.name,'old_material':old.name,'new_material':obj.data.materials[i].name})

after=snapshot()
if before!=after:
    raise RuntimeError('Source geometry/transforms/UVs unexpectedly changed')
if not changed:
    raise RuntimeError('Expected architecture materials were not found')
scene['STATUS']='Room1 continuous solid wall/floor v1; user requested material-only trial.'
scene['COLOR_SCOPE']='Temporary colors sampled from accepted single-pod v2; gray pods remain source reference.'
scene['API_STATUS']='Official REST generation checked separately; solid maps are deterministic, not generated AI textures.'
scene.camera=bpy.data.objects['CAM_01_full_room_overview_REVIEW']
scene.render.filepath='//evidence/01_solid_overview.png'
target=ROOT/'room1_wall_floor_solid_v1.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(target))
for cam,name in [
    ('CAM_01_full_room_overview_REVIEW','01_solid_overview.png'),
    ('CAM_02_low_angle_CANDIDATE','02_solid_low_angle.png'),
    ('CAM_03_top_plan_LAYOUT_ONLY','03_solid_top_plan.png'),
]:
    render(cam,name)
scene.camera=bpy.data.objects['CAM_01_full_room_overview_REVIEW']
scene.render.filepath='//evidence/01_solid_overview.png'
bpy.ops.wm.save_as_mainfile(filepath=str(target))
(ROOT/'structural_readback.json').write_text(json.dumps({
    'source':SOURCE.name,'geometry_transforms_uvs_unchanged':before==after,
    'object_count':len(before),'material_changes':changed,
    'render_settings':settings,
    'scope':'structural comparison only; no Godot runtime test or artistic approval',
},indent=2),encoding='utf-8')
print('SOLID_SURFACE_REVIEW_SAVED',target)
