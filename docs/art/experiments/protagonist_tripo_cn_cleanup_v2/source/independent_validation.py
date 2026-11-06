"""Read-only independent geometry and presentation-boundary validation for v2."""
from pathlib import Path
import hashlib, json, struct
from mathutils import Vector
import bpy

EXP=Path(__file__).resolve().parent.parent
V1=EXP.parent/'protagonist_tripo_cn_cleanup_v1'
RAW=EXP.parent/'protagonist_tripo_cn_p20_v1'
BLEND=EXP/'model/protagonist_cn_cleanup_v2.blend'
GLB=EXP/'model/protagonist_cn_cleanup_v2.glb'
OUT=EXP/'source/independent_validation.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fail_list(d): return [k for k,v in d.items() if not v]

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
before_col=bpy.data.collections.get('BEFORE_V1')
after_col=bpy.data.collections.get('AFTER_V2')
for collection in (before_col,after_col):
    if collection:
        collection.hide_viewport=False
        for obj in collection.all_objects:
            obj.hide_viewport=False
            obj.hide_set(False)
bpy.context.view_layer.update()
before=[o for o in before_col.all_objects if o.type=='MESH'] if before_col else []
after=[o for o in after_col.all_objects if o.type=='MESH'] if after_col else []
src=before[0] if len(before)==1 else None
cand=after[0] if len(after)==1 else None
checks={'v1_blend_hash_unchanged':sha(V1/'model/protagonist_cn_cleanup_v1.blend')=='98a8a0bd8c9c7550177f31403e63dbfd5b535cf94c6f4132bc7ad94af136ac0e','raw_obj_hash_unchanged':sha(RAW/'model/protagonist_tripo_cn_p20_v1_raw.obj')=='f9717909d1df005269bfa695aa8a6863193ce4c27e583b3e52b9360d3ed58ff6','two_meshes_in_declared_collections':src is not None and cand is not None}
metrics={}
if src and cand:
    checks['mesh_counts']=len(src.data.polygons)==2596 and len(cand.data.polygons)==2582 and len(cand.data.vertices)==2515
    checks['same_transform']=all(abs(src.matrix_world[r][c]-cand.matrix_world[r][c])<1e-12 for r in range(4) for c in range(4))
    checks['no_uv_rig_modifier_shape_keys']=not cand.data.uv_layers and not cand.modifiers and cand.data.shape_keys is None and not [o for o in bpy.context.scene.objects if o.type=='ARMATURE']
    raw_s=src.data.attributes.get('raw_obj_face_index'); raw_c=cand.data.attributes.get('raw_obj_face_index')
    comp_s=src.data.attributes.get('raw_component_id'); comp_c=cand.data.attributes.get('raw_component_id')
    checks['raw_face_and_component_attributes_present']=all((raw_s,raw_c,comp_s,comp_c))
    smap={int(raw_s.data[p.index].value):p for p in src.data.polygons}
    cmap={int(raw_c.data[p.index].value):p for p in cand.data.polygons}
    hair_raw=[rid for rid,p in cmap.items() if int(comp_c.data[p.index].value)==6]
    xz_max=0.0; orient_min=1.0; area_ratio_min=1.0; tri_count=0; missing=[]; loop_mismatch=[]
    for rid in hair_raw:
        sp=smap.get(rid); cp=cmap[rid]
        if sp is None: missing.append(rid); continue
        if len(sp.vertices)!=len(cp.vertices): loop_mismatch.append(rid); continue
        old=[src.data.vertices[i].co.copy() for i in sp.vertices]
        new=[cand.data.vertices[i].co.copy() for i in cp.vertices]
        for a,b in zip(old,new): xz_max=max(xz_max,abs(a.x-b.x),abs(a.z-b.z))
        choices=[((0,1,2),)] if len(old)==3 else [((0,1,2),(0,2,3)),((0,1,3),(1,2,3))]
        for choice in choices:
            for i,j,k in choice:
                ao=(old[j]-old[i]).cross(old[k]-old[i]); an=(new[j]-new[i]).cross(new[k]-new[i])
                ao_len=ao.length; an_len=an.length
                if ao_len>1e-12:
                    orient_min=min(orient_min,ao.dot(an)/(ao_len*max(an_len,1e-30)))
                    area_ratio_min=min(area_ratio_min,an_len/ao_len)
                tri_count+=1
    checks['retained_hair_faces_correspond']=not missing and not loop_mismatch
    checks['retained_hair_xz_unchanged']=xz_max<=1e-7
    checks['retained_hair_no_fold_or_collapse']=orient_min>0 and area_ratio_min>=0.05
    metrics.update({'candidate_hair_faces':len(hair_raw),'missing_source_raw_faces':missing,'loop_mismatch_raw_faces':loop_mismatch,'retained_hair_xz_max_delta':xz_max,'min_oriented_triangle_dot':orient_min,'min_area_ratio':area_ratio_min,'triangles_checked_both_quad_diagonals':tri_count})
    expected={'Hair_Main':{6},'Robe':{2},'Head_Neck':{5},'Hands':{3,20},'Feet':{0,19}}
    actual_groups={g.name:set() for g in cand.vertex_groups}
    for group in cand.vertex_groups:
        for vi in range(len(cand.data.vertices)):
            try:
                if group.weight(vi)>0: actual_groups[group.name].add(vi)
            except RuntimeError: pass
    def component_vertices(ids): return {vi for p in cand.data.polygons if int(comp_c.data[p.index].value) in ids for vi in p.vertices}
    group_ok=set(actual_groups)==set(expected) and all(actual_groups[name]==component_vertices(ids) for name,ids in expected.items())
    checks['five_semantic_groups_exact_membership']=group_ok
    metrics['semantic_group_vertex_counts']={k:len(v) for k,v in actual_groups.items()}
else:
    for name in ('mesh_counts','same_transform','no_uv_rig_modifier_shape_keys','raw_face_and_component_attributes_present','retained_hair_faces_correspond','retained_hair_xz_unchanged','retained_hair_no_fold_or_collapse','five_semantic_groups_exact_membership'):
        checks[name]=False

data=GLB.read_bytes(); magic,ver,total=struct.unpack_from('<4sII',data); n,kind=struct.unpack_from('<II',data,12); gltf=json.loads(data[20:20+n])
checks['glb_candidate_only_no_uv_rig_camera']=magic==b'glTF' and ver==2 and total==len(data) and kind==0x4E4F534A and len(gltf.get('meshes',[]))==1 and not gltf.get('cameras') and not gltf.get('skins') and not gltf.get('animations') and all('TEXCOORD_0' not in p.get('attributes',{}) for m in gltf['meshes'] for p in m['primitives'])
visual={'actual_views_reviewed':['front','side','back','quarter','head_back'],'finding':'Left exposed loop is gone; lower hair edge is subtly softened. Right broad raised lock remains. No new black triangles, obvious cut, or body/robe shading change is visible in matched views.','remaining_limits':['Hair hem remains low-detail and somewhat jagged.','Hands and feet remain rough starting-mesh geometry.','Not UV-ready/rig-ready or user-art-approved; no game or runtime test.']}
result={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'metrics':metrics,'visual_review':visual,'artifact_sha256':{'blend':sha(BLEND),'glb':sha(GLB)}}
OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(result['status'],len(checks)-len(fail_list(checks)),'/',len(checks),fail_list(checks))
assert all(checks.values()),fail_list(checks)
