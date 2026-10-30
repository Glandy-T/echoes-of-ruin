"""Select native PixelLab pixels through overlap cuts; draw no material marks."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]

def minimum_cut(error):
    h,w=error.shape;cost=error.copy();parents=np.zeros((h,w),dtype=np.int16)
    for y in range(1,h):
        prev=np.pad(cost[y-1],(1,1),constant_values=np.inf)
        choices=np.stack([prev[:-2],prev[1:-1],prev[2:]])
        parent=choices.argmin(axis=0);parents[y]=np.arange(w)+parent-1
        cost[y]+=choices[parent,np.arange(w)]
    x=int(cost[-1].argmin());path=np.empty(h,dtype=int)
    for y in range(h-1,-1,-1):
        path[y]=x
        if y:x=int(parents[y,x])
    return path

def build(only_ready=False):
    layout=json.loads((HERE/'tile_layout.json').read_text())
    guide=np.asarray(Image.open(HERE/'world_guide.png').convert('RGBA'))
    edit=np.asarray(Image.open(HERE/'world_edit_mask.png').convert('L'))>0
    accepted=np.asarray(Image.open(HERE/'approved_r25_material_mask.png').convert('L'))>0
    base=np.asarray(Image.open(ROOT/'assets/art/room1_pixel_unify_r22/floor_with_leaks.png').convert('RGBA'))
    approved=np.asarray(Image.open(ROOT/'assets/art/room1_floor_detail_r25/floor_candidate.png').convert('RGBA'))
    canvas=guide.copy();owner=np.zeros(edit.shape,dtype=np.uint8);coverage=np.zeros(edit.shape,bool)
    seams=[];used=[]
    selection=json.loads((HERE/'selection.json').read_text()) if (HERE/'selection.json').exists() else {}
    for idx,tile in enumerate(layout['tiles'],1):
        actual_name=selection.get(tile['name'],tile['name'])
        path=EXP/'raw'/f"{actual_name}.png"
        if only_ready and not path.exists():path=EXP/'raw'/f"{tile['name']}.png"
        if only_ready and not path.exists():continue
        raw=np.array(Image.open(path).convert('RGBA'));assert raw.shape==(256,256,4)
        x,y=tile['origin_px'];row,col=tile['row'],tile['column']
        local_edit=edit[y:y+256,x:x+256]
        assert bool((raw[:,:,3][local_edit]==255).all()),tile['name']
        # Ignore arbitrary AI pixels in the black mask when calculating seam
        # error. They never enter the final creative output.
        raw[~local_edit]=guide[y:y+256,x:x+256][~local_edit]
        old=canvas[y:y+256,x:x+256].copy();take=np.ones((256,256),bool)
        covered=coverage[y:y+256,x:x+256]
        for side in ['left','top']:
            if side=='left' and col:
                overlap=layout['overlap_x']
                if not covered[:,:overlap].all():continue
                error=np.sum((old[:,:overlap,:3].astype(float)-raw[:,:overlap,:3])**2,axis=2)
                cut=minimum_cut(error)
                for py,px in enumerate(cut):take[py,:px]=False
            elif side=='top' and row:
                overlap=layout['overlap_y']
                if not covered[:overlap,:].all():continue
                error=np.sum((old[:overlap,:,:3].astype(float)-raw[:overlap,:,:3])**2,axis=2)
                cut=minimum_cut(error.T)
                for px,py in enumerate(cut):take[:py,px]=False
            else:continue
            seams.append({'tile':tile['name'],'side':side,'native_overlap':overlap,'cut':cut.tolist(),'mean_overlap_rgb_error':float(error.mean())})
        dest=canvas[y:y+256,x:x+256];dest[take]=raw[take]
        ids=owner[y:y+256,x:x+256];ids[take]=idx
        coverage[y:y+256,x:x+256]=True;used.append(tile['name'])
    final=base.copy();actual=edit&coverage
    final[actual]=canvas[actual];final[accepted]=approved[accepted]
    owner[~actual]=0;owner[accepted]=255
    if only_ready:
        Image.fromarray(final).save(HERE/'pilot_composite.png')
        return
    assert coverage.all() and len(used)==len(layout['tiles'])
    assert (owner[edit]>0).all()
    reintegrated=np.asarray(Image.open(EXP/'raw/c_reintegrate.png').convert('RGBA'))
    local=np.asarray(Image.open(HERE/'mask_c_reintegrate.png').convert('L'))>0
    dest=final[96:352,168:424];dest[local]=reintegrated[local]
    owner[~actual]=0;owner[accepted]=100
    actual=edit|accepted
    layer=np.zeros_like(final);layer[actual]=final[actual];layer[:,:,3]=np.where(actual,255,0)
    (HERE/'layers').mkdir(exist_ok=True)
    hidden=np.zeros_like(base);hidden[~actual]=base[~actual]
    Image.fromarray(hidden).save(HERE/'layers/base_current_hidden.png')
    Image.fromarray(layer).save(HERE/'layers/new_native_PixelLab_material.png')
    Image.fromarray(owner).save(HERE/'pixel_source_ids.png')
    out=ROOT/'assets/art/room1_floor_detail_full_r26';out.mkdir(parents=True,exist_ok=True)
    Image.fromarray(final).save(out/'floor_with_leaks.png');(out/'.gitignore').write_text('*.import\n',encoding='utf8')
    counts={t['name']:int((owner==i).sum()) for i,t in enumerate(layout['tiles'],1)}
    assert all(n>0 for n in counts.values()),counts
    repair_counts={'c_reintegrate':int((owner==100).sum())}
    assert repair_counts['c_reintegrate']==int(accepted.sum())
    report={'native_canvas':[1648,728],'native_scale':1,'new_independent_originals':len(used),'source_selection':selection,'source_pixel_counts':counts,'reintegrated_C_area_pixels':repair_counts,'old_C_pixels_reused':0,'current_hidden_pixels':int((owner==0).sum()),'seams':seams,'no_resampling':True,'no_material_painting':True,'opaque_binary_layers':True,'output_sha256':hashlib.sha256((out/'floor_with_leaks.png').read_bytes()).hexdigest()}
    (HERE/'assembly.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('R26_COMPOSED',len(used),'world-aligned independent originals; all unoccupied floor material comes from selected native PixelLab outputs')

if __name__=='__main__':
    import sys
    build('--pilot' in sys.argv)
