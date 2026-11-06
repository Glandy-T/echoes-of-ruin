"""Delivery integrity checks; these do not substitute for visual/user review."""
from pathlib import Path
import hashlib, json, struct
from html.parser import HTMLParser
from PIL import Image

EXP=Path(__file__).resolve().parent.parent
RAW=EXP.parent/'protagonist_tripo_cn_p20_v1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks={}
record=read(RAW/'source/generation_record.json')
for name,data in record['download']['files'].items():
    path=RAW/'model'/name
    checks['raw_unchanged_'+name]=sha(path)==data['sha256'] and path.stat().st_size==data['bytes']
build=read(EXP/'source/build_report.json')
recipe=read(EXP/'source/repair_recipe.json')
checks['source_hash_verified']=build['raw_sha_matches_intent']
checks['recipe_head_ids_match']=set(build['recipe']['delete_head_component_ids'])==set(recipe['delete_head_component_ids'])
checks['retained_vertices_unmoved']=build['weld']['max_retained_vertex_coordinate_delta']==0.0
normals=build['normals']['retained_corner_normal_evidence']
checks['retained_normals_mapped']=normals['retained_faces_matched']==build['exact_deletion']['remaining_faces']
checks['retained_normals_within_tolerance']=normals['max_abs_component_delta']<=0.002
captures=read(EXP/'source/capture_record.json')
checks['ten_captures']=len(captures)==10
for view in ('front','side','back','quarter','head_back'):
    a=next(x for x in captures if x['state']=='before' and x['view']==view)
    b=next(x for x in captures if x['state']=='after' and x['view']==view)
    checks[view+'_same_camera']=a['camera_world_matrix']==b['camera_world_matrix']
    for item in (a,b):
        path=EXP/'evidence'/item['file']
        checks[item['state']+'_'+view+'_capture']=sha(path)==item['sha256'] and Image.open(path).size==(1280,720)
glb=EXP/'model/protagonist_cn_cleanup_v1.glb'
data=glb.read_bytes()
magic,version,total=struct.unpack_from('<4sII',data)
length,kind=struct.unpack_from('<II',data,12)
doc=json.loads(data[20:20+length])
checks['valid_glb_header']=magic==b'glTF' and version==2 and total==len(data) and kind==0x4E4F534A
checks['only_candidate_mesh_exported']=len(doc.get('meshes',[]))==1
checks['no_qa_cameras_in_glb']=not doc.get('cameras')
checks['no_rig_or_texture_claim']=not doc.get('skins') and not doc.get('images')
checks['no_uv_claim']=all('TEXCOORD_0' not in p['attributes'] for m in doc['meshes'] for p in m['primitives'])
class Links(HTMLParser):
    def __init__(self):super().__init__();self.paths=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ('src','href') and v and not v.startswith(('http','#')):self.paths.append(v)
parser=Links();parser.feed((EXP/'preview.html').read_text(encoding='utf-8'))
checks['preview_links_exist']=all((EXP/p).is_file() for p in parser.paths)
report={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
        'scope':'Integrity and packaging only; user visual acceptance pending, no animation/game validation.',
        'artifacts':{str(p.relative_to(EXP)).replace('\\','/'):sha(p) for p in (EXP/'model').iterdir() if p.suffix in ('.blend','.glb')}}
(EXP/'source/delivery_validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(report['status'],sum(checks.values()),'/',len(checks))
assert all(checks.values()),[k for k,v in checks.items() if not v]
