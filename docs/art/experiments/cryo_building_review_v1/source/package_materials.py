"""Pack native PixelLab images and documented inherited crops into editable masters.
Structural restoration uses the exact guide. No image synthesis or invented ageing.
"""
from pathlib import Path
from PIL import Image, ImageChops
from collections import Counter
import argparse, hashlib, json, shutil, subprocess

S=Path(__file__).resolve().parent; E=S.parent; R=S.parents[4]
A=R/'assets/art/cryo_building_review_v1/textures'; RAW=E/'raw'; ED=E/'editable'; EV=E/'evidence/materials'; PACK=S/'layers'
for p in (A,RAW,ED,EV,PACK): p.mkdir(parents=True,exist_ok=True)
REPLACED={'M05-L','M05-D','M06-01','M06-02','M06-03','M06-J','M06-R','M07'}
# Remove named defects only. Donors are different accepted working PixelLab maps
# at their own native resolution. These are local masks, not generated stains.
LOCAL={
 'EL-A':('M05-D-R1',[(4,0,15,13,'all'),(65,1,81,14,'all'),(45,170,66,192,'all'),(12,54,49,145,'dark'),(67,53,111,144,'dark')]),
 'EL-B':('M05-D-R1',[(7,53,49,149,'dark'),(59,53,111,145,'dark')]),
 'EN-B':('M05-D-R1',[(16,57,55,141,'dark'),(83,56,121,141,'dark')]),
 'M06-J':('M06-01-R1',[(115,54,177,149,'dark'),(182,53,242,143,'dark')]),
 'M06-R':('M06-01-R1',[(28,55,76,143,'dark'),(78,55,112,142,'dark')])}
def hash(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def source_copy(name,rel,region=None):
    src=R/rel; i=Image.open(src).convert('RGBA'); i=i.crop(region) if region else i
    dest=A/f'{name}.png'; i.save(dest)
    return {'material':name,'source':rel,'source_sha256':hash(src),'crop':region,'size':list(i.size),'export':dest.name,'status':'inherited_original_native_pixels'}

def inherited():
    base='assets/art/cryo_stair_material_sample_v1/'
    wall='assets/art/room1_wall_detail_full_r24/wall_rear.png'
    door='assets/art/room1_door_window_r30/door_front.png'
    return [source_copy('M01',base+'wall_body.png'),source_copy('M02','assets/art/cryo_corridor_baked_v2/corridor_baked_v2_floor.png'),source_copy('M03',base+'mineral_a.png'),
        source_copy('M08',door,(0,0,4,184)),source_copy('M09',wall,(128,12,384,17)),source_copy('M10',base+'tread_edge.png')]

def generated(row, aseprite):
    id, mat=row['name'],row['material']; chosen=id+'-R1' if id in REPLACED else id; raw=RAW/f'{chosen}.png'; j=S/'jobs'/id
    if not raw.exists(): return {'material':mat,'status':'missing_no_usable_PixelLab_return'}
    out=Image.open(raw).convert('RGBA'); expected=tuple(row['native_size']); size=out.size
    if size==tuple(row['input_size']) and size!=expected: out=out.crop(row['export_crop'])
    if out.size!=expected: return {'material':mat,'status':'rejected_wrong_native_dimensions','size':list(size),'expected':expected}
    if out.getchannel('A').getextrema()!=(255,255): return {'material':mat,'status':'rejected_unexpected_transparency','size':list(size)}
    mask=Image.open(j/'edit_mask.png').convert('L'); guide=Image.open(j/'guide.png').convert('RGBA')
    out.putalpha(mask)
    protected=Image.new('RGBA',expected,(0,0,0,0)); protected.paste(guide,(0,0),ImageChops.invert(mask))
    dest=A/f'{mat}.png'; composed=Image.alpha_composite(guide,out)
    refin=Image.new('RGBA',expected,(0,0,0,0)); changed=0; donor=None
    if id in LOCAL:
        donor,boxes=LOCAL[id];copy=Image.open(RAW/f'{donor}.png').convert('RGBA');assert copy.size==(256,256)
        for x0,y0,x1,y1,kind in boxes:
            for y in range(y0,min(y1,expected[1])):
                for x in range(x0,min(x1,expected[0])):
                    src=composed.getpixel((x,y));
                    lum=(src[0]*2+src[1]*3+src[2])/6
                    limit=169 if id.startswith('M06') else 77
                    if mask.getpixel((x,y)) and (kind=='all' or lum<limit):
                        refin.putpixel((x,y),copy.getpixel(((x+29)%256,(y+67)%256)))
                        changed+=1
    composed=Image.alpha_composite(composed,refin)
    d=PACK/id; d.mkdir(exist_ok=True); guide.save(d/'base.png'); out.save(d/'ai.png'); protected.save(d/'protected.png');refin.save(d/'local.png')
    output=ED/f'{mat}.aseprite'; readback=d/'readback.png'
    subprocess.run([aseprite,'-b','--script-param',f'layer_dir={d}','--script-param',f'output={output}','--script',str(S/'package_material.lua')],check=True,timeout=35)
    assert ImageChops.difference(composed.convert('RGB'),Image.open(readback).convert('RGB')).getbbox() is None, mat
    shutil.copy2(readback,dest)
    composed.resize((min(96,expected[0])*4,min(96,expected[1])*4),Image.Resampling.NEAREST).save(EV/f'{mat}_nearest4.png') if max(expected)<=96 else composed.crop((max(0,expected[0]//2-48),0,min(expected[0],expected[0]//2+48),min(96,expected[1]))).resize((min(96,expected[0])*4,min(96,expected[1])*4),Image.Resampling.NEAREST).save(EV/f'{mat}_nearest4.png')
    n=len(Counter(composed.get_flattened_data()))
    return {'material':mat,'status':'packaged_native_pending_visual_review','size':list(expected),'raw_size':list(size),'selected_raw':chosen+'.png','unique_colors':n,'raw_sha256':hash(raw),'export_sha256':hash(dest),'editor_readback_exact':True,'protected_pixels_restored':list(mask.get_flattened_data()).count(0),'local_cleanup_pixels':changed,'local_cleanup_donor':donor,'local_cleanup_regions':LOCAL[id][1] if donor else [],'notes':'Exact geometry restoration and bounded local cleanup only; donor pixels are other native PixelLab work, not synthesized. No scaling of runtime map.'}

if __name__=='__main__':
    arg=argparse.ArgumentParser();arg.add_argument('--inherit-only',action='store_true');arg.add_argument('--aseprite',default='C:/文件类/Aseprite/Aseprite/aseprite.exe'); ns=arg.parse_args()
    rows=inherited()
    if not ns.inherit_only:
        rows += [generated(row,ns.aseprite) for row in json.loads((S/'requests.json').read_text(encoding='utf-8'))]
    dump(S/'material_packaging.json',rows)
    print('Material packaging:',len(rows),'records',sum(x['status']=='packaged_native_pending_visual_review' for x in rows),'new')
