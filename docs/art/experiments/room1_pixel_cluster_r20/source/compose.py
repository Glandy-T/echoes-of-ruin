"""Nearest enlargement and exact technical masking only; PixelLab makes art."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
OUT=ROOT/'assets/art/room1_pixel_cluster_r20';OUT.mkdir(parents=True,exist_ok=True)
records=[]
for job in json.loads((HERE/'requests.json').read_text()):
    key=job['name'];raw=Image.open(EXP/'raw'/f'{key}.png').convert('RGBA')
    assert list(raw.size)==job['native_size'],(key,raw.size,job['native_size'])
    baseline=Image.open(HERE/f'baseline_{key}.png').convert('RGBA')
    mask=Image.open(HERE/f'mask_{key}.png').resize(baseline.size,Image.Resampling.NEAREST).convert('L')
    mask=Image.fromarray(np.minimum(np.asarray(mask),np.asarray(Image.open(HERE/f'mask_full_{key}.png').convert('L'))))
    enlarged=raw.resize(baseline.size,Image.Resampling.NEAREST);enlarged.putalpha(mask)
    result=Image.alpha_composite(baseline,enlarged)
    assert np.array_equal(np.asarray(result)[np.asarray(mask)==0],np.asarray(baseline)[np.asarray(mask)==0])
    if key=='wall':
        base=Image.open(ROOT/'assets/art/room1_wall_lamp_r13/wall_left.png').convert('RGBA')
        layer=Image.new('RGBA',base.size);layer.paste(enlarged,(432,16))
        final=Image.alpha_composite(base,layer);name='wall_left'
        outside=np.ones((base.height,base.width),dtype=bool);outside[16:272,432:688]=False
        assert np.array_equal(np.asarray(final)[outside],np.asarray(base)[outside])
    else:
        base=baseline;layer=enlarged;final=result;name='pod_'+key
    base.save(HERE/'layers'/f'{name}_base.png');layer.save(HERE/'layers'/f'{name}_PixelLab.png')
    final.save(OUT/f'{name}.png');final.save(HERE/'layers'/f'{name}_composite.png')
    records.append({'role':key,'output':str((OUT/f'{name}.png').relative_to(ROOT)).replace('\\','/'),'native_size':list(raw.size),'atlas_size':list(final.size),'grid_scale':2,'rgb_colors':len(final.convert('RGB').getcolors(final.width*final.height)),'protected_exact':True,'outside_wall_patch_exact':True if key=='wall' else None,'changed_pixels_vs_current':int(np.any(np.array(result)!=np.array(baseline),axis=2).sum()),'raw_sha256':hashlib.sha256((EXP/'raw'/f'{key}.png').read_bytes()).hexdigest(),'final_sha256':hashlib.sha256((OUT/f'{name}.png').read_bytes()).hexdigest()})
(HERE/'composite_validation.json').write_text(json.dumps({'result':'PASS','records':records,'technical_operations':['2x integer nearest enlargement','conservative binary masks','exact existing ID/structure preservation'],'art_pixels_source':'PixelLab inpaint-v3 only; no procedural aging or manual repaint'},indent=2),encoding='utf-8')
print('R20_COMPOSE_PASS 4 textures; protected structure and wall-outside region exact')
