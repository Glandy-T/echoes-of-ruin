"""Export portable GLBs from a temporary Blender copy; source .blend stays intact."""
from pathlib import Path
import json
import struct
import bpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'godot_export';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'room1_material_revision_v1.blend'))
bpy.context.scene.frame_set(1)
architecture_names=['Floor_continuous_no_tile_seams','Wall_rear_left','Wall_rear_right',
                    'Wall_rear_door_header','Wall_front','Wall_left','Wall_right',
                    'Roof_hidden_for_cutaway','MAIN_DOOR_PLACEHOLDER_NOT_APPROVED']
objects=[o for o in bpy.data.objects if o.type=='MESH' and
         (o.name in architecture_names or any(c.name.startswith('04_PODS_20_') for c in o.users_collection))]
source_render_visible={o.name:(not o.hide_render and
    all(not c.hide_render for c in o.users_collection)) for o in objects}
for collection in bpy.data.collections:
    collection.hide_viewport=False
    collection.hide_render=False
def unhide(layer):
    layer.exclude=False;layer.hide_viewport=False
    for child in layer.children:unhide(child)
unhide(bpy.context.view_layer.layer_collection)
bpy.context.view_layer.update()
material_cache={}
uv_records=[]


def export_material(original):
    if original.name in material_cache:return material_cache[original.name]
    mat=bpy.data.materials.new('GODOT_'+original.name)
    mat.use_nodes=True
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    shader=nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value=.95
    shader.inputs['Specular IOR Level'].default_value=.08
    source_nodes=original.node_tree.nodes if original.use_nodes else []
    source_shader=next((n for n in source_nodes if n.type=='BSDF_PRINCIPLED'),None)
    if source_shader:
        for prop in ['Base Color','Roughness','Metallic','Specular IOR Level']:
            shader.inputs[prop].default_value=source_shader.inputs[prop].default_value
    else:shader.inputs['Base Color'].default_value=original.diffuse_color
    for old in source_nodes:
        if old.type!='TEX_IMAGE' or not old.image:continue
        filename=Path(old.image.filepath).name
        texture=nodes.new('ShaderNodeTexImage');texture.image=old.image
        texture.interpolation='Closest';texture.extension='EXTEND'
        uv=nodes.new('ShaderNodeUVMap');uv.uv_map='UV_GODOT_0'
        links.new(uv.outputs['UV'],texture.inputs['Vector'])
        if '_emission' not in filename:links.new(texture.outputs['Color'],shader.inputs['Base Color'])
        else:
            # Export RGB emission explicitly; no unsupported procedural mix.
            color_file=ROOT/'textures'/filename.replace('_emission','_emissive_color')
            texture.image=bpy.data.images.load(str(color_file),check_existing=True)
            texture.image.colorspace_settings.name='sRGB'
            links.new(texture.outputs['Color'],shader.inputs['Emission Color'])
            shader.inputs['Emission Color'].default_value=(1,1,1,1)
            shader.inputs['Emission Strength'].default_value=.65
    material_cache[original.name]=mat
    return mat


for obj in objects:
    obj.data=obj.data.copy()
    mesh=obj.data
    # Collapse material-specific source UVs into UV0 per loop. Game engines need
    # a single usable exported set; never discard the active coating UV by index.
    values=[(0.,0.) for _ in mesh.loops]
    used=set()
    for polygon in mesh.polygons:
        source=mesh.materials[polygon.material_index]
        uv_name=None
        if source and source.use_nodes:
            uv_name=next((n.uv_map for n in source.node_tree.nodes if n.type=='UVMAP'),None)
        layer=mesh.uv_layers.get(uv_name) if uv_name else mesh.uv_layers.active
        if layer:
            used.add(layer.name)
            for idx in polygon.loop_indices:values[idx]=tuple(layer.data[idx].uv)
    while len(mesh.uv_layers):mesh.uv_layers.remove(mesh.uv_layers[0])
    layer=mesh.uv_layers.new(name='UV_GODOT_0');layer.active_render=True
    for i,value in enumerate(values):layer.data[i].uv=value
    for index,old in enumerate(list(mesh.materials)):
        if old:mesh.materials[index]=export_material(old)
    obj.hide_render=False;obj.hide_viewport=False;obj.hide_set(False)
    uv_records.append({'object':obj.name,'source_uvs_used':sorted(used),'export_uv':'UV_GODOT_0'})


def export(filename,chosen):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in chosen:obj.select_set(True)
    bpy.context.view_layer.objects.active=chosen[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT/filename),export_format='GLB',
        use_selection=True,use_visible=False,use_renderable=False,
        export_materials='EXPORT',export_texcoords=True,export_normals=True,
        export_cameras=False,export_lights=False,export_animations=False,
        export_image_format='AUTO',export_keep_originals=False,export_yup=True)
    data=(OUT/filename).read_bytes()
    length,kind=struct.unpack_from('<II',data,12)
    if kind!=0x4e4f534a:raise RuntimeError('Missing GLB JSON chunk')
    doc=json.loads(data[20:20+length])
    records={'file':filename,'bytes':len(data),'export_object_names':[o.name for o in chosen],
        'meshes':len(doc.get('meshes',[])),'materials':len(doc.get('materials',[])),
        'embedded_images':all('bufferView' in i for i in doc.get('images',[])),
        'images':len(doc.get('images',[])),'samplers':doc.get('samplers',[]),
        'cameras':len(doc.get('cameras',[])),'animations':len(doc.get('animations',[])),
        'texture_coordinate_attributes':sorted({a for m in doc.get('meshes',[]) for p in m['primitives'] for a in p['attributes'] if a.startswith('TEXCOORD_')})}
    (OUT/(filename+'.json')).write_text(json.dumps(records,indent=2),encoding='utf-8')
    return records


records=[]
records.append(export('room1_shell_full_r1.glb',[o for o in objects if o.name in architecture_names]))
records.append(export('room1_layout_review_r1.glb',[o for o in objects if source_render_visible[o.name]]))
(OUT/'manifest.json').write_text(json.dumps({
    'source':'room1_material_revision_v1.blend','units':'meters',
    'axis_conversion':'Blender (x,y,z) -> glTF/Godot (x,z,-y)',
    'original_blend_modified':False,'materials':'Principled + image textures; no lighting bake',
    'uv_repack':'per-face material UV copied to UV0 in temporary export meshes',
    'nearest_note':'Sampler uses nearest; bind provided Godot post-import script for no-mipmap nearest.',
    'scope':'Full shell includes original hidden front/left/roof; layout review retains original cutaway and gray pod placeholders.',
    'collisions_or_navigation':'not created; tomorrow integrate deliberately',
    'files':records,'uv_records':uv_records,
},indent=2),encoding='utf-8')
print('ROOM_GLB_EXPORT_COMPLETE')
