"""World-aligned native inputs/masks; PixelLab supplies every new material pixel."""
from pathlib import Path
import json, hashlib, shutil
import numpy as np
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent; EXP=HERE.parent; ROOT=HERE.parents[4]
R25=ROOT/'docs/art/experiments/room1_floor_detail_r25/source'
W,H=1648,728
for name in ['raw','editable','evidence','source/layers']:(EXP/name).mkdir(parents=True,exist_ok=True)
for name in ['jobs.py','pixellab_api.py']:shutil.copyfile(R25/name,HERE/name)
(HERE/'jobs.py').write_text((HERE/'jobs.py').read_text().replace('R25_PIXELLAB_QUEUE_COMPLETE','R26_PIXELLAB_QUEUE_COMPLETE'),encoding='utf8')
original=Image.open(ROOT/'assets/art/room1_floor_variants_r15/floor_with_leaks.png').convert('RGBA')
current=Image.open(ROOT/'assets/art/room1_pixel_unify_r22/floor_with_leaks.png').convert('RGBA')
approved=Image.open(ROOT/'assets/art/room1_floor_detail_r25/floor_candidate.png').convert('RGBA')
assert original.size==current.size==approved.size==(W,H)
footprint_path=HERE/'current_pod_footprints.json'
assert footprint_path.exists(),'Current-model floor mask must be verified before paid submission.'
pods=json.loads(footprint_path.read_text(encoding='utf8'))['pods']
occupied=Image.new('L',(W,H),0);d=ImageDraw.Draw(occupied)
for pod in pods:d.polygon([tuple(p) for p in pod['pixel_polygon']],fill=255)
occupied=np.asarray(occupied)>0
accepted=np.zeros((H,W),bool)
accepted[96:352,168:424]=np.asarray(Image.open(R25/'mask_candidate.png').convert('L'))>0
editable=~(occupied|accepted)
guide=np.array(original)
guide[occupied]=np.asarray(current)[occupied]
guide[accepted]=np.asarray(approved)[accepted]
Image.fromarray(guide).save(HERE/'world_guide.png')
Image.fromarray(np.where(editable,255,0).astype('uint8')).save(HERE/'world_edit_mask.png')
Image.fromarray(np.where(occupied,255,0).astype('uint8')).save(HERE/'occupied_mask.png')
Image.fromarray(np.where(accepted,255,0).astype('uint8')).save(HERE/'approved_r25_material_mask.png')
common='''Revise this OWN PROJECT flat top-down FLOOR ALBEDO into finished native 256x256 pixel art. Match the supplied cool matte blue-gray coating and fine detail density, without enlargement. WHITE mask is floor material. BLACK is exact occupied cryopod floor or already approved material, NOT new objects, tiles or panels. Preserve their arrangement. Attach old contact film directly to real footprint boundaries: uneven width, interrupted edges, irregular connected groups and smaller 1-3 pixel stepped fringes thinning into intact coating. Retain broad quiet areas with low-contrast material variation; do not flatten the surface to empty color. Use varied small and medium clusters and selected finer transitions, not large rounded chunks, wide peeling islands or uniform pepper noise. Maintain the existing source blue-gray palette, subtle contrast and localized dry residue positions. Give this location a NEW distribution of small attached clusters and fine transitions rather than copying another patch or stamping repeated round islands. No new leaks; only keep residue where already supplied. No yellow, green, brown, rust, moss, white powder, bright outlines, closed rectangular borders, long scratches, cracks, route marks, seams, tile joints, grid, text, equipment, perspective, cast light, shadows, glow, reflections or wet highlights. This is continuous flat material color, not a scene illustration. Carry material naturally through ordinary canvas edges; never frame the patch. Black is protected; replace WHITE entirely with newly revised material, not an overlay of old grime. '''
jobs=[];tiles=[]
xs=[0,232,464,696,928,1160,1392];ys=[0,236,472]
for row,y in enumerate(ys):
    for col,x in enumerate(xs):
        name=f'floor_{row*len(xs)+col+1:02d}'
        box=(x,y,x+256,y+256)
        Image.fromarray(guide).crop(box).save(HERE/f'guide_{name}.png')
        Image.fromarray(np.where(editable,255,0).astype('uint8')).crop(box).save(HERE/f'mask_{name}.png')
        real=[]
        if row==0:real.append('TOP')
        if row==len(ys)-1:real.append('BOTTOM')
        if col==0:real.append('LEFT')
        if col==len(xs)-1:real.append('RIGHT')
        edge=('Actual wall contact exists only at '+','.join(real)+' canvas edge(s); keep its fine broken deposits continuous.' if real else 'No canvas edge is a wall contact here; do not add border deposits.')
        variations=[
            'Bias small contact groups to different real corners; keep a thin irregular fringe.',
            'Favor short broken attached groups, with variable quiet gaps between contacts.',
            'Use different small clustered transitions around real contacts; avoid a uniform ring.',
            'Keep intact centers and more varied fragmented contact ends, no large blotches.',
        ]
        prompt=common+edge+' '+variations[(row*3+col)%4]
        assert len(prompt)<=2000,len(prompt)
        (HERE/f'prompt_{name}.txt').write_text(prompt,encoding='utf8')
        jobs.append({'name':name,'endpoint':'/inpaint-v3','prompt':f'prompt_{name}.txt','guide':f'guide_{name}.png','mask':f'mask_{name}.png','seed':2026103600+row*7+col,'native_size':[256,256]})
        tiles.append({'name':name,'row':row,'column':col,'origin_px':[x,y],'native_size':[256,256],'actual_wall_edges':real})
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf8')
(HERE/'tile_layout.json').write_text(json.dumps({'canvas':[W,H],'native_scale':1,'tiles':tiles,'overlap_x':24,'overlap_y':20,'all_origins_world_aligned':True,'resize_or_flip':False},indent=2),encoding='utf8')
baseline=json.loads((R25/'baseline_file_hashes.json').read_text())
optional={}
for path in ['assets/art/cryopod_standard_v8/closed_raw_irradiance.exr','assets/art/cryopod_standard_v8/open_raw_irradiance.exr']:
    if path in baseline:optional[path]=baseline.pop(path)
(HERE/'optional_local_legacy_hashes.json').write_text(json.dumps(optional,indent=2),encoding='utf8')
for f in (ROOT/'assets/art/room1_floor_detail_r25').glob('*.png'):baseline[f.relative_to(ROOT).as_posix()]=hashlib.sha256(f.read_bytes()).hexdigest()
for path in ['docs/art/experiments/room1_wall_detail_full_r24/room1_wall_detail_full_r24.blend','scripts/dev/room1_floor_detail_r25.gd']:
    baseline[path]=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
(HERE/'baseline_file_hashes.json').write_text(json.dumps(baseline,indent=2),encoding='utf8')
(HERE/'input_provenance.json').write_text(json.dumps({'guide_sources':['r15 original native PixelLab floor','r25 approved C effective material','r22 occupied hidden pixels only'],'canvas':[W,H],'mapping':'u=(world_x-.2)*80; v=(world_z+9.3)*80','native_tile_size':[256,256],'new_original_requests':len(jobs),'resampling':False,'PixelCanals_content_submitted':False,'C_area_excluded_from_first21_requests':int(accepted.sum()),'r25_old_8px_sample_join':'Not retained as a frame; the whole-floor material reconnects these pixels.','fixed_leaks':['P03','P06','P13','P18'],'occupied_mask_source':'current_pod_footprints.json','script_material_art':False},indent=2),encoding='utf8')
(EXP/'.gitignore').write_text('*.log\n*.log.*\n*.err\n*.blend1\n__pycache__/\nsource/balance_*.json\n',encoding='utf8')
print('R26_PREPARED',len(jobs),'independent native256 world patches; estimate',len(jobs)*10,'generations')
