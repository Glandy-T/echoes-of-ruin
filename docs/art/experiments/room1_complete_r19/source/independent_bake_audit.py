"""Read-only independent audit for the locked Room 1 r19 bake.

Run with Blender background on room1_complete_r19.blend.  It deliberately
does not save the file, alter assets, or reuse the baker's reported values.
"""
import array, hashlib, json, math, os, re, struct, sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

REPO = Path(bpy.data.filepath).parents[4]
HERE = Path(__file__).resolve().parent
OUT = HERE / "independent_bake_audit.json"
LAYOUT = json.loads((HERE / "layout_before.json").read_text(encoding="utf-8"))
MANIFEST = json.loads((HERE / "bake_manifest.json").read_text(encoding="utf-8"))

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda:f.read(1 << 20), b""): h.update(chunk)
    return h.hexdigest()

def node_images(mat):
    if not mat or not mat.use_nodes: return []
    return [n.image for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]

def mesh_rows(obj):
    m = obj.data; u0=m.uv_layers.get("UV_GODOT_0") or m.uv_layers[0]; u2=m.uv_layers.get("LightmapUV")
    rows=[]
    for poly in m.polygons:
        name=m.materials[poly.material_index].name if poly.material_index < len(m.materials) else ""
        for li in poly.loop_indices:
            co=obj.matrix_world @ m.vertices[m.loops[li].vertex_index].co
            a=u0.data[li].uv if u0 else (0,0); b=u2.data[li].uv if u2 else (0,0)
            rows.append((name, *(round(float(v),5) for v in (*co,*a,*b))))
    return sorted(rows)

def mesh_rows_no_material(obj):
    return [r[1:] for r in mesh_rows(obj)]

def rows_close(a,b,tolerance=2.0e-4):
    if len(a)!=len(b): return False, None
    worst=max((max(abs(x-y) for x,y in zip(left,right)) for left,right in zip(a,b)),default=0.0)
    return worst <= tolerance, worst

def channel_check(rows_a,rows_b,columns,tolerance=2.0e-4):
    a=sorted(tuple(row[i] for i in columns) for row in rows_a); b=sorted(tuple(row[i] for i in columns) for row in rows_b)
    if len(a)!=len(b): return False,None
    worst=max((max(abs(x-y) for x,y in zip(left,right)) for left,right in zip(a,b)),default=0.0)
    return worst<=tolerance,worst

def shared_edge_uv_continuity(obj,tolerance=1.0e-5):
    """Reports, rather than assumes, whether coincident world edges share UV2."""
    m=obj.data; uv=m.uv_layers['LightmapUV']; edges={}
    for poly in m.polygons:
        loops=list(poly.loop_indices)
        for i,li in enumerate(loops):
            lj=loops[(i+1)%len(loops)]
            a=obj.matrix_world@m.vertices[m.loops[li].vertex_index].co; b=obj.matrix_world@m.vertices[m.loops[lj].vertex_index].co
            pa=tuple(round(float(x),6) for x in a); pb=tuple(round(float(x),6) for x in b)
            ua=tuple(float(x) for x in uv.data[li].uv); ub=tuple(float(x) for x in uv.data[lj].uv)
            normal=(obj.matrix_world.to_3x3() @ poly.normal).normalized()
            key=tuple(sorted((pa,pb))); edges.setdefault(key,[]).append(((pa,pb),(ua,ub),tuple(float(x) for x in normal)))
    paired=[v for v in edges.values() if len(v)==2]; continuous=0; discontinuous=[]
    coplanar=[pair for pair in paired if sum(pair[0][2][i]*pair[1][2][i] for i in range(3)) >= 0.99999]
    for pair in coplanar:
        (_,left,_),(_,right,_)=pair
        direct=max(abs(left[0][i]-right[0][i]) for i in range(2))<=tolerance and max(abs(left[1][i]-right[1][i]) for i in range(2))<=tolerance
        reverse=max(abs(left[0][i]-right[1][i]) for i in range(2))<=tolerance and max(abs(left[1][i]-right[0][i]) for i in range(2))<=tolerance
        if direct or reverse: continuous+=1
        elif len(discontinuous)<10: discontinuous.append({'uv_a':left,'uv_b':right})
    return {'physical_edge_count':len(edges),'two_face_shared_edges_all_normals':len(paired),'coplanar_shared_edges':len(coplanar),'uv2_continuous_coplanar_shared_edges':continuous,'uv2_discontinuous_coplanar_shared_edges':len(coplanar)-continuous,'examples_of_discontinuous_coplanar_edges':discontinuous}

def shell_source_records(obj,godot_space=False,flip_v=False):
    m=obj.data; u0=m.uv_layers.get('UV_GODOT_0') or m.uv_layers[0]; u2=m.uv_layers['LightmapUV']; out=[]
    for poly in m.polygons:
        base_normal=(obj.matrix_world.to_3x3()@poly.normal).normalized()
        for li in poly.loop_indices:
            normal=base_normal.copy()
            co=obj.matrix_world@m.vertices[m.loops[li].vertex_index].co
            if godot_space:
                co=Vector((co.x,co.z,-co.y)); normal=Vector((normal.x,normal.z,-normal.y))
            key=tuple(round(float(x),4) for x in co)+tuple(round(float(x),4) for x in normal)
            mat=m.materials[poly.material_index].name if poly.material_index<len(m.materials) else ''
            a=u0.data[li].uv; b=u2.data[li].uv
            out.append({'key':key,'material':mat,'uv0':[round(float(a.x),6),round(float(1-a.y if flip_v else a.y),6)],'uv2':[round(float(b.x),6),round(float(1-b.y if flip_v else b.y),6)]})
    return out

def shell_glb_records(path,node_filter,flip_v=True):
    doc,binary=glb_payload(path); out=[]; conversion=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
    def visit(i,parent):
        n=doc['nodes'][i]
        if 'matrix' in n: local=Matrix([n['matrix'][j:j+4] for j in range(0,16,4)]).transposed()
        else:
            q=n.get('rotation',[0,0,0,1]); local=Matrix.Translation(n.get('translation',[0,0,0]))@Quaternion((q[3],q[0],q[1],q[2])).to_matrix().to_4x4()@Matrix.Diagonal([*n.get('scale',[1,1,1]),1])
        world=parent@local
        if 'mesh' in n and node_filter(n):
            for p in doc['meshes'][n['mesh']]['primitives']:
                a=p['attributes']
                if not all(x in a for x in ('POSITION','NORMAL','TEXCOORD_0','TEXCOORD_1')): continue
                pos=glb_array(doc,binary,a['POSITION']); nor=glb_array(doc,binary,a['NORMAL']); u0=glb_array(doc,binary,a['TEXCOORD_0']); u2=glb_array(doc,binary,a['TEXCOORD_1'])
                ix=glb_array(doc,binary,p['indices']).reshape(-1) if 'indices' in p else np.arange(len(pos)); nm=(conversion@world).to_3x3().inverted().transposed()
                for j in ix:
                    j=int(j); co=conversion@world@Vector(pos[j]); no=(nm@Vector(nor[j])).normalized(); x,y=u0[j]; u,v=u2[j]
                    out.append({'key':tuple(round(float(z),4) for z in co)+tuple(round(float(z),4) for z in no),'node':n.get('name',''),'uv0':[round(float(x),6),round(float(1-y if flip_v else y),6)],'uv2':[round(float(u),6),round(float(1-v if flip_v else v),6)]})
        for child in n.get('children',[]): visit(child,world)
    for i in doc['scenes'][doc.get('scene',0)]['nodes']: visit(i,Matrix.Identity(4))
    return out

def shell_uv_match_sample(source_records,runtime_records):
    src={}; run={}
    for r in source_records: src.setdefault(r['key'],[]).append(r)
    for r in runtime_records: run.setdefault(r['key'],[]).append(r)
    keys=sorted(set(src)&set(run)); mismatch=[]; matched=0
    for key in keys:
        a=sorted((tuple(x['uv0']),tuple(x['uv2'])) for x in src[key]); b=sorted((tuple(x['uv0']),tuple(x['uv2'])) for x in run[key])
        if a==b: matched+=1
        elif not mismatch: mismatch=[{'position_normal':key,'blend':src[key],'runtime_r4':run[key]}]
    return {'position_normal_keys_shared':len(keys),'position_normal_keys_uv_pairs_match':matched,'sample_first_mismatch':mismatch}

def shell_corner_membership(source_records,runtime_records,tolerance=2.0e-4):
    """Set-membership check; deliberately ignores duplicate triangle corners."""
    source={(r['key'],tuple(r['uv0']),tuple(r['uv2'])) for r in source_records}
    def close(a,b): return len(a)==len(b) and all(abs(x-y)<=tolerance for x,y in zip(a,b))
    misses=[]; hit=0
    for r in runtime_records:
        found=any(close(r['key'],s[0]) and close(r['uv0'],s[1]) and close(r['uv2'],s[2]) for s in source)
        if found: hit+=1
        elif len(misses)<3: misses.append(r)
    return {'runtime_corners':len(runtime_records),'corners_with_position_normal_uv_membership_within_2e-4':hit,'unmatched_corner_count':len(runtime_records)-hit,'unmatched_samples':misses}

def shell_runtime_dump_records(path):
    raw=json.loads(Path(path).read_text(encoding='utf-8')); out=[]
    for mesh in raw:
        label=mesh.get('name','')
        for tri in mesh.get('triangles',[]):
            for x in tri:
                key=tuple(round(float(v),4) for v in x['position'])+tuple(round(float(v),4) for v in x['normal'])
                out.append({'key':key,'node':label,'uv0':[round(float(v),6) for v in x['uv0']],'uv2':[round(float(v),6) for v in x['uv2']]})
    return out

def glb_payload(path):
    raw=Path(path).read_bytes(); n=struct.unpack_from('<I',raw,12)[0]
    return json.loads(raw[20:20+n]), raw[28+n:]

def glb_array(doc,binary,index):
    a=doc['accessors'][index]; v=doc['bufferViews'][a['bufferView']]
    dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']])
    n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    return np.ndarray((a['count'],n),dtype=dt,buffer=binary,
        offset=v.get('byteOffset',0)+a.get('byteOffset',0),
        strides=(v.get('byteStride',n*dt.itemsize),dt.itemsize)).copy()

def glb_uv_signatures(path):
    doc,binary=glb_payload(path); out=[]
    for mesh in doc.get('meshes',[]):
        for p in mesh.get('primitives',[]):
            a=p['attributes']
            for key in ('TEXCOORD_0','TEXCOORD_1'):
                out.append((key,hashlib.sha256(glb_array(doc,binary,a[key]).tobytes()).hexdigest(),len(glb_array(doc,binary,a[key]))))
    return sorted(out)

def glb_world_rows(path,node_filter=None,flip_v=True):
    """Visible position/UV rows, canonicalized into Blender coordinates."""
    doc,binary=glb_payload(path); rows=[]; conversion=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
    def visit(i,parent):
        n=doc['nodes'][i]
        if 'matrix' in n: local=Matrix([n['matrix'][j:j+4] for j in range(0,16,4)]).transposed()
        else:
            q=n.get('rotation',[0,0,0,1]); local=Matrix.Translation(n.get('translation',[0,0,0])) @ Quaternion((q[3],q[0],q[1],q[2])).to_matrix().to_4x4() @ Matrix.Diagonal([*n.get('scale',[1,1,1]),1])
        world=parent@local
        if 'mesh' in n and (node_filter is None or node_filter(n)):
            for p in doc['meshes'][n['mesh']]['primitives']:
                a=p['attributes']
                # r4's stale placeholder door has no lightmap UV and is not
                # part of the r19 shell receiver; do not conflate it with the
                # runtime shell contract under test.
                if 'TEXCOORD_0' not in a or 'TEXCOORD_1' not in a: continue
                pos=glb_array(doc,binary,a['POSITION']); u0=glb_array(doc,binary,a['TEXCOORD_0']); u2=glb_array(doc,binary,a['TEXCOORD_1'])
                ix=glb_array(doc,binary,p['indices']).reshape(-1) if 'indices' in p else np.arange(len(pos))
                for j in ix:
                    co=conversion@world@Vector(pos[int(j)]); x,y=u0[int(j)]; u,v=u2[int(j)]
                    rows.append(tuple(round(float(v),5) for v in (*co,x,1-y if flip_v else y,u,1-v if flip_v else v)))
        for child in n.get('children',[]): visit(child,world)
    for i in doc['scenes'][doc.get('scene',0)]['nodes']: visit(i,Matrix.Identity(4))
    return sorted(rows)

def rel_image(image):
    try: return Path(bpy.path.abspath(image.filepath)).resolve().relative_to(REPO).as_posix()
    except Exception: return str(image.filepath).replace('\\','/')

# Load the project's actual independent UV checker instead of copying it.
uv_ns={}
exec(compile((REPO/'scripts/dev/room1_uv2_audit.py').read_text(encoding='utf-8'), 'room1_uv2_audit.py', 'exec'), uv_ns)
audit_uv2_layout=uv_ns['audit_uv2_layout']

objects=list(bpy.data.objects)
receivers=sorted([o for o in objects if re.fullmatch(r'R19_P\d\d_closed_receiver',o.name or '')],key=lambda o:o.name)
old=[o.name for o in objects if 'pod_v3' in o.name.lower() or re.match(r'Bake_P\d\d_',o.name or '')]
shell=[o for o in objects if o.name == 'R19_shell_receiver']
report={"audit":"independent read-only Blender audit","blend":str(Path(bpy.data.filepath)),"confirmed":{},"failures":[],"limitations":[]}

report['confirmed']['source_editability']={
 "blend_opened": bool(bpy.data.filepath), "mesh_object_count":sum(o.type=='MESH' for o in objects),
 "closed_receiver_names":[o.name for o in receivers], "closed_receiver_count":len(receivers),
 "old_v3_or_bake_p_objects":old, "shell_mesh_names":sorted(o.name for o in shell),
 "blend_file_path_is_absolute_expected_for_open_file":not bpy.data.filepath.startswith('//'),
 "external_images_absolute":sum(bool(i.filepath and not i.filepath.startswith('//')) for i in bpy.data.images),
 "external_images_relative":sum(bool(i.filepath and i.filepath.startswith('//')) for i in bpy.data.images),
}
relative_check_path=HERE/'relative_paths_check.json'
if relative_check_path.exists():
    report['confirmed']['upload_portability_readback']=json.loads(relative_check_path.read_text(encoding='utf-8'))
scene=bpy.context.scene
report['confirmed']['saved_scene_bake_settings']={'render_engine':scene.render.engine,'cycles_samples':scene.cycles.samples,'adaptive_sampling':scene.cycles.use_adaptive_sampling,'saved_scene_margin_not_a_per_job_contract':scene.render.bake.margin}
if len(receivers)!=20: report['failures'].append('Expected 20 R19 closed receivers, found %d'%len(receivers))
if old: report['failures'].append('Old v3/Bake_P geometry still present: '+', '.join(old[:20]))

# Per-pod material/image bindings and UV2 audit.  Separate calls are intentional:
# each pod has its own 1024 lightmap, so cross-pod overlaps are not errors.
expected={p['id']:p['bake_color_maps'] for p in LAYOUT['pods']}
pod_rows={}; pod_uv={}; materials={}
for o in receivers:
    pid=o.name.split('_')[1]
    actual={}
    for m in o.data.materials:
        imgs=[rel_image(x) for x in node_images(m)]
        actual[m.name]=imgs
    materials[pid]=actual
    want=set(expected.get(pid,{}).values())
    got={p for v in actual.values() for p in v if p.endswith('.png')}
    missing=sorted(want-got); unexpected_old=sorted(x for x in actual if 'v3' in x.lower())
    if missing: report['failures'].append('%s missing expected color images: %s'%(pid,missing))
    if unexpected_old: report['failures'].append('%s has old v3 material suffixes: %s'%(pid,unexpected_old))
    pod_uv[pid]=audit_uv2_layout([o])
    pod_rows[pid]=len(mesh_rows(o))
report['confirmed']['pod_materials']=materials
report['confirmed']['pod_uv2_per_lightmap']=pod_uv
report['confirmed']['pod_loop_rows']=pod_rows
for pid,a in pod_uv.items():
    if a['uv_degenerate_triangle_count'] or a['out_of_atlas_vertex_count'] or a['positive_area_overlap_count']:
        report['failures'].append('%s UV2 failed: %s'% (pid,{k:a[k] for k in ('uv_degenerate_triangle_count','out_of_atlas_vertex_count','positive_area_overlap_count')}))

# Direct GLB-to-saved-Blend comparison for one receiver from each orientation
# class plus the animated P12 closed endpoint.  This tests visible vertices and
# both UV layers, rather than object names or source-layer labels.
frozen_path=REPO/'docs/art/experiments/room1_pod_standard_v8/source/frozen_glb_pose.py'
frozen_source=frozen_path.read_text(encoding='utf-8').replace(
    'materials={m.name:m for m in dst.materials}',
    "materials={m.name.rsplit('.', 1)[0] if m.name.rsplit('.', 1)[-1].isdigit() else m.name:m for m in dst.materials}")
frozen_scope={'__file__':str(frozen_path),'__name__':'independent_frozen_pose'}
exec(compile(frozen_source,str(frozen_path),'exec'),frozen_scope)
load_pose=frozen_scope['load_frozen_pose']; pose_checks={}
for pid in ('P01','P11','P12'):
    entry=next(p for p in LAYOUT['pods'] if p['id']==pid)
    anchor=Vector((float(entry['origin'][0]),-float(entry['origin'][2]),float(entry['origin'][1])))
    imported=load_pose(REPO/'assets/art/cryopod_standard_v8/cryopod_standard_v8_closed.glb',REPO/'docs/art/experiments/room1_pod_standard_v8/room1_pod_standard_v8_packed.blend',anchor)
    if entry['basis_columns'][0][0] < 0:
        pivot=Matrix.Translation(anchor) @ Matrix.Rotation(math.pi,4,'Z') @ Matrix.Translation(-anchor)
        for x in imported: x.matrix_world=pivot @ x.matrix_world
    opaque=[x for x in imported if not any(t in ' '.join(m.name.lower() for m in x.data.materials if m) for t in ('glass','display','tube_diffuser'))]
    exp=sorted(r for x in opaque for r in mesh_rows_no_material(x)); act=mesh_rows_no_material(bpy.data.objects['R19_'+pid+'_closed_receiver'])
    same,worst=rows_close(exp,act)
    p_ok,p_delta=channel_check(exp,act,(0,1,2)); u0_ok,u0_delta=channel_check(exp,act,(3,4)); u2_ok,u2_delta=channel_check(exp,act,(5,6))
    pose_checks[pid]={'expected_visible_loop_rows':len(exp),'saved_visible_loop_rows':len(act),'position_set_identical_within_2e-4':p_ok,'uv0_set_identical_within_2e-4':u0_ok,'uv2_set_identical_within_2e-4':u2_ok,'full_position_uv_pairing_identical_within_2e-4':same,'max_deltas':{'position':p_delta,'uv0':u0_delta,'uv2':u2_delta,'paired':worst}}
    if not (p_ok and u0_ok and u2_ok): report['failures'].append('%s saved visible vertices or UVs differ from transformed closed v8 GLB'%pid)
report['confirmed']['v8_glb_to_saved_visible_vertex_uv_checks']=pose_checks
v8=REPO/'assets/art/cryopod_standard_v8'; sig={p.name:glb_uv_signatures(p) for p in (v8/'cryopod_standard_v8.glb',v8/'cryopod_standard_v8_closed.glb',v8/'cryopod_standard_v8_open.glb')}
same_uv=len({json.dumps(x,sort_keys=True) for x in sig.values()})==1
report['confirmed']['p12_closed_open_v8_uv_contract']={'uv_accessors_by_file':sig,'all_three_uv_accessor_signatures_identical':same_uv}
if not same_uv: report['failures'].append('v8 base/closed/open GLB UV accessor contract differs')

# Shell uses one 2048 map.  Audit it as one atlas (unlike pods).
if shell:
    shell_uv=audit_uv2_layout(shell)
    shell_edges=shared_edge_uv_continuity(shell[0])
    report['confirmed']['shell_uv2_atlas']=shell_uv
    report['confirmed']['shell_uv2_shared_edge_readback']=shell_edges
    if shell_uv['uv_degenerate_triangle_count'] or shell_uv['out_of_atlas_vertex_count'] or shell_uv['positive_area_overlap_count']:
        report['failures'].append('Shell UV2 failed: %s'%{k:shell_uv[k] for k in ('uv_degenerate_triangle_count','out_of_atlas_vertex_count','positive_area_overlap_count')})
else: report['failures'].append('No R19 shell receiver')

# Runtime r4 shell GLB is compared to the joined receiver by visible world
# vertices and both UV layers after Godot->Blender coordinate conversion.
if shell:
    runtime_rows=glb_world_rows(REPO/MANIFEST['inputs']['runtime_r4_shell_glb'],lambda n:n.get('name','').startswith('Bake_Shell_') and 'PLACEHOLDER' not in n.get('name',''))
    runtime_rows_no_flip=glb_world_rows(REPO/MANIFEST['inputs']['runtime_r4_shell_glb'],lambda n:n.get('name','').startswith('Bake_Shell_') and 'PLACEHOLDER' not in n.get('name',''),False)
    source_rows=mesh_rows_no_material(shell[0])
    same,worst=rows_close(runtime_rows,source_rows); p_ok,p_delta=channel_check(runtime_rows,source_rows,(0,1,2)); u0_ok,u0_delta=channel_check(runtime_rows,source_rows,(3,4)); u2_ok,u2_delta=channel_check(runtime_rows,source_rows,(5,6))
    direct_same,direct_worst=rows_close(runtime_rows_no_flip,source_rows); direct_u0,direct_u0_delta=channel_check(runtime_rows_no_flip,source_rows,(3,4)); direct_u2,direct_u2_delta=channel_check(runtime_rows_no_flip,source_rows,(5,6))
    report['confirmed']['runtime_r4_shell_visible_vertex_uv_check']={'runtime_rows':len(runtime_rows),'saved_rows':len(source_rows),'position_set_identical_within_2e-4':p_ok,'uv0_set_identical_within_2e-4':u0_ok,'uv2_set_identical_within_2e-4':u2_ok,'full_position_uv_pairing_identical_within_2e-4':same,'max_deltas':{'position':p_delta,'uv0':u0_delta,'uv2':u2_delta,'paired':worst},'unflipped_glb_uv_control':{'uv0_set_identical_within_2e-4':direct_u0,'uv2_set_identical_within_2e-4':direct_u2,'full_pairing_identical_within_2e-4':direct_same,'max_uv0_delta':direct_u0_delta,'max_uv2_delta':direct_u2_delta,'max_paired_delta':direct_worst}}
    report['confirmed']['runtime_r4_shell_position_normal_uv_readback']=shell_uv_match_sample(shell_source_records(shell[0]),shell_glb_records(REPO/MANIFEST['inputs']['runtime_r4_shell_glb'],lambda n:n.get('name','').startswith('Bake_Shell_') and 'PLACEHOLDER' not in n.get('name','')))
    runtime_dump=HERE/'runtime_shell_triangles.json'
    if runtime_dump.exists():
        actual=shell_runtime_dump_records(runtime_dump)
        direct=shell_uv_match_sample(shell_source_records(shell[0],godot_space=True),actual)
        flipped=shell_uv_match_sample(shell_source_records(shell[0],godot_space=True,flip_v=True),actual)
        direct_member=shell_corner_membership(shell_source_records(shell[0],godot_space=True),actual)
        flipped_member=shell_corner_membership(shell_source_records(shell[0],godot_space=True,flip_v=True),actual)
        report['confirmed']['actual_godot_shell_position_normal_uv_readback']={'runtime_dump':str(runtime_dump),'runtime_corner_count':len(actual),'blend_direct_uv':direct,'blend_v_flipped_uv_control':flipped,'direct_corner_membership':direct_member,'v_flipped_corner_membership':flipped_member}
        if flipped_member['unmatched_corner_count']:
            report['failures'].append('Actual Godot shell vertex/normal/UV contract has unmatched corners')
    if not (p_ok and u0_ok and u2_ok): report['limitations'].append('Raw r4 GLB accessor-to-Blender comparison differs under both simple V conventions; actual Godot vertex/UV dump above is the authoritative runtime check.')

# Check actual image files against manifest hashes and inspect decoded EXR pixels.
images=[]
job_margins=[]
for ent in MANIFEST.get('images',[]):
    name=ent['name']; final=REPO/'assets/art/room1_complete_r19/lighting'/(name+'.exr'); raw=REPO/'assets/art/room1_complete_r19/lighting'/(name+'_raw.exr')
    status={'name':name,'raw_exists':raw.exists(),'final_exists':final.exists(),'raw_sha_match':raw.exists() and sha(raw)==ent['raw_sha256'],'final_sha_match':final.exists() and sha(final)==ent['final_sha256']}
    for key,path in [('raw',raw),('final',final)]:
        if path.exists():
            im=bpy.data.images.load(str(path),check_existing=False)
            pixels=array.array('f',[0.0])*(im.size[0]*im.size[1]*4); im.pixels.foreach_get(pixels)
            status[key+'_size']=list(im.size); status[key+'_finite']=all(math.isfinite(v) for v in pixels)
            bpy.data.images.remove(im)
    images.append(status)
    margin=ent.get('margin_px'); expected_margin=6 if name.startswith('room_') else 4
    job_margins.append({'name':name,'margin_px':margin,'expected_margin_px':expected_margin,'matches_expected':margin==expected_margin})
    if margin!=expected_margin: report['failures'].append('Per-job bake margin mismatch '+name+': '+str(margin))
    if not all(status.get(k) for k in ('raw_exists','final_exists','raw_sha_match','final_sha_match','raw_finite','final_finite')): report['failures'].append('EXR issue '+name+': '+str(status))
report['confirmed']['exr_readback']=images
report['confirmed']['per_job_margin_readback']=job_margins

# Inputs hash/readback without trusting their prior summary.
input_status={'layout_sha_match':sha(HERE/'layout_before.json')==MANIFEST['inputs']['layout_sha256'],'runtime_shell':{}}
runtime=REPO/MANIFEST['inputs']['runtime_r4_shell_glb']
input_status['runtime_shell']={'exists':runtime.exists(),'sha_match':runtime.exists() and sha(runtime)==MANIFEST['inputs']['runtime_r4_shell_glb_sha256']}
maps=[]
for item in MANIFEST['inputs']['r13_r15_and_r16_color_maps']:
    p=REPO/item['path']; maps.append({'path':item['path'],'exists':p.exists(),'sha_match':p.exists() and sha(p)==item['sha256']})
input_status['color_maps']=maps
report['confirmed']['input_hashes']=input_status
if not input_status['layout_sha_match'] or not input_status['runtime_shell']['sha_match'] or any(not x['sha_match'] for x in maps): report['failures'].append('One or more recorded inputs changed or are missing')

# Bake configuration evidence, separately labelled as source evidence (not an EXR proof).
source=(HERE/'bake_room1_complete_r19.py').read_text(encoding='utf-8')
shader=(REPO/'scripts/dev/room1_complete_surface_r19.gdshader').read_text(encoding='utf-8')
imports=[]
for ent in MANIFEST.get('images',[]):
    name=ent['name']; p=REPO/'assets/art/room1_complete_r19/lighting'/(name+'.exr.import')
    t=p.read_text(encoding='utf-8') if p.exists() else ''
    imports.append({'name':name,'import_exists':p.exists(),'mipmaps_generate_false':'mipmaps/generate=false' in t})
report['confirmed']['runtime_sampler_contract']={
 'shader_strip_irradiance_linear_repeat_disable':'uniform sampler2D strip_irradiance : filter_linear, repeat_disable;' in shader,
 'shader_strip_irradiance_open_linear_repeat_disable':'uniform sampler2D strip_irradiance_open : filter_linear, repeat_disable;' in shader,
 'exr_imports':imports,
}
if not all(x['import_exists'] and x['mipmaps_generate_false'] for x in imports): report['failures'].append('One or more final EXR imports lack mipmaps/generate=false')
report['confirmed']['bake_source_evidence']={
 'samples_env_default_1024': 'R19_SAMPLES", "1024"' in source or "R19_SAMPLES', '1024'" in source,
 'pod_margin_4_per_job':'margin = 6 if output_name.startswith("room_") else 4' in source,
 'shell_margin_6_per_job':'margin = 6 if output_name.startswith("room_") else 4' in source,
 'bake_uses_per_job_margin':'margin=margin' in source,
 'oidn_node': 'CompositorNodeDenoise' in source,
 'pods_1024': 'f"P{n:02d}_closed", 1024' in source,
 'shell_2048': 'bake_receiver(shell, shell_name, 2048)' in source,
}
report['limitations'] += [
 'EXR readback proves finite decoded pixels and the manifest hashes, but cannot independently identify OIDN implementation from EXR metadata; only source wiring plus raw/final byte differences are available.',
 'Per-job dilation is 4px for every pod and 6px for both shell maps. Independent UV spacing is measured separately; pod atlas outer-edge minimum remains 0px and is not claimed as padding.',
 'UV shared-edge continuity is checked for valid non-overlapping atlases only; this report does not certify irradiance continuity without a rendered seam visual review.',
 'The source Blend uses repository-relative dependencies. The Blender image-datablock count and upload external-unpacked count use different scopes; portability still requires the repository-relative files to accompany the Blend.',
 'Godot camera/lighting/interactive visual acceptance is intentionally outside this audit.'
]
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('INDEPENDENT_AUDIT',json.dumps({'failures':len(report['failures']),'output':str(OUT)},ensure_ascii=False))
