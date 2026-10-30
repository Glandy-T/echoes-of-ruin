"""Crop API-only padding, nearest 4x enlargement and exact protection masks."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
OUT=ROOT/'assets/art/room1_pixel_cluster_r21';OUT.mkdir(parents=True,exist_ok=True)
rows=[]
for job in json.loads((HERE/'requests.json').read_text()):
    key=job['name'];path=EXP/'raw'/f'{key}.png';raw=Image.open(path).convert('RGBA')
    assert list(raw.size)==job['native_size']
    correction=None
    if key=='shell_end' and (EXP/'result_shell_end_fix.json').exists():
        patch=Image.open(EXP/'raw/shell_end_fix.png').convert('RGBA');assert patch.size==raw.size
        repair_mask=Image.open(HERE/'mask_end_repair.png').convert('L')
        before=np.array(raw);raw=Image.composite(patch,raw,repair_mask)
        assert np.array_equal(np.array(raw)[np.array(repair_mask)==0],before[np.array(repair_mask)==0])
        editable=np.array(Image.open(HERE/'mask_shell_end.png').convert('L'))>0
        remaining=int(((np.array(raw)[:,:,:3].max(axis=2)<32)&editable).sum())
        assert remaining==0,('Rejected near-black material persists',remaining)
        raw.save(HERE/'shell_end_combined_AI_layers.png')
        correction={'original_raw':'raw/shell_end.png','PixelLab_repair_raw':'raw/shell_end_fix.png','mask':'source/mask_end_repair.png','repaired_raw_sha256':hashlib.sha256((EXP/'raw/shell_end_fix.png').read_bytes()).hexdigest(),'remaining_editable_near_black_pixels':remaining,'unmasked_original_AI_pixels_exact':True}
    content=raw.crop(job['content_box']);baseline=Image.open(HERE/f'baseline_{key}.png').convert('RGBA')
    lowmask=Image.open(HERE/f'mask_{key}.png').convert('L').crop(job['content_box'])
    mask=lowmask.resize(baseline.size,Image.Resampling.NEAREST)
    mask=Image.fromarray(np.minimum(np.asarray(mask),np.asarray(Image.open(HERE/f'mask_full_{key}.png').convert('L'))))
    layer=content.resize(baseline.size,Image.Resampling.NEAREST);layer.putalpha(mask)
    result=Image.alpha_composite(baseline,layer)
    assert np.array_equal(np.array(result)[np.array(mask)==0],np.array(baseline)[np.array(mask)==0])
    if key=='wall':
        base=Image.open(ROOT/'assets/art/room1_wall_lamp_r13/wall_left.png').convert('RGBA');whole=Image.new('RGBA',base.size);whole.paste(layer,(432,16));name='wall_left'
        final=Image.alpha_composite(base,whole)
        outside=np.ones((base.height,base.width),bool);outside[16:272,432:688]=False
        assert np.array_equal(np.array(final)[outside],np.array(base)[outside]);layer=whole
    else:base=baseline;final=result;name='pod_'+key
    base.save(HERE/'layers'/f'{name}_base.png');layer.save(HERE/'layers'/f'{name}_PixelLab.png');final.save(HERE/'layers'/f'{name}_composite.png');final.save(OUT/f'{name}.png')
    rows.append({'role':key,'canvas_size':job['native_size'],'native_content_size':list(content.size),'output_size':list(final.size),'scale':4,'protected_pixels_exact':True,'wall_outside_exact':True if key=='wall' else None,'changed_pixels':int(np.any(np.array(result)!=np.array(baseline),axis=2).sum()),'raw_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'PixelLab_correction':correction,'final_sha256':hashlib.sha256((OUT/f'{name}.png').read_bytes()).hexdigest()})
(HERE/'composite_validation.json').write_text(json.dumps({'result':'PASS','rows':rows,'technical_operations_only':['remove black-masked API padding','4x integer nearest enlargement','binary structural/ID protection'],'new_material_art':'PixelLab only'},indent=2),encoding='utf-8')
print('R21_COMPOSE_PASS')
