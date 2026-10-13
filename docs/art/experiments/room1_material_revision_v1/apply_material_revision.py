"""Replace floor/wall review textures only; preserve geometry, UVs and lighting."""
from pathlib import Path
import json
import bpy

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'room1_floor_pixel_compare_v1/floor_A_uniform_v1.blend'
OUT=ROOT/'evidence'
OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene
scene.render.resolution_x=1920
scene.render.resolution_y=1080
scene.render.resolution_percentage=100


def snapshot():
    results={}
    for o in bpy.data.objects:
        item={'type':o.type,'matrix':[list(r) for r in o.matrix_world],
              'hide_render':o.hide_render,'hide_viewport':o.hide_viewport}
        if o.type=='MESH':
            item.update(vertices=[list(v.co) for v in o.data.vertices],
                        faces=[list(p.vertices) for p in o.data.polygons],
                        uvs={l.name:[list(d.uv) for d in l.data] for l in o.data.uv_layers},
                        materials=[m.name if m else None for m in o.data.materials],
                        face_slots=[p.material_index for p in o.data.polygons])
        if o.type=='CAMERA':
            item['camera']=[o.data.type,o.data.lens,o.data.ortho_scale,o.data.shift_x,o.data.shift_y]
        if o.type=='LIGHT':
            item['light']=[o.data.type,o.data.energy,list(o.data.color)]
        results[o.name]=item
    return results


before=snapshot()
views=[('CAM_01_full_room_overview_REVIEW','overview'),
       ('CAM_02_low_angle_CANDIDATE','low_angle'),
       ('CAM_03_top_plan_LAYOUT_ONLY','top_plan'),
       ('CAM_WALL_V1_detail_REVIEW','wall_detail')]


def render_views(prefix):
    for camera,key in views:
        scene.camera=bpy.data.objects[camera]
        scene.render.filepath=str(OUT/f'{prefix}_{key}.png')
        bpy.ops.render.render(write_still=True)


render_views('before')
images={}
for filename in ['floor_albedo.png']+[f'{k}_{kind}.png' for k in ['rear','front','left','right'] for kind in ['albedo','emission']]:
    image=bpy.data.images.load(str(ROOT/'textures'/filename),check_existing=False)
    image.colorspace_settings.name='Non-Color' if 'emission' in filename else 'sRGB'
    image.pack()
    image.filepath='//textures/'+filename
    images[filename]=image

specs={
    'Floor_continuous_no_tile_seams':('floor','FLOOR_PIXEL_COMPARE_V1_'),
    'Wall_rear_left':('rear','WALL_PIXEL_V2_'),
    'Wall_rear_right':('rear','WALL_PIXEL_V2_'),
    'Wall_rear_door_header':('rear','WALL_PIXEL_V2_'),
    'Wall_front':('front','WALL_PIXEL_V2_'),
    'Wall_left':('left','WALL_PIXEL_V2_'),
    'Wall_right':('right','WALL_PIXEL_V2_'),
}
copies={}
changes=[]
for name,(key,prefix) in specs.items():
    obj=bpy.data.objects[name]
    replaced=[]
    for index,mat in enumerate(obj.data.materials):
        if mat and mat.name.startswith(prefix):
            if mat.name not in copies:
                revised=mat.copy()
                revised.name='MATERIAL_REVISION_V1_'+key
                found=0
                for node in revised.node_tree.nodes:
                    if node.type=='TEX_IMAGE' and node.image:
                        original=Path(node.image.filepath).name
                        if '_albedo' in original:
                            node.image=images[key+'_albedo.png'];found+=1
                        elif '_emission' in original:
                            node.image=images[key+'_emission.png'];found+=1
                expected=1 if key=='floor' else 2
                if found!=expected:raise RuntimeError(f'{name}: expected {expected} image nodes, got {found}')
                revised['STATUS']='Uniform floor / material-time wall finish; awaiting review.'
                copies[mat.name]=revised
            obj.data.materials[index]=copies[mat.name]
            replaced.append(index)
    if not replaced:raise RuntimeError('No candidate slot replaced on '+name)
    changes.append({'object':name,'material_slots':replaced,'texture_key':key})

after=snapshot()
if before.keys()!=after.keys():raise RuntimeError('Object inventory changed')
for name,old in before.items():
    new=after[name].copy();old=old.copy()
    if name in specs:
        old.pop('materials',None);new.pop('materials',None)
    if old!=new:raise RuntimeError('Out-of-scope structural change on '+name)

scene['STATUS']='Uniform A selected; revised floor/wall material finish awaiting review.'
scene['SCOPE']='Only existing floor/wall texture material slots replaced. No geometry, UV, camera or light changes.'
scene['WALL_HISTORY']='No old AI age patch layer; low-contrast coating, protected edge deposits and band contact illustrations.'
scene['LIGHTING_LIMIT']='Inherited review illumination; continuous 22.5cm pale blue-white diffuser/mask unchanged. Godot lighting not validated.'
render_views('after')
scene.camera=bpy.data.objects['CAM_01_full_room_overview_REVIEW']
scene.render.filepath='//evidence/after_overview.png'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'room1_material_revision_v1.blend'))
(ROOT/'structural_readback.json').write_text(json.dumps({
    'source':SOURCE.name,'source_object_count':len(before),
    'geometry_transforms_visibility_and_uv_unchanged':True,
    'cameras_and_lights_unchanged':True,
    'all_other_objects_unchanged':True,'new_objects':[],
    'floor_and_wall_changes':changes,
    'scope':'Generation guard and rendered review only, not art approval or Godot runtime validation.'
},indent=2),encoding='utf-8')
print('MATERIAL_REVISION_SAVED')
