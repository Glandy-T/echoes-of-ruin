"""Arrange native PixelLab wall panels; preserve exact existing lamp/construction pixels."""
from pathlib import Path
import json,random,hashlib
from PIL import Image,ImageDraw
import numpy as np
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
R23=ROOT/'docs/art/experiments/room1_wall_detail_r23'
LAMP=ROOT/'docs/art/experiments/room1_wall_lamp_r13/source'
OUT=ROOT/'assets/art/room1_wall_detail_full_r24';OUT.mkdir(parents=True,exist_ok=True)
mask=Image.open(R23/'source/mask.png').convert('L');pool={};raws={}
selection=json.loads((HERE/'selection.json').read_text()) if (HERE/'selection.json').exists() else {}
for key in 'abcdefgh':
    path=(R23 if key in 'ab' else EXP)/f"raw/{selection.get(key,key)}.png"
    raw=Image.open(path).convert('RGBA');assert raw.size==(256,256)
    raws[key]=raw.copy();raw.putalpha(mask)
    for half in range(2):pool[f'{key}{half}']=raw.crop((half*128,0,half*128+128,256))
walls=['left','right','front','rear']
bases={wall:Image.open(ROOT/f'assets/art/room1_pixel_unify_r22/wall_{wall}.png').convert('RGBA') for wall in walls}
starts={wall:list(range(-80,base.width,128)) for wall,base in bases.items()}
rng=random.Random(2026103444)
for attempt in range(10000):
    orders={wall:rng.sample(list(pool),len(starts[wall])) for wall in walls}
    if any(any(a[0]==b[0] for a,b in zip(seq,seq[1:])) for seq in orders.values()):continue
    if any(a==b for a,b in zip(orders['left'],orders['right'])):continue
    if any(a==b for a,b in zip(orders['front'],orders['rear'])):continue
    corners=[(orders['left'][-1],orders['rear'][0]),(orders['rear'][-1],orders['right'][-1]),(orders['right'][0],orders['front'][-1]),(orders['front'][0],orders['left'][0])]
    if any(a[0]==b[0] for a,b in corners):continue
    break
else:raise RuntimeError('Distinct wall panel arrangement failed')

portal_key=selection.get('portal','portal')
portal=Image.open(EXP/f'raw/{portal_key}.png').convert('RGBA');assert portal.size==(256,256)
portal.putalpha(Image.open(HERE/f'mask_{portal_key}.png').convert('L'))
packages=[];records={}
for wall in walls:
    base=bases[wall];layer=Image.new('RGBA',base.size)
    for start,key in zip(starts[wall],orders[wall]):layer.paste(pool[key],(start,16))
    if wall=='rear':layer.paste(portal,(688,16))
    alpha=np.array(layer.getchannel('A'))
    lamp=np.asarray(Image.open(LAMP/f'{wall}_lamp_layer.png').convert('RGBA'))[:,:,3]>0
    alpha[lamp]=0;alpha[:,:2]=0;alpha[:,-2:]=0
    layer.putalpha(Image.fromarray(alpha));final=Image.alpha_composite(base,layer)
    a=np.asarray(final);b=np.asarray(base);safe=alpha==0
    assert np.array_equal(a[safe],b[safe]);assert np.array_equal(a[lamp],b[lamp])
    folder=HERE/'layers'/wall;folder.mkdir(parents=True,exist_ok=True)
    base.save(folder/'base_r22.png');layer.save(folder/'PixelLab_all_new_material.png');final.save(folder/'composite.png')
    path=OUT/f'wall_{wall}.png';final.save(path)
    packages.append({'wall':wall,'output':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    records[wall]={'placements':[[x,key] for x,key in zip(starts[wall],orders[wall])],'no_repeated_half_panel_on_same_wall':len(set(orders[wall]))==len(orders[wall]),'adjacent_pairs_different':all(a[0]!=b[0] for a,b in zip(orders[wall],orders[wall][1:])),'portal_override':[688,16,944,272] if wall=='rear' else None,'lamp_and_protected_pixels_exact':True,'changed_material_pixels':int(np.any(a!=b,axis=2).sum())}
(HERE/'packages.json').write_text(json.dumps(packages,indent=2),encoding='utf-8')
(HERE/'assembly.json').write_text(json.dumps({'native_tile_size':[256,256],'scale':1,'independent_pairs':8,'half_panels':16,'reused_r23':['a','b'],'new_native_originals':[selection.get(k,k) for k in list('cdefgh')+['portal']],'wall_placements':records,'technical_operations':['native crop/placement','binary protection mask only'],'resampling':False,'mirroring':False,'procedural_aging':False,'legacy_sparse_layers_overlaid':False},indent=2),encoding='utf-8')
print('R24_COMPOSED 4 complete wall maps, 16 distinct native half panels, exact lamp protection')
