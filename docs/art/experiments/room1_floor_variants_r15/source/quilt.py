"""Native AI-pixel quilting: choose and align sources; synthesize no marks."""
from pathlib import Path
import numpy as np,json
from PIL import Image

def minimum_cut(error):
    """Top-to-bottom least squared color mismatch seam in a geometric overlap."""
    h,w=error.shape;cost=error.copy();parents=np.zeros((h,w),dtype=np.int16)
    for y in range(1,h):
        prev=np.pad(cost[y-1],(1,1),constant_values=np.inf)
        candidates=np.stack([prev[:-2],prev[1:-1],prev[2:]])
        parent=np.argmin(candidates,axis=0)
        parents[y]=np.arange(w)+parent-1
        cost[y]+=candidates[parent,np.arange(w)]
    x=int(np.argmin(cost[-1]));path=np.empty(h,dtype=int)
    for y in range(h-1,-1,-1):
        path[y]=x
        if y:x=int(parents[y,x])
    return path

def build(raw,source_dir,w=1648,h=728):
    ids=sorted(n for n in raw if n.startswith('base_'))
    assert len(ids)>=7,'Need genuine independent base variants before quilting.'
    # Global color-only alignment to the approved r14 base palette. Keep every
    # spatial mark and pixel cluster from PixelLab, not handwritten corrections.
    palette=np.unique(raw['base_00'].reshape(-1,3),axis=0)
    images={};lookups={}
    for n in ids:
        values,index=np.unique(raw[n].reshape(-1,3),axis=0,return_inverse=True)
        nearest=np.argmin(np.sum((values[:,None,:]-palette[None,:,:])**2,axis=2),axis=1)
        images[n]=palette[nearest[index]].reshape(raw[n].shape).astype(np.int16)
        lookups[n]=[{'raw_rgb':v.astype(int).tolist(),'aligned_rgb':palette[k].astype(int).tolist()} for v,k in zip(values,nearest)]
    canvas=np.zeros((h,w,3),dtype=np.int16);step=208;overlap=48
    grid={};counts={n:0 for n in ids};records=[];rng=np.random.default_rng(2026103015)
    for row,y in enumerate(range(0,h,step)):
        for col,x in enumerate(range(0,w,step)):
            ph=min(256,h-y);pw=min(256,w-x)
            old=canvas[y:y+ph,x:x+pw].copy()
            covered=np.zeros((ph,pw),dtype=bool)
            if col:covered[:,:overlap]=True
            if row:covered[:overlap,:]=True
            neighbors=[(row,col-1),(row,col-2),(row-1,col-1),(row-1,col),(row-1,col+1),(row-2,col)]
            banned={grid[p] for p in neighbors if p in grid}
            choices=[n for n in rng.permutation(ids) if n not in banned]
            assert choices
            scores={}
            for n in choices:
                diff=images[n][:ph,:pw].astype(float)-old
                mismatch=float(np.mean(np.sum(diff[covered]**2,axis=1))) if covered.any() else 0.0
                scores[n]=mismatch+counts[n]*30.0
            name=min(scores,key=scores.get);patch=images[name][:ph,:pw]
            take=np.ones((ph,pw),dtype=bool)
            if col:
                error=np.sum((patch[:,:overlap].astype(float)-old[:,:overlap])**2,axis=2)
                seam=minimum_cut(error)
                for py,cut in enumerate(seam):take[py,:cut]=False
            if row:
                error=np.sum((patch[:overlap,:].astype(float)-old[:overlap,:])**2,axis=2)
                seam=minimum_cut(error.T)
                for px,cut in enumerate(seam):take[:cut,px]=False
            target=canvas[y:y+ph,x:x+pw];target[take]=patch[take]
            grid[row,col]=name;counts[name]+=1
            records.append({'row':row,'column':col,'source':name,'origin_px':[x,y],'native_crop_size':[pw,ph],'scale':1,'rotation':0,'horizontal_flip':False,'changed_pixels':int(take.sum())})
    assert all(grid.get((r,c))!=grid.get((r,c-1)) for r,c in grid if c>0)
    assert all(grid.get((r,c))!=grid.get((r-1,c)) for r,c in grid if r>0)
    # Every output pixel must come from the AI palette; no interpolated shading.
    palette={tuple(v) for n in ids for v in np.unique(images[n].reshape(-1,3),axis=0)}
    assert all(tuple(v) in palette for v in np.unique(canvas.reshape(-1,3),axis=0))
    report={'method':'native-pixel minimum-error overlap cuts, no new painted material','palette_alignment_only':lookups,'step_px':step,'overlap_px':overlap,'sources':ids,'placements':records,'usage_counts':counts,'immediate_repeat_count':0,'native_source_palette_only':True}
    (source_dir/'base_quilt.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return canvas.astype(float)
