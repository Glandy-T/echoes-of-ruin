"""Read-only source/packaging/capture checks; never a substitute for visual acceptance."""
from pathlib import Path
import json,hashlib,struct,subprocess
from PIL import Image

HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
ASSET=ROOT/'assets/art/cryo_stair_material_sample_v1'
def same(a,b):
    return a.size==b.size and a.convert('RGBA').tobytes()==b.convert('RGBA').tobytes()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks={};usage=0;context_changes={}
for job in json.loads((HERE/'requests.json').read_text()):
    name=job['name'];raw=Image.open(EXP/'raw'/f'{name}.png')
    result=json.loads((EXP/f'result_{name}.json').read_text())
    checks[name+'_job_completed']=result['status']=='completed'
    usage+=result['usage']['generations']
    if job.get('adopted') is False:continue
    output=job.get('output_name',name)
    image=Image.open(ASSET/f'{output}.png')
    crop=raw.crop(tuple(job['retained_crop']))
    if output=='mineral_a':
        checks[name+'_native_base']=same(crop,Image.open(HERE/'layers/mineral_a_PixelLab_native.png'))
        overlay=Image.open(HERE/'layers/mineral_a_background_refine.png').convert('RGBA')
        checks[name+'_aseprite_local_layer_composite']=same(Image.alpha_composite(crop.convert('RGBA'),overlay),image)
        source_pixels=crop.convert('RGBA').tobytes();final_pixels=image.convert('RGBA').tobytes()
        changes=[(tuple(source_pixels[i:i+4]),tuple(final_pixels[i:i+4])) for i in range(0,len(source_pixels),4) if source_pixels[i:i+4]!=final_pixels[i:i+4]]
        checks[name+'_only_declared_flat_background_color_corrected']=bool(changes) and all(a==(122,139,139,255) and b==(124,131,128,255) for a,b in changes)
    else:checks[name+'_native_crop']=same(crop,image)
    checks[name+'_aseprite_readback']=same(image,Image.open(HERE/f'readback_{output}.png'))
    guide=Image.open(HERE/job['guide'])
    context_a=raw.crop((192,0,256,256)).convert('RGBA').tobytes()
    context_b=guide.crop((192,0,256,256)).convert('RGBA').tobytes()
    context_changes[name]=sum(context_a[i:i+4]!=context_b[i:i+4] for i in range(0,len(context_a),4))
    checks[name+'_context_excluded_from_export']=job['retained_crop'][2]<=192
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
checks['six_requests_total60']=usage==60
before=Image.open(EXP/'evidence/before_quiet_overview.png')
checks['quiet_revision_changes_visible_pixels']=not same(before,Image.open(EXP/'evidence/material_overview.png'))
def geometry_signature(data):
    n,t=struct.unpack_from('<II',data,12)
    doc=json.loads(data[20:20+n]);binary=data[20+n+8:]
    chunks=[]
    for accessor in doc['accessors']:
        view=doc['bufferViews'][accessor['bufferView']]
        width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[accessor['type']]
        size={5121:1,5123:2,5125:4,5126:4}[accessor['componentType']]*width
        offset=view.get('byteOffset',0)+accessor.get('byteOffset',0)
        stride=view.get('byteStride',size)
        packed=b''.join(binary[offset+i*stride:offset+i*stride+size] for i in range(accessor['count']))
        chunks.append((accessor['type'],accessor['componentType'],accessor['count'],hashlib.sha256(packed).hexdigest()))
    return doc['nodes'],doc['meshes'],chunks
baseline=subprocess.check_output(['git','show','0a4f14a7f3b07c24bb0c52d03b8c2f6f8a4a760f:assets/art/cryo_stair_material_sample_v1/stair_material_sample_v1.glb'],cwd=ROOT)
checks['nodes_geometry_normals_uv_indices_unchanged']=geometry_signature(baseline)==geometry_signature(blob)
report={'status':'TECHNICAL_CHECKS_PASS' if all(checks.values()) else 'CHECK_FAILURE','checks':checks,'unexported_protected_context_changed_pixels':context_changes,'context_note':'Service changed a few protected-context pixels; context excluded from every exported mineral/edge texture. Not claimed pixel-exact outside mask.','usage_generations':usage,'remaining_generations_after_batch':131,'glb_sha256':sha(ASSET/'stair_material_sample_v1.glb'),'blend_sha256':sha(EXP/'model/stair_material_sample_v1.blend'),'capture_script_sha256':sha(ROOT/'scripts/dev/cryo_stair_material_sample_v1.gd'),'evidence_sha256':{r['file']:sha(EXP/'evidence'/r['file']) for r in records},'visual_review':{'observed':'A renders as matte gray fine-cluster mineral; step front edges are readable; reused r24 lower-wall material visible; B is substantially coarser. Distinct UV phases reduce exact two-step repetition.','limitations':['A still has broad darker patina patches and visibly reused grain; user must review whether these suit the fine mineral direction.','No full stairwell, return flight, ceiling, full-wall treatment, final handrail, movement validation, motion lighting or final bake.','The stair side/support and cropped wall edges are technical cutaway surfaces, not final architectural finish.'],'user_acceptance':'PENDING'}}
report['remaining_generations_after_batch']=101  # Read-only API snapshot after masked middle on 2026-11-05.
report['revision']='masked_middle: original A with three local PixelLab contrast edits; quiet1 rejected, full-image middle ineffective'
report['aseprite_local_refinement']={'layer':'local_refine_AI_mask_background_7A8B8B_to_7C8380','operation':'Only replace AI-introduced flat background color #7A8B8B with original #7C8380; no new grains or aging painted.','changed_pixels':len(changes)}
report['visual_review']={'observed':'Current candidate targets only three existing strong-contrast patches; retains original fine mineral clusters elsewhere. Same-camera original and rejected quiet1 retained. Existing nosing detail and r24 wall remain.','limitations':['This intermediate finish still awaits user review; original A was too busy and quiet1 was rejected as too flat.','No full stairwell, return flight, ceiling, full-wall treatment, final handrail, movement validation, motion lighting or final bake.'],'user_acceptance':'PENDING'}
provenance=json.loads((EXP/'texture_provenance.json').read_text())
for entry in provenance:
    entry['final_runtime_png_sha256']=sha(ASSET/(entry['output_name']+'.png'))
    entry['local_refinement']='Aseprite one flat background color corrected on independent layer' if entry['output_name']=='mineral_a' else 'none; Aseprite packaging only'
    if 'export_sha256' in entry:entry['native_crop_png_sha256']=entry.pop('export_sha256')
(EXP/'texture_provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
(EXP/'validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(report['status'],f'{sum(checks.values())}/{len(checks)}', 'usage',usage)
assert all(checks.values()),[k for k,v in checks.items() if not v]
