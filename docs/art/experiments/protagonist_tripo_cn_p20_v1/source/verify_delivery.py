"""Verify downloaded sources and inspection packaging; not an artistic approval."""
from pathlib import Path
import hashlib,json,struct,zipfile
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
record=json.loads((HERE/'generation_record.json').read_text())
audit=json.loads((HERE/'mesh_audit.json').read_text())
readback=json.loads((HERE/'blend_readback.json').read_text())
checks={}
for name,data in record['download']['files'].items():
    p=EXP/'model'/name
    checks[name+'_exact_download']=p.stat().st_size==data['bytes'] and sha(p)==data['sha256']
with zipfile.ZipFile(EXP/'model/protagonist_tripo_cn_p20_v1_raw.zip') as archive:
    for name in archive.namelist():checks[name+'_matches_original_archive']=archive.read(name)==(EXP/'model'/name).read_bytes()
checks['front_input_exact']=sha(HERE/'input_front.png')==record['input']['front_sha256']
checks['back_input_exact']=sha(HERE/'input_back.png')==record['input']['back_sha256']
checks['only_one_generation_recorded']=record['submission_count']==1
checks['private_generation']=record['requested_settings']['privacy']=='Private'
checks['no_international_credits_used']=record['region']=='cn' and record['credits_consumed_observed']==0
checks['raw_preserved_in_inspection']=audit['raw_files_unchanged_during_inspection']
primary=audit['primary_export']['meshes'][0]
glb=audit['glb_export_inspected_separately']['meshes'][0]
checks['quad_source_kept']=primary['quad_polygons']==2486 and primary['triangle_polygons']==534 and primary['polygons']==3020
checks['glb_triangles_distinguished']=glb['polygons']==5506 and glb['quad_polygons']==0
checks['no_implicit_uv_or_rig_claim']=not primary['uv_layers'] and not audit['primary_export']['armatures']
for name in ('front','side','back','quarter','head_back'):
    checks[name+'_1280x720']=Image.open(EXP/f'evidence/blender_{name}.png').size==(1280,720)
checks['web_crop_only_model']=Image.open(EXP/'evidence/tripo_front.png').size==(300,470)
checks['blend_source_saved']=(EXP/'model/protagonist_cn_p20_inspection.blend').stat().st_size>0
report={'status':'DELIVERY_CHECKS_PASS' if all(checks.values()) else 'CHECK_FAILURE','checks':checks,'saved_blend_readback':readback,'art_status':'USER_REVIEW_PENDING_STARTING_MESH_ONLY','known_limits':['Exported ground plane included','Thin hair fragments and rough hands/feet remain','No UV, skeleton, deformation, game-camera or runtime validation'],'artifacts_sha256':{str(p.relative_to(EXP)).replace('\\','/'):sha(p) for p in (EXP/'model').iterdir() if p.suffix in ('.glb','.obj','.mtl','.zip','.blend')}}
(HERE/'delivery_validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
record['blender_inspection']={'version':audit['blender_version'],'primary_source':'OBJ','OBJ_polygons':primary['polygons'],'OBJ_quads':primary['quad_polygons'],'OBJ_triangles':primary['triangle_polygons'],'GLB_triangles':glb['polygons'],'raw_geometry_modified':False,'UV_layers':len(primary['uv_layers']),'armatures':len(audit['primary_export']['armatures']),'user_art_approval':False}
(HERE/'generation_record.json').write_text(json.dumps(record,indent=2,ensure_ascii=False),encoding='utf-8')
print(report['status'],sum(checks.values()),'/',len(checks))
assert all(checks.values()),[k for k,v in checks.items() if not v]
