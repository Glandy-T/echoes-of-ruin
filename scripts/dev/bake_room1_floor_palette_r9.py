"""Rebake unchanged r6 walls and r9 neutral-cool floor palette into preserved r4 geometry/UV2."""
import bpy, hashlib, json, os, runpy, shutil, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OLD=ROOT/'assets/art/room1_wall_finish_r4'
OUT=ROOT/'assets/art/room1_floor_palette_r9'
HERE=ROOT/'docs/art/experiments/room1_floor_palette_r9'
OUT.mkdir(parents=True,exist_ok=True);HERE.mkdir(parents=True,exist_ok=True)
if (OUT/'strip_irradiance_denoised.exr').exists() and os.environ.get('ROOM1_FLOOR_PALETTE_R9_ALLOW_OVERWRITE')!='1':raise RuntimeError('r9 exists: preserve completed results; explicit local rebuild requires ROOM1_FLOOR_PALETTE_R9_ALLOW_OVERWRITE=1')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'docs/art/experiments/room1_wall_finish_r4/room1_wall_finish_r4_packed.blend'))
scene=bpy.context.scene
receivers=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Bake_') and not o.hide_render]
assert len(receivers)==129
def geometry_hash(objects):
    h=hashlib.sha256()
    for obj in sorted(objects,key=lambda x:x.name):
        h.update(obj.name.encode());h.update(repr([tuple(r) for r in obj.matrix_world]).encode())
        for v in obj.data.vertices:h.update(repr(tuple(v.co)).encode())
        for p in obj.data.polygons:h.update(repr((tuple(p.vertices),p.material_index,p.use_smooth)).encode())
        for layer in obj.data.uv_layers:
            h.update(layer.name.encode())
            for uv in layer.data:h.update(repr(tuple(uv.uv)).encode())
    return h.hexdigest()
before=geometry_hash(receivers)
emitters=[o for o in bpy.data.objects if o.name.startswith('ContinuousRibbon_')]
assert len(emitters)==4
def emitter_record():
    return [{'name':o.name,'matrix':[list(r) for r in o.matrix_world],'vertices':[list(v.co) for v in o.data.vertices],
       'materials':[{'name':m.name,'nodes':[{'type':n.bl_idname,'inputs':{i.name:(list(i.default_value) if hasattr(i.default_value,'__iter__') else i.default_value) for i in n.inputs if hasattr(i,'default_value')}} for n in m.node_tree.nodes]} for m in o.data.materials]} for o in emitters]
emit_before=emitter_record()
maps={'Bake_Shell_Floor_continuous_no_tile_seams':('floor','assets/art/room1_floor_palette_r9/floor_with_leaks.png'),
 'Bake_Shell_Wall_left':('side','assets/art/room1_seam_contact_r6/wall_left.png'),
 'Bake_Shell_Wall_right':('side','assets/art/room1_seam_contact_r6/wall_right.png'),
 'Bake_Shell_Wall_front':('wall','assets/art/room1_seam_contact_r6/wall_front.png'),
 'Bake_Shell_Wall_rear_left':('wall','assets/art/room1_seam_contact_r6/wall_rear.png'),
 'Bake_Shell_Wall_rear_right':('wall','assets/art/room1_seam_contact_r6/wall_rear.png'),
 'Bake_Shell_Wall_rear_door_header':('wall','assets/art/room1_seam_contact_r6/wall_rear.png')}
material_records=[]
def math_node(nodes,links,op,a,b=None):
    n=nodes.new('ShaderNodeMath');n.operation=op
    for idx,val in enumerate([a,b]):
        if val is None:continue
        if isinstance(val,(float,int)):n.inputs[idx].default_value=val
        else:links.new(val,n.inputs[idx])
    return n.outputs[0]
for name,(kind,path) in maps.items():
    obj=bpy.data.objects.get(name);assert obj is not None,name
    slots=0
    for slot in obj.material_slots:
        old=slot.material
        if old is None or 'MATERIAL_REVISION' not in old.name:continue
        material=old.copy();material.name=old.name+'_R7_'+name.removeprefix('Bake_Shell_');slot.material=material
        nodes=material.node_tree.nodes;links=material.node_tree.links
        bsdf=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
        original=bsdf.inputs['Base Color'].links[0].from_socket if bsdf.inputs['Base Color'].is_linked else None
        geometry=nodes.new('ShaderNodeNewGeometry');position=nodes.new('ShaderNodeSeparateXYZ');links.new(geometry.outputs['Position'],position.inputs[0])
        normal=nodes.new('ShaderNodeSeparateXYZ');links.new(geometry.outputs['Normal'],normal.inputs[0])
        axis='Y' if kind=='side' else 'X';span=9.1 if kind=='side' else 20.6
        u=math_node(nodes,links,'DIVIDE',math_node(nodes,links,'SUBTRACT',position.outputs[axis],.2),span)
        if kind=='floor':v=math_node(nodes,links,'DIVIDE',math_node(nodes,links,'SUBTRACT',position.outputs['Y'],.2),9.1)
        else:v=math_node(nodes,links,'DIVIDE',position.outputs['Z'],3.4)
        combine=nodes.new('ShaderNodeCombineXYZ');links.new(u,combine.inputs['X']);links.new(v,combine.inputs['Y'])
        texture=nodes.new('ShaderNodeTexImage');texture.name='R7_WORLD_PIXEL_COLOR';texture.label=path
        texture.image=bpy.data.images.load(str(ROOT/path),check_existing=True);texture.image.colorspace_settings.name='sRGB';texture.image.pack()
        texture.interpolation='Closest';texture.extension='EXTEND';links.new(combine.outputs[0],texture.inputs['Vector'])
        valid=math_node(nodes,links,'MULTIPLY',math_node(nodes,links,'GREATER_THAN',u,-.000001),math_node(nodes,links,'LESS_THAN',u,1.000001))
        valid=math_node(nodes,links,'MULTIPLY',valid,math_node(nodes,links,'GREATER_THAN',v,-.000001))
        valid=math_node(nodes,links,'MULTIPLY',valid,math_node(nodes,links,'LESS_THAN',v,1.000001))
        if kind=='floor':valid=math_node(nodes,links,'MULTIPLY',valid,math_node(nodes,links,'GREATER_THAN',normal.outputs['Z'],.9))
        mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';links.new(valid,mix.inputs[0]);links.new(texture.outputs['Color'],mix.inputs[2])
        if original:links.new(original,mix.inputs[1])
        else:mix.inputs[1].default_value=bsdf.inputs['Base Color'].default_value
        links.new(mix.outputs[0],bsdf.inputs['Base Color'])
        slots+=1;material_records.append({'object':name,'material':material.name,'kind':kind,'color_map':path,'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),'sampling':'Closest sRGB, world projection, preserve original outside inner-face range'})
    assert slots>0,name
assert before==geometry_hash(receivers)
assert emit_before==emitter_record()
layout=runpy.run_path(str(ROOT/'scripts/dev/room1_uv2_audit.py'))['audit_uv2_layout'](receivers)
for key in ['uv_degenerate_triangle_count','positive_area_overlap_count','out_of_atlas_vertex_count']:assert layout[key]==0,(key,layout[key])
assert layout['uv_non_degenerate_triangle_count']==layout['geometry_non_degenerate_triangle_count']
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1024;scene.cycles.use_adaptive_sampling=False
scene.cycles.max_bounces=3;scene.cycles.diffuse_bounces=2
scene.render.bake.use_pass_color=False;scene.render.bake.use_pass_direct=True;scene.render.bake.use_pass_indirect=True;scene.render.bake.margin=4
image=bpy.data.images.new('FloorPaletteR9Irradiance',width=2048,height=2048,alpha=False,float_buffer=True);image.colorspace_settings.name='Non-Color'
for material in {s.material for o in receivers for s in o.material_slots if s.material}:
    node=material.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;material.node_tree.nodes.active=node
bpy.ops.object.select_all(action='DESELECT');copies=[]
for original in receivers:
    copy=original.copy();copy.data=original.data.copy();copy.parent=None;copy.matrix_world=original.matrix_world.copy()
    bpy.context.collection.objects.link(copy);copy.hide_render=False;copy.select_set(True);original.hide_render=True;copies.append(copy)
bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();joined=bpy.context.object
joined.data.uv_layers.active_index=list(joined.data.uv_layers).index(joined.data.uv_layers['LightmapUV']);joined.data.uv_layers['LightmapUV'].active_render=True
print('FLOOR_PALETTE_R9_BAKE_BEGIN 1024 samples, unchanged UV2/emitters, latest albedo',flush=True)
started=time.monotonic();bpy.ops.object.bake(type='DIFFUSE',pass_filter={'DIRECT','INDIRECT'},uv_layer='LightmapUV',use_clear=True,margin=4);elapsed=time.monotonic()-started
bpy.data.objects.remove(joined,do_unlink=True)
for original in receivers:original.hide_render=False
assert before==geometry_hash(receivers);assert emit_before==emitter_record()
image.filepath_raw=str(OUT/'strip_irradiance.exr');image.file_format='OPEN_EXR';image.save();image.pack()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'room1_floor_palette_r9_packed.blend'),compress=True,check_existing=False)
for file in ['room1_baked_uv2_r3.glb','mesh_mapping.json','uv2_layout_record.json']:shutil.copyfile(OLD/file,OUT/file)
manifest=json.loads((OLD/'bake_manifest.json').read_text(encoding='utf-8'));manifest.update({'bake_seconds':elapsed,'blender':bpy.app.version_string,'geometry_source':'assets/art/room1_wall_finish_r4/room1_baked_uv2_r3.glb','geometry_sha256':hashlib.sha256((OUT/'room1_baked_uv2_r3.glb').read_bytes()).hexdigest(),'source_geometry_uv_hash':before,'source_geometry_uv_preserved':before==geometry_hash(receivers),'emitters_preserved':True,'albedo_sources':material_records,'scope':'Unchanged r6 walls / r9 cool-neutral floor, preserving r8 contact/deposit silhouettes and four leak positions drive diffuse indirect bounce. Irradiance excludes receiving albedo. Original geometry, UV0/UV2, emitters and Godot lighting parameters retained; no global brightening.'})
(OUT/'bake_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(HERE/'source_scope.json').write_text(json.dumps({'geometry_uv_before':before,'geometry_uv_after':geometry_hash(receivers),'emitter_before':emit_before,'emitter_after':emitter_record(),'material_changes':material_records,'uv2_audit':layout},ensure_ascii=False,indent=2),encoding='utf-8')
os.environ['ROOM1_BAKE_OUTPUT']=str(OUT.relative_to(ROOT));runpy.run_path(str(ROOT/'scripts/dev/denoise_room1_strip_r3.py'),run_name='__main__')
print('FLOOR_PALETTE_R9_COMPLETE',elapsed,flush=True)
