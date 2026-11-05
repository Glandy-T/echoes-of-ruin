"""Read-only source/packaging/capture checks; never a substitute for visual acceptance."""
from pathlib import Path
import json,hashlib,struct
from PIL import Image

HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
ASSET=ROOT/'assets/art/cryo_stair_material_sample_v1'
def same(a,b):
    return a.size==b.size and a.convert('RGBA').tobytes()==b.convert('RGBA').tobytes()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks={};usage=0;context_changes={}
for job in json.loads((HERE/'requests.json').read_text()):
    name=job['name'];raw=Image.open(EXP/'raw'/f'{name}.png')
    image=Image.open(ASSET/f'{name}.png')
    checks[name+'_native_crop']=same(raw.crop(tuple(job['retained_crop'])),image)
    checks[name+'_aseprite_readback']=same(image,Image.open(HERE/f'readback_{name}.png'))
    guide=Image.open(HERE/job['guide'])
    context_a=list(raw.crop((192,0,256,256)).convert('RGBA').getdata())
    context_b=list(guide.crop((192,0,256,256)).convert('RGBA').getdata())
    context_changes[name]=sum(a!=b for a,b in zip(context_a,context_b))
    checks[name+'_context_excluded_from_export']=job['retained_crop'][2]<=192
    result=json.loads((EXP/f'result_{name}.json').read_text())
    checks[name+'_job_completed']=result['status']=='completed'
    usage+=result['usage']['generations']
wall=Image.open(ROOT/'assets/art/room1_wall_detail_full_r24/wall_left.png').crop((0,40,728,272))
checks['wall_exact_r24_native_crop']=same(wall,Image.open(ASSET/'wall_body.png'))
checks['wall_aseprite_readback']=same(wall,Image.open(HERE/'readback_wall_body.png'))
blob=(ASSET/'stair_material_sample_v1.glb').read_bytes()
magic,version,length=struct.unpack_from('<III',blob)
chunklen,chunktype=struct.unpack_from('<II',blob,12)
gltf=json.loads(blob[20:20+chunklen])
checks['glb2_valid_header']=magic==0x46546c67 and version==2 and length==len(blob)
checks['glb_images_embedded']=all('bufferView' in i for i in gltf['images'])
checks['glb_no_camera_or_lights']=not gltf.get('cameras') and 'KHR_lights_punctual' not in gltf.get('extensions',{})
checks['glb_nearest_magnification']=all(s.get('magFilter')==9728 for s in gltf['samplers'])
records=json.loads((EXP/'evidence/capture_record.json').read_text())
checks['five_runtime_captures']=len(records)==5
checks['capture_resolution']=all(Image.open(EXP/'evidence'/r['file']).size==(1280,720) for r in records)
checks['comparison_camera_identical']=records[0]['transform']==records[1]['transform']==records[4]['transform']
checks['comparison_fov_identical']=all(r['fov']==48 for r in records)
checks['candidate_b_visibly_different_bytes']=sha(EXP/'evidence/material_overview.png')!=sha(EXP/'evidence/candidate_b_overview.png')
checks['three_requests_total30']=usage==30
report={'status':'TECHNICAL_CHECKS_PASS' if all(checks.values()) else 'CHECK_FAILURE','checks':checks,'unexported_protected_context_changed_pixels':context_changes,'context_note':'Service changed a few protected-context pixels; context excluded from every exported mineral/edge texture. Not claimed pixel-exact outside mask.','usage_generations':usage,'remaining_generations_after_batch':131,'glb_sha256':sha(ASSET/'stair_material_sample_v1.glb'),'blend_sha256':sha(EXP/'model/stair_material_sample_v1.blend'),'capture_script_sha256':sha(ROOT/'scripts/dev/cryo_stair_material_sample_v1.gd'),'evidence_sha256':{r['file']:sha(EXP/'evidence'/r['file']) for r in records},'visual_review':{'observed':'A renders as matte gray fine-cluster mineral; step front edges are readable; reused r24 lower-wall material visible; B is substantially coarser. Distinct UV phases reduce exact two-step repetition.','limitations':['A still has broad darker patina patches and visibly reused grain; user must review whether these suit the fine mineral direction.','No full stairwell, return flight, ceiling, full-wall treatment, final handrail, movement validation, motion lighting or final bake.','The stair side/support and cropped wall edges are technical cutaway surfaces, not final architectural finish.'],'user_acceptance':'PENDING'}}
(EXP/'validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(report['status'],f'{sum(checks.values())}/{len(checks)}', 'usage',usage)
assert all(checks.values()),[k for k,v in checks.items() if not v]
