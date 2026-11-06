"""Read-only artifact checks, including untouched nonhair geometry and shading."""
from pathlib import Path
import hashlib,json,struct
from html.parser import HTMLParser
import bpy

EXP=Path(__file__).resolve().parent.parent
V1=EXP.parent/'protagonist_tripo_cn_cleanup_v1'
RAW=EXP.parent/'protagonist_tripo_cn_p20_v1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks={}
checks['v1_blend_unchanged']=sha(V1/'model/protagonist_cn_cleanup_v1.blend')=='98a8a0bd8c9c7550177f31403e63dbfd5b535cf94c6f4132bc7ad94af136ac0e'
checks['v1_glb_unchanged']=sha(V1/'model/protagonist_cn_cleanup_v1.glb')=='b826b7946cbcd43fc6dc555d0e16f80c63610b92ae9b4bbbba2e7dcd64086bda'
for name,record in read(RAW/'source/generation_record.json')['download']['files'].items():
    checks['raw_unchanged_'+name]=sha(RAW/'model'/name)==record['sha256']
blend=EXP/'model/protagonist_cn_cleanup_v2.blend'
bpy.ops.wm.open_mainfile(filepath=str(blend))
groups=[bpy.data.collections[n] for n in ('BEFORE_V1','AFTER_V2')]
for group in groups:
    group.hide_viewport=False;group.hide_render=False
    for obj in group.all_objects:obj.hide_set(False);obj.hide_render=False
bpy.context.view_layer.update()
srcs=[o for o in groups[0].all_objects if o.type=='MESH']
dsts=[o for o in groups[1].all_objects if o.type=='MESH']
checks['one_before_mesh']=len(srcs)==1
checks['candidate_mesh_present']=bool(dsts)
src=srcs[0]
def nonhair_faces(objects):
    result={}
    for obj in objects:
        mesh=obj.data
        components=mesh.attributes['raw_component_id'].data
        ids=mesh.attributes['raw_obj_face_index'].data
        for face in mesh.polygons:
            if components[face.index].value==6:continue
            fid=ids[face.index].value
            if fid in result:raise RuntimeError('Duplicate nonhair raw face ID')
            corners=[]
            for li in face.loop_indices:
                co=tuple(mesh.vertices[mesh.loops[li].vertex_index].co)
                corners.append((co,tuple(mesh.corner_normals[li].vector)))
            result[fid]=dict(corners)
    return result
a,b=nonhair_faces(srcs),nonhair_faces(dsts)
checks['all_nonhair_faces_kept']=set(a)==set(b)
checks['nonhair_coordinates_exact']=set(a)==set(b) and all(set(a[f])==set(b[f]) for f in a)
normal_delta=max((max(abs(a[f][co][i]-b[f][co][i]) for i in range(3)) for f in a if f in b for co in a[f] if co in b[f]),default=float('inf'))
checks['nonhair_corner_normals_preserved']=checks['nonhair_coordinates_exact'] and normal_delta<=0.002
checks['transforms_unchanged']=all(max(abs(src.matrix_world[r][c]-dst.matrix_world[r][c]) for r in range(4) for c in range(4))<=1e-7 for dst in dsts)
def hair_faces(objects):
    result={}
    for obj in objects:
        mesh=obj.data
        for face in mesh.polygons:
            if mesh.attributes['raw_component_id'].data[face.index].value==6:
                result[mesh.attributes['raw_obj_face_index'].data[face.index].value]=[tuple(mesh.vertices[v].co) for v in face.vertices]
    return result
ha,hb=hair_faces(srcs),hair_faces(dsts)
checks['only_existing_hair_faces_retained']=set(hb).issubset(ha)
checks['hair_fairing_only_local_y']=checks['only_existing_hair_faces_retained'] and all(sorted((v[0],v[2]) for v in hb[f])==sorted((v[0],v[2]) for v in ha[f]) for f in hb)
max_hair_delta=0.0;valid_hem=True
hairmin=min(v[1] for vs in ha.values() for v in vs)
for f,points in hb.items():
    for v in points:
        choices=[u for u in ha[f] if (u[0],u[2])==(v[0],v[2])]
        if not choices:valid_hem=False;continue
        old=min(choices,key=lambda u:abs(u[1]-v[1]));delta=abs(old[1]-v[1])
        max_hair_delta=max(max_hair_delta,delta)
        if delta>1e-7 and old[1]>hairmin+0.0200001:valid_hem=False
checks['hair_fairing_within_approved_hem']=valid_hem and max_hair_delta<=0.0030001
checks['hair_length_extent_preserved']=abs(min(v[1] for vs in hb.values() for v in vs)-hairmin)<1e-7 and abs(max(v[1] for vs in hb.values() for v in vs)-max(v[1] for vs in ha.values() for v in vs))<1e-7
checks['no_uv_or_rig_claim']=not any(o.type=='ARMATURE' for o in bpy.context.scene.objects) and all(not o.data.uv_layers and not o.modifiers for o in dsts)
glb=EXP/'model/protagonist_cn_cleanup_v2.glb'
data=glb.read_bytes();magic,version,total=struct.unpack_from('<4sII',data);length,kind=struct.unpack_from('<II',data,12)
doc=json.loads(data[20:20+length])
checks['valid_glb']=magic==b'glTF' and version==2 and total==len(data) and kind==0x4E4F534A
checks['only_candidate_glb_meshes']=len(doc.get('meshes',[]))==len(dsts)
checks['no_before_cameras_or_rig_in_glb']=not any(doc.get(k) for k in ('cameras','skins','animations'))
captures=read(EXP/'source/capture_record.json')
checks['ten_final_images']=len(captures)==10
for view in ('front','side','back','quarter','head_back'):
    before=next(x for x in captures if x['state']=='before' and x['view']==view)
    after=next(x for x in captures if x['state']=='after' and x['view']==view)
    checks[view+'_matched_camera']=before['camera_world_matrix']==after['camera_world_matrix']
    checks[view+'_intact_images']=all(sha(EXP/'evidence'/x['file'])==x['sha256'] and struct.unpack_from('>II',(EXP/'evidence'/x['file']).read_bytes(),16)==(1280,720) for x in (before,after))
class Links(HTMLParser):
    def __init__(self):super().__init__();self.paths=[]
    def handle_starttag(self,tag,attrs):
        for key,val in attrs:
            if key in ('href','src') and val and not val.startswith(('http','#')):self.paths.append(val)
links=Links();links.feed((EXP/'preview.html').read_text(encoding='utf-8'))
checks['preview_links_exist']=all((EXP/p).is_file() for p in links.paths)
report={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'untouched_nonhair_faces':len(a),'max_nonhair_normal_component_delta':normal_delta,'max_hair_vertex_height_delta':max_hair_delta,'candidate_counts':[{'object':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons)} for o in dsts],'artifact_sha256':{'blend':sha(blend),'glb':sha(glb)},'boundary':'File/geometry checks only. User visual approval and UV/rig/deformation/game validation are separate.'}
(EXP/'source/delivery_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(report['status'],sum(checks.values()),'/',len(checks))
assert all(checks.values()),[k for k,v in checks.items() if not v]
