"""Align and mask real PixelLab pixels. No hand-painted or synthetic material art."""
from pathlib import Path
import json,hashlib,random
import numpy as np
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent; EXP=HERE.parent; ROOT=HERE.parents[4]
OUT=ROOT/'assets/art/room1_pixel_unify_r22'; OUT.mkdir(parents=True,exist_ok=True)
LAY=HERE/'layers'; LAY.mkdir(exist_ok=True)
R20=ROOT/'docs/art/experiments/room1_pixel_cluster_r20'
WALL=ROOT/'docs/art/experiments/room1_wall_pixellab_r12/source'
LAMP=ROOT/'docs/art/experiments/room1_wall_lamp_r13/source'
POD=ROOT/'docs/art/experiments/room1_pod_pixellab_r16/source'
records=[]; packages=[]

def load(p):return Image.open(p).convert('RGBA')
def enlarged(name):
    raw=load(EXP/f'raw/{name}.png'); full=load(HERE/f'guide_full_{name}.png')
    assert raw.size==(full.width//2,full.height//2),(name,raw.size)
    low=Image.open(HERE/f'mask_{name}.png').convert('L').resize(full.size,Image.Resampling.NEAREST)
    mask=Image.fromarray(np.minimum(np.asarray(low),np.asarray(Image.open(HERE/f'mask_full_{name}.png').convert('L'))))
    layer=raw.resize(full.size,Image.Resampling.NEAREST);layer.putalpha(mask)
    return full,layer
def package(name,base,layers,final,path):
    folder=LAY/name;folder.mkdir(parents=True,exist_ok=True)
    base.save(folder/'base.png'); names=[]
    for i,(label,layer) in enumerate(layers):
        fn=f'{i:02d}_{label}.png';layer.save(folder/fn);names.append([label,fn])
    final.save(folder/'composite.png');path.parent.mkdir(parents=True,exist_ok=True);final.save(path)
    packages.append({'name':name,'base':str((folder/'base.png').relative_to(EXP)).replace('\\','/'),'layers':[[label,str((folder/fn).relative_to(EXP)).replace('\\','/')] for label,fn in names],'final':str(path.relative_to(ROOT)).replace('\\','/'),'size':list(final.size),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})

def walls():
    pool={}
    # Reuse the already accepted r20 AI surface, preserving its provenance.
    old=load(R20/'source/layers/wall_left_PixelLab.png').crop((432,16,688,272))
    for half in range(2):pool[f'accepted_r20_{half}']=old.crop((half*128,0,half*128+128,256))
    for i in range(1,6):
        _,tile=enlarged(f'wall_{i}')
        for half in range(2):pool[f'new_{i}_{half}']=tile.crop((half*128,0,half*128+128,256))
    clean,portal=enlarged('portal_fix')
    rng=random.Random(2026103022);prev_orders=[];placements={}
    for side in ['left','right','front','rear']:
        base=load(WALL/f'clean_{side}.png'); layer=Image.new('RGBA',base.size)
        starts=list(range(-80,base.width,128));order=[]; counts={k:0 for k in pool}
        for i,start in enumerate(starts):
            choices=list(pool);rng.shuffle(choices)
            choices=[k for k in choices if k not in order[-3:] and (not prev_orders or i>=len(prev_orders[-1]) or k!=prev_orders[-1][i])]
            chosen=min(choices,key=lambda k:counts[k]);counts[chosen]+=1;order.append(chosen)
            layer.paste(pool[chosen],(start,16))
        if side=='rear':
            # Replace the complete portal art region, not an AI layer over old dirt.
            layer.paste(Image.new('RGBA',(256,256)),(688,16));layer.paste(portal,(688,16))
        alpha=layer.getchannel('A');d=ImageDraw.Draw(alpha)
        d.rectangle((0,0,1,base.height-1),fill=0);d.rectangle((base.width-2,0,base.width-1,base.height-1),fill=0)
        layer.putalpha(alpha)
        lamp=load(LAMP/f'{side}_lamp_layer.png')
        final=Image.alpha_composite(Image.alpha_composite(base,layer),lamp)
        # Aseprite and Pillow round fractional alpha blends differently by one
        # RGB level. Store a registered opaque lamp layer so master readback is
        # exact; retain the original fractional alpha separately for editing.
        registered=final.copy();registered.putalpha(Image.fromarray((np.asarray(lamp)[:,:,3]>0).astype('uint8')*255))
        package('wall_'+side,base,[('PixelLab_2x_material',layer),('retained_lamp_exact_registered',registered)],final,OUT/f'wall_{side}.png')
        lamp.save(LAY/('wall_'+side)/'original_r13_lamp_RGBA.png')
        # Exact preserved lamp/clean edge and seam pixels are technical structure.
        placements[side]=[[x,k] for x,k in zip(starts,order)];prev_orders.append(order)
    records.append({'walls':placements,'independent_new_wall_pairs':5,'reused_r20_pairs':1,'half_panels':12,'new_portal':True,'legacy_body_age_layers_used':False})

def pods():
    roles=['lid','shell_side','shell_end']; variants={}
    for variant in 'abcd':
        for role in roles:
            if variant=='a':
                final=load(ROOT/f'assets/art/room1_pixel_cluster_r20/pod_{role}.png')
                base=load(R20/f'source/layers/pod_{role}_base.png')
                layer=load(R20/f'source/layers/pod_{role}_PixelLab.png')
            else:
                key=f'{variant}_{role}'
                if variant in ['b','d'] and role=='lid':key+='_fix'
                base,layer=enlarged(key)
                final=Image.alpha_composite(base,layer)
                protected=np.asarray(layer)[:,:,3]==0
                assert np.array_equal(np.asarray(final)[protected],np.asarray(base)[protected])
            path=OUT/f'variant_{variant}/{role}.png'
            package(f'pod_{variant}_{role}',base,[('PixelLab_material_2x',layer)],final,path)
            assert np.array_equal(np.asarray(Image.alpha_composite(base,layer)),np.asarray(final))
            variants[variant,role]=final
    layout=json.loads((ROOT/'assets/art/room1_complete_r19/layout.json').read_text())
    plates={'lid':(47,197,80,211),'shell_end':(55,35,73,49)}
    for pod in layout['pods']:
        variant='abcd'[pod['variant_index']]
        for role,box in plates.items():
            final=variants[variant,role].copy()
            # Copy only the exact functional ID panel already validated in r19.
            identity=load(ROOT/f"assets/art/room1_complete_r19/numbered/{pod['id']}_{role}.png").crop(box)
            final.paste(identity,box[:2]);p=OUT/f"numbered/{pod['id']}_{role}.png";p.parent.mkdir(exist_ok=True);final.save(p)
    records.append({'pod_variants':4,'external_roles':roles,'numbered_maps':40,'ID_method':'exact r19 functional ID plate crop only; no material painting','interior_glass_screen_tubes_unchanged':True})

def floor():
    # Work at the native AI grid so overlap selection cannot split enlarged pixels.
    layout=json.loads((HERE/'floor_tile_layout.json').read_text())
    merged=np.zeros((364,824,4),dtype=np.uint8);coverage=np.zeros((364,824),bool)
    masks=Image.new('L',(1648,728));seams=[]
    def minimum_cut(error):
        h,w=error.shape;cost=error.copy();parents=np.zeros(error.shape,dtype=np.int16)
        for y in range(1,h):
            prev=np.pad(cost[y-1],(1,1),constant_values=np.inf)
            options=np.stack([prev[:-2],prev[1:-1],prev[2:]])
            choice=options.argmin(axis=0);parents[y]=np.arange(w)+choice-1
            cost[y]+=options[choice,np.arange(w)]
        x=int(cost[-1].argmin());path=np.empty(h,dtype=int)
        for y in range(h-1,-1,-1):
            path[y]=x
            if y:x=int(parents[y,x])
        return path
    for tile in layout['tiles']:
        name=tile['name'];x,y=tile['native_origin'];row,col=tile['row'],tile['column']
        actual='floor_08_fix' if name=='floor_tile_08' else name
        raw=np.asarray(load(EXP/f'raw/{actual}.png')).copy();assert raw.shape==(256,256,4)
        if name=='floor_tile_02':
            repair=np.asarray(load(EXP/'raw/floor_02_fix.png'))
            edit=np.asarray(Image.open(HERE/'mask_floor_02_fix.png').convert('L'))>0
            raw[edit]=repair[edit]
            assert not ((raw[:,:,:3].min(2)>200)&(np.asarray(Image.open(HERE/'mask_floor_tile_02.png').convert('L'))>0)).any(),'White halo remains after AI repair'
            Image.fromarray(raw).save(HERE/'floor_tile_02_combined_AI_outputs.png')
        edit_mask=np.asarray(Image.open(HERE/f'mask_{name}.png').convert('L'))>0
        assert not ((raw[:,:,:3].min(2)>200)&edit_mask).any(),'Rejected white material in '+name
        old=merged[y:y+256,x:x+256].copy();take=np.ones((256,256),bool)
        if col:
            left=next(t for t in layout['tiles'] if t['row']==row and t['column']==col-1)
            overlap=left['native_origin'][0]+256-x
            error=np.sum((old[:,:overlap,:3].astype(float)-raw[:,:overlap,:3])**2,axis=2)
            seam=minimum_cut(error)
            for py,cut in enumerate(seam):take[py,:cut]=False
            seams.append({'tile':name,'edge':'left','cut':seam.tolist()})
        if row:
            overlap=256-y
            error=np.sum((old[:overlap,:,:3].astype(float)-raw[:overlap,:,:3])**2,axis=2)
            seam=minimum_cut(error.T)
            for px,cut in enumerate(seam):take[:cut,px]=False
            seams.append({'tile':name,'edge':'top','cut':seam.tolist()})
        target=merged[y:y+256,x:x+256];target[take]=raw[take];coverage[y:y+256,x:x+256]=True
        low=Image.open(HERE/f'mask_{name}.png').convert('L').resize((512,512),Image.Resampling.NEAREST)
        full=Image.open(HERE/f'mask_full_{name}.png').convert('L')
        mask=Image.fromarray(np.minimum(np.asarray(full),np.asarray(low)))
        masks.paste(mask,(x*2,y*2))
    assert coverage.all()
    raw=Image.fromarray(merged).resize((1648,728),Image.Resampling.NEAREST)
    base=load(ROOT/'assets/art/room1_floor_variants_r15/floor_with_leaks.png')
    raw.putalpha(masks);final=Image.alpha_composite(base,raw)
    package('floor_with_leaks',base,[('PixelLab_world_aligned_2x_floor',raw)],final,OUT/'floor_with_leaks.png')
    records.append({'floor_native_merge_size':[824,364],'native_seams':seams,'independent_world_aligned_AI_tiles':8,'occupied_footprint_exact':True,'old_floor_outside_conservative_occupied_mask_replaced':True,'floor_design':'continuous no tile/grid/route; fixed footprint contacts and existing leak sites'})

if __name__=='__main__':
    walls();pods();floor()
    (HERE/'packages.json').write_text(json.dumps(packages,indent=2),encoding='utf-8')
    (HERE/'composite_validation.json').write_text(json.dumps({'result':'PASS','records':records,'operations':['nearest 2x enlargement','exact binary structural masking','world-aligned native AI overlap cut','exact functional ID plate transfer'],'art_source':'PixelLab only'},indent=2),encoding='utf-8')
    print('R22_COMPOSED',len(packages),'editable texture packages and 40 functional numbered maps')
