"""Build the Room 1 reusable standard cryopod v8 from the approved v4 source.

This keeps the v4 silhouette, packed pixel source maps and color UVs.  It adds
only the approved fixed interior side-tube fixtures, exposes stable node and
material keys for Godot, and exports one animated GLB plus closed/open static
pose GLBs for local irradiance baking.
"""
from pathlib import Path
import json, struct, hashlib, runpy
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[3]
SOURCE = REPO / 'docs/art/experiments/room1_pod_volume_v4/room1_pod_volume_v4.blend'
OUT_BLEND = HERE / 'room1_pod_standard_v8_packed.blend'
OUT = REPO / 'assets/art/cryopod_standard_v8'
OUT.mkdir(parents=True, exist_ok=True)
REPORT = HERE / 'source' / 'standard_v8_validation.json'
CONTRACT = HERE / 'source' / 'godot_contract.json'

LID_END = Vector((.6115432978, 0.0, .641924))
# Compact 12cm clearance stage; sampled world-space clearance is recorded.
# This is not a claim that 12cm is a mathematically minimal lift.
LID_LIFT = Vector((0.0, 0.0, .670000))
TUBE_SPECS = {
    'PodTubeHousing_L': ((-.458, 0, .310), (.016, 1.740, .034), 'POD_V8_tube_housing'),
    'PodTubeHousing_R': (( .458, 0, .310), (.016, 1.740, .034), 'POD_V8_tube_housing'),
    'PodTubeDiffuser_L': ((-.447, 0, .310), (.006, 1.700, .022), 'POD_V8_tube_diffuser'),
    'PodTubeDiffuser_R': (( .447, 0, .310), (.006, 1.700, .022), 'POD_V8_tube_diffuser'),
}
MATERIAL_KEYS = ('lid','shell_side','shell_end','interior','mattress','glass','display','section','tube_housing','tube_diffuser')

def require(value, text):
    if not value: raise RuntimeError(text)
    return value

def glb_json(path):
    raw = path.read_bytes()
    return json.loads(raw[20:20 + struct.unpack_from('<I', raw, 12)[0]])

def make_box(name, center, size, material, parent):
    cx,cy,cz=center; sx,sy,sz=(v*.5 for v in size)
    verts=[(cx-sx,cy-sy,cz-sz),(cx+sx,cy-sy,cz-sz),(cx+sx,cy+sy,cz-sz),(cx-sx,cy+sy,cz-sz),
           (cx-sx,cy-sy,cz+sz),(cx+sx,cy-sy,cz+sz),(cx+sx,cy+sy,cz+sz),(cx-sx,cy+sy,cz+sz)]
    faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    mesh=bpy.data.meshes.new(name+'_mesh'); mesh.from_pydata(verts,[],faces); mesh.materials.append(material); mesh.update()
    obj=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(obj); obj.parent=parent
    return obj

def append_uv0(mesh):
    if mesh.uv_layers: return mesh.uv_layers[0]
    uv=mesh.uv_layers.new(name='UV_GODOT_0')
    for poly in mesh.polygons:
        for n,li in enumerate(poly.loop_indices): uv.data[li].uv=((0,0),(1,0),(1,1),(0,1))[n%4]
    return uv

def clone_renamed_materials():
    mats={}
    for old in list(bpy.data.materials):
        name=old.name
        if name.startswith('POD_V4_'):
            key=name.removeprefix('POD_V4_')
            if key in MATERIAL_KEYS:
                old.name='POD_V8_'+key
                old['asset_material_key']=key
                mats[key]=old
    for key in MATERIAL_KEYS[:8]: require(mats.get(key), 'missing v4 material '+key)
    housing=bpy.data.materials.new('POD_V8_tube_housing'); housing.use_nodes=True; housing['asset_material_key']='tube_housing'
    hn=housing.node_tree.nodes; hl=housing.node_tree.links; hn.clear(); hout=hn.new('ShaderNodeOutputMaterial'); bsdf=hn.new('ShaderNodeBsdfPrincipled'); hl.new(bsdf.outputs['BSDF'],hout.inputs['Surface']); bsdf.inputs['Base Color'].default_value=(.08,.13,.15,1); bsdf.inputs['Roughness'].default_value=.62
    diffuser=bpy.data.materials.new('POD_V8_tube_diffuser'); diffuser.use_nodes=True; diffuser['asset_material_key']='tube_diffuser'
    n=diffuser.node_tree.nodes; l=diffuser.node_tree.links; n.clear(); out=n.new('ShaderNodeOutputMaterial'); emit=n.new('ShaderNodeEmission'); emit.inputs['Color'].default_value=(.58,.76,.80,1); emit.inputs['Strength'].default_value=.55; l.new(emit.outputs[0],out.inputs[0])
    mats['tube_housing']=housing; mats['tube_diffuser']=diffuser
    return mats

def set_parent_keep_world(obj, parent):
    matrix=obj.matrix_world.copy(); obj.parent=parent; obj.matrix_parent_inverse=parent.matrix_world.inverted(); obj.matrix_world=matrix

def empty(name, parent=None):
    obj=bpy.data.objects.new(name,None); bpy.context.collection.objects.link(obj)
    if parent: set_parent_keep_world(obj,parent)
    return obj

def setup_nodes(mats):
    # v4's actual approved geometry remains untouched; only its runtime names
    # and parent hierarchy are normalized.
    lid=require(bpy.data.objects.get('ONE_PIECE_COVER_head_window'),'v4 lid missing'); shell=require(bpy.data.objects.get('Reference_led_fixed_shell'),'v4 shell missing')
    bed=require(bpy.data.objects.get('Sleeping_surface'),'v4 mattress missing'); display=require(bpy.data.objects.get('Foot_info_display_surface'),'v4 display missing')
    frame=require(bpy.data.objects.get('pod_v4_window_frame'),'v4 window frame missing'); seal=require(bpy.data.objects.get('pod_v4_window_inner_seal'),'v4 window seal missing')
    backing=require(bpy.data.objects.get('pod_v4_lid_inner_backing'),'v4 lid backing missing'); basin=require(bpy.data.objects.get('pod_v4_basin_seal_lip'),'v4 basin seal missing')
    display_housing=require(bpy.data.objects.get('pod_v4_display_housing'),'v4 display housing missing')
    root=empty('CryopodRoot')
    motion=require(bpy.data.objects.get('Whole_lid_motion'),'v4 motion parent missing'); motion.name='LidMotion'; set_parent_keep_world(motion,root)
    # Split by actual material role, with its actual color UV promoted to UV0.
    # A marker empty is not a glass mesh, and a multi-color-UV shell cannot
    # reserve TEXCOORD_1 for a lightmap until its material UVs are normalized.
    uv_names={'lid':'UV_TRIAL_V3_LID_XY','shell_side':'UV_TRIAL_V3_SHELL_SIDE','shell_end':'UV_TRIAL_V3_SHELL_END','interior':'UV_TRIAL_V3_INTERIOR_XY','mattress':'UV_TRIAL_V3_MATTRESS_XY','glass':'UV_TRIAL_V3_GLASS_XY','display':'UV_SCREEN_0_1','section':'UV_POD_V4_SECTION'}
    specs=[(lid,motion,{'lid':'PodLid','interior':'PodLidInterior','glass':'PodGlass'}),
           (shell,root,{'shell_side':'PodShell','shell_end':'PodShellEnd','interior':'PodInterior','section':'PodShellSection'}),
           (bed,root,{'mattress':'PodMattress'}),(display,root,{'display':'PodDisplay'}),
           (frame,motion,{'section':'PodWindowFrame'}),(seal,motion,{'section':'PodWindowSeal'}),
           (backing,motion,{'section':'PodLidBacking'}),(basin,root,{'section':'PodBasinSeal'}),
           (display_housing,root,{'section':'PodDisplayHousing'})]
    pieces=[]
    for source,parent,roles in specs:
        for key,name in roles.items():
            mesh=source.data.copy();wanted={p.index for p in mesh.polygons if mesh.materials[p.material_index]==mats[key]}
            require(wanted,f'Missing actual {key} faces in {source.name}')
            bm=bmesh.new();bm.from_mesh(mesh);bm.faces.ensure_lookup_table()
            bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.index not in wanted],context='FACES')
            loose=[v for v in bm.verts if not v.link_faces]
            if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
            bm.to_mesh(mesh);bm.free();mesh.update()
            actual=mesh.uv_layers.get(uv_names[key]);require(actual,f'Actual color UV missing: {key}')
            values=[d.uv.copy() for d in actual.data]
            while mesh.uv_layers:mesh.uv_layers.remove(mesh.uv_layers[0])
            uv=mesh.uv_layers.new(name='UV_GODOT_0')
            for i,value in enumerate(values):uv.data[i].uv=value
            uv.active_render=True;mesh.materials.clear();mesh.materials.append(mats[key])
            for p in mesh.polygons:p.material_index=0
            # Every color image explicitly uses normalized color UV0, including
            # Cycles bake context where LightmapUV is the active receiver UV.
            nodes=mats[key].node_tree.nodes;links=mats[key].node_tree.links
            for node in nodes:
                if node.type=='UVMAP':node.uv_map='UV_GODOT_0'
            obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
            obj.matrix_world=source.matrix_world.copy();set_parent_keep_world(obj,parent);pieces.append(obj)
        bpy.data.objects.remove(source,do_unlink=True)
    tubes=[]
    for name,(center,size,matname) in TUBE_SPECS.items(): tubes.append(make_box(name,center,size,mats[matname.removeprefix('POD_V8_')],root))
    # A single, explicit mapping used by the Godot worker and asset checker.
    return root,motion,pieces+tubes

def set_lid_action(motion):
    motion.animation_data_clear(); motion.rotation_mode='XYZ'
    # Blender creates the compatible layered Action/slot on first insertion.
    values={1:(Vector((0,0,.55)),0.0),20:(LID_LIFT,0.0),60:(LID_END,.7853981853)}
    for frame,(location,ry) in values.items():
        motion.location=location; motion.rotation_euler=(0,ry,0)
        motion.keyframe_insert(data_path='location',frame=frame); motion.keyframe_insert(data_path='rotation_euler',index=1,frame=frame)
    action=motion.animation_data.action; require(action,'Lid action was not created'); action.name='LidOpen'
    # The path is deliberately piecewise linear: whole lid clears vertically
    # first, then translates/rotates to the unchanged approved terminal pose.
    curves=[]
    if hasattr(action,'fcurves'): curves=action.fcurves
    else:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags: curves.extend(bag.fcurves)
    for curve in curves:
        for point in curve.keyframe_points: point.interpolation='LINEAR'
    return {'name':action.name,'fps':30,'frames':{'closed':1,'lift_clear':20,'open':60},'seconds':{'closed':0,'lift_clear':19/30,'open':59/30},'lift_candidates_m':[.08,.12,.16,.20],'selected_lift_m':.12,'locations':{'closed':[0,0,.55],'lift_clear':list(LID_LIFT),'open':list(LID_END)},'rotation_y_radians':{'closed':0,'lift_clear':0,'open':.7853981853}}

def make_shared_lightmap(objects):
    """One Smart Project atlas is copied back loop-for-loop to separate meshes.

    It keeps every runtime mesh separate while guaranteeing a common non-overlap
    coordinate space.  Color UV0 is never edited and remains first.
    """
    meshes=[o for o in objects if o.type=='MESH']
    # The approved v4 shell carries three zero-area construction faces.  They
    # have no visible surface but cannot receive a valid lightmap chart; remove
    # only those mathematically degenerate faces before building UV2.
    for obj in meshes:
        bm=bmesh.new(); bm.from_mesh(obj.data)
        dead=[face for face in bm.faces if face.calc_area() < 1e-12]
        if dead: bmesh.ops.delete(bm,geom=dead,context='FACES_ONLY')
        # Export/irradiance consumers triangulate anyway.  Do it explicitly so
        # an n-gon fan cannot manufacture collinear zero-area UV audit tris.
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
        bm.to_mesh(obj.data); bm.free(); obj.data.update()
    combined_verts=[]; combined_faces=[]; mapping=[]; vertex_base=0
    for obj in meshes:
        mesh=obj.data; append_uv0(mesh)
        if mesh.uv_layers.get('LightmapUV'): mesh.uv_layers.remove(mesh.uv_layers['LightmapUV'])
        for v in mesh.vertices: combined_verts.append(obj.matrix_world @ v.co)
        offset=len(mapping)
        for poly in mesh.polygons:
            combined_faces.append(tuple(vertex_base+i for i in poly.vertices))
            mapping.extend((obj,li) for li in poly.loop_indices)
        vertex_base+=len(mesh.vertices)
    tempmesh=bpy.data.meshes.new('V8_SHARED_LIGHTMAP_TEMP'); tempmesh.from_pydata(combined_verts,[],combined_faces); tempmesh.update()
    temp=bpy.data.objects.new('V8_SHARED_LIGHTMAP_TEMP',tempmesh); bpy.context.collection.objects.link(temp)
    uv=tempmesh.uv_layers.new(name='LightmapUV'); tempmesh.uv_layers.active=uv
    bpy.context.view_layer.objects.active=temp; temp.select_set(True); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15192, margin_method='SCALED', island_margin=.008, area_weight=.0, correct_aspect=True, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    require(len(mapping)==len(tempmesh.loops),'loop ordering changed while making shared atlas')
    by_mesh={}
    for index,(obj,loop_index) in enumerate(mapping): by_mesh.setdefault(obj,[]).append((loop_index,tempmesh.uv_layers['LightmapUV'].data[index].uv.copy()))
    for obj,entries in by_mesh.items():
        dst=obj.data.uv_layers.new(name='LightmapUV')
        for loop_index,coord in entries: dst.data[loop_index].uv=coord
        # Explicitly preserve v4 color layer as exported TEXCOORD_0.
        obj.data.uv_layers.active_index=0
        obj.data.uv_layers[0].active_render=True
    bpy.data.objects.remove(temp,do_unlink=True)

def uv_basic(objects):
    result={'triangles':0,'degenerate_triangles':0,'out_of_atlas_vertices':0,'bounds':[1,1,0,0], 'by_mesh':{}, 'shared_atlas':'single temporary Smart UV Project, loop-mapped back to separated meshes'}
    for obj in objects:
        if obj.type!='MESH': continue
        uv=obj.data.uv_layers['LightmapUV']; local_deg=0
        for poly in obj.data.polygons:
            ids=poly.loop_indices
            for i in range(1,len(ids)-1):
                a,b,c=[uv.data[ids[x]].uv for x in (0,i,i+1)]; area=abs((b.x-a.x)*(c.y-a.y)-(c.x-a.x)*(b.y-a.y))*.5
                result['triangles']+=1; result['degenerate_triangles']+=area<1e-12; local_deg+=area<1e-12
            for li in ids:
                p=uv.data[li].uv; result['bounds']=[min(result['bounds'][0],p.x),min(result['bounds'][1],p.y),max(result['bounds'][2],p.x),max(result['bounds'][3],p.y)]
                result['out_of_atlas_vertices']+=p.x<-.000001 or p.y<-.000001 or p.x>1.000001 or p.y>1.000001
        result['by_mesh'][obj.name]=local_deg
    return result

def selected_descendants(root):
    return [root]+list(root.children_recursive)

def export(glb, root, animations):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in selected_descendants(root): obj.select_set(True)
    bpy.context.view_layer.objects.active=root
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_image_format='AUTO',export_apply=False,export_animations=animations,export_current_frame=not animations,export_force_sampling=True,export_yup=True)
    return glb_json(glb)

def bounds_at_frame(objects, frame):
    bpy.context.scene.frame_set(frame); bpy.context.view_layer.update(); coords=[]
    for obj in objects:
        if obj.type=='MESH': coords.extend(obj.matrix_world @ vertex.co for vertex in obj.data.vertices)
    return {'min':[min(v[i] for v in coords) for i in range(3)],'max':[max(v[i] for v in coords) for i in range(3)]}

def bvh_collision_report(lid, fixed, frames=(1,8,14,20,30,40,50,60)):
    deps=bpy.context.evaluated_depsgraph_get(); out=[]
    def world_bvh(obj):
        evaluated=obj.evaluated_get(deps); mesh=evaluated.to_mesh()
        try:
            verts=[evaluated.matrix_world @ v.co for v in mesh.vertices]
            faces=[tuple(poly.vertices) for poly in mesh.polygons if len(poly.vertices)>=3]
            return BVHTree.FromPolygons(verts,faces,all_triangles=False)
        finally:
            evaluated.to_mesh_clear()
    for frame in frames:
        bpy.context.scene.frame_set(frame); bpy.context.view_layer.update()
        moving=world_bvh(lid)
        hits={}
        for obj in fixed:
            other=world_bvh(obj); pairs=moving.overlap(other)
            if pairs: hits[obj.name]=len(pairs)
        out.append({'frame':frame,'pairs':hits})
    return out

def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    # Remove only review cameras/lights/floor; no v4 asset geometry is rebuilt.
    for obj in list(bpy.data.objects):
        if obj.type in {'CAMERA','LIGHT'} or obj.name=='Review_floor': bpy.data.objects.remove(obj,do_unlink=True)
    mats=clone_renamed_materials(); root,motion,meshes=setup_nodes(mats)
    bpy.context.scene.render.fps=30; bpy.context.scene.frame_start=1; bpy.context.scene.frame_end=60
    animation=set_lid_action(motion)
    make_shared_lightmap(meshes)
    uv=uv_basic(meshes); print('UV2_AUDIT',json.dumps(uv),flush=True); require(uv['degenerate_triangles']==0,'degenerate UV2 triangles'); require(uv['out_of_atlas_vertices']==0,'out-of-atlas UV2')
    precise=runpy.run_path(str(REPO/'scripts/dev/room1_uv2_audit.py'))['audit_uv2_layout'](meshes)
    require(precise['positive_area_overlap_count']==0,'shared UV2 atlas overlaps')
    uv['precise_overlap_audit']=precise
    lid=bpy.data.objects['PodLid']; fixed=[bpy.data.objects[n] for n in ('PodShell','PodMattress','PodTubeHousing_L','PodTubeHousing_R','PodTubeDiffuser_L','PodTubeDiffuser_R')]
    collision=bvh_collision_report(lid,fixed)
    # Static poses share the exact UV2 layout from this same source file.
    bpy.context.scene.frame_set(1); closed=export(OUT/'cryopod_standard_v8_closed.glb',root,False)
    bpy.context.scene.frame_set(60); opened=export(OUT/'cryopod_standard_v8_open.glb',root,False)
    bpy.context.scene.frame_set(1); animated=export(OUT/'cryopod_standard_v8.glb',root,True)
    bpy.ops.file.pack_all(); bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND),compress=True,check_existing=False)
    all_prims=[p for m in animated.get('meshes',[]) for p in m.get('primitives',[])]
    require(animated.get('animations'),'animated GLB did not contain LidOpen')
    require(all('TEXCOORD_0' in p.get('attributes',{}) and 'TEXCOORD_1' in p.get('attributes',{}) for p in all_prims),'UV0/UV2 missing from GLB primitive')
    contract={'version':'cryopod_standard_v8','root':'CryopodRoot','animation':animation,'nodes':{'fixed':['PodShell','PodShellEnd','PodShellSection','PodInterior','PodMattress','PodDisplay','PodDisplayHousing','PodBasinSeal','PodTubeHousing_L','PodTubeHousing_R','PodTubeDiffuser_L','PodTubeDiffuser_R'],'lid_motion_parent':'LidMotion','moving':['PodLid','PodLidInterior','PodGlass','PodWindowFrame','PodWindowSeal','PodLidBacking']},'materials':{key:'POD_V8_'+key for key in MATERIAL_KEYS},'coordinate_contract':{'godot_to_blender':'(X, -Z, Y)','diffusers_godot':'x=+/-0.447,y=0.31,z=0,size=(0.006,0.022,1.70)','housings_godot':'x=+/-0.458,y=0.31,z=0,size=(0.016,0.034,1.74)'},'uv_contract':'TEXCOORD_0=v4 source color UV; TEXCOORD_1=one shared LightmapUV atlas copied to separated runtime meshes; same source layout for closed/open/animated exports.'}
    report={'version':'cryopod_standard_v8','source_v4':str(SOURCE),'blend':str(OUT_BLEND),'outputs':{'animated':str(OUT/'cryopod_standard_v8.glb'),'closed':str(OUT/'cryopod_standard_v8_closed.glb'),'open':str(OUT/'cryopod_standard_v8_open.glb')},'animation':animation,'uv2':uv,'bounds':{'closed':bounds_at_frame(meshes,1),'open':bounds_at_frame(meshes,60)},'collision_bvh_lid_vs_fixed':collision,'glb':{'animation_names':[a.get('name') for a in animated.get('animations',[])],'primitive_count':len(all_prims),'materials':[m.get('name') for m in animated.get('materials',[])]},'note':'BVH reports initial closed fitted contacts separately from path samples; inspect nonzero values before declaring clearance.'}
    CONTRACT.write_text(json.dumps(contract,ensure_ascii=False,indent=2),encoding='utf8'); REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print('V8_BUILD_COMPLETE',json.dumps(report,ensure_ascii=False))

if __name__=='__main__': main()
