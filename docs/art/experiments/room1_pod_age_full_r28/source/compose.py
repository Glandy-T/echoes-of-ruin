"""Register native AI pixels, then transfer exact functional numbers. No painted aging."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,shutil,hashlib,re,ast
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4];R27=ROOT/'docs/art/experiments/room1_pod_age_r27';TARGET=ROOT/'assets/art/room1_pod_age_full_r28'
ROLES=['lid','shell_side','shell_end'];records=[]
for v in 'abcd':
 (TARGET/f'variant_{v}').mkdir(parents=True,exist_ok=True);(HERE/'layers'/f'variant_{v}').mkdir(parents=True,exist_ok=True)
 for role in ROLES:
  if v=='d' and role=='shell_end':continue
  base=Image.open(R27/'source'/f'guide_{role}.png').convert('RGBA');identity=Image.open(R27/'source'/f'identity_{role}.png').convert('RGBA');mask=Image.open(R27/'source'/f'mask_{role}.png').convert('L')
  if v=='a':
   raw=Image.open(R27/'source/layers'/f'{role}_PixelLab.png').convert('RGBA');final=Image.open(ROOT/'assets/art/room1_pod_age_r27'/f'{role}.png').convert('RGBA')
   shutil.copy2(ROOT/'assets/art/room1_pod_age_r27'/f'{role}.png',TARGET/f'variant_{v}'/f'{role}.png')
  else:
   raw_name=f'{v}_{role}'
   raw=Image.open(EXP/'raw'/f'{raw_name}.png').convert('RGBA');assert raw.size==base.size
   final=Image.alpha_composite(Image.composite(raw,base,mask),identity);final.save(TARGET/f'variant_{v}'/f'{role}.png')
   a=np.asarray(raw).copy();a[:,:,3]=np.asarray(mask);raw=Image.fromarray(a)
  base.save(HERE/'layers'/f'variant_{v}'/f'{role}_base.png');raw.save(HERE/'layers'/f'variant_{v}'/f'{role}_PixelLab.png');identity.save(HERE/'layers'/f'variant_{v}'/f'{role}_identity.png')
  protected=np.asarray(mask)==0;assert np.array_equal(np.asarray(final)[protected],np.asarray(base)[protected])
  records.append({'variant':v,'role':role,'native_size':list(final.size),'original_AI':f'r27 selected {role}' if v=='a' else f'raw/{v}_{role}.png','creative_resize':False,'protected_structure_exact':True})
DIGITS=ast.literal_eval(re.search(r'const DIGITS := (\[.*?\])',(ROOT/'scripts/props/cryopod_material_variants_r16.gd').read_text(encoding='utf8')).group(1))
PLATES={'lid':(47,197,33,14),'shell_end':(55,35,18,14)};START={'lid':(55,198),'shell_end':(57,37)}
def numbering(role,number,size):
 oldsize=(128,256) if role=='lid' else (128,80);im=Image.new('RGBA',oldsize);d=ImageDraw.Draw(im);x,y,w,h=PLATES[role]
 d.rectangle((x,y,x+w-1,y+h-1),fill=(190,199,194,255));sx,sy=START[role]
 for k,char in enumerate(f'{number:02d}'):
  pat=DIGITS[int(char)]
  for row in range(5):
   for col in range(3):
    if pat[row*3+col]=='1':d.rectangle((sx+k*8+col*2,sy+row*2,sx+k*8+col*2+1,sy+row*2+1),fill=(34,51,64,255))
 return im.resize(size,Image.Resampling.NEAREST)
(TARGET/'numbered').mkdir(exist_ok=True);(HERE/'number_layers').mkdir(exist_ok=True)
layout=json.loads((TARGET/'layout_variants.json').read_text());numbers=[]
for p in layout['pods']:
 for role,variant_key in [('lid','lid_variant'),('shell_end','end_variant')]:
  src=TARGET/f"variant_{p[variant_key]}"/f'{role}.png';base=Image.open(src).convert('RGBA')
  if p['id']=='P12':
   final=base;layer=Image.open(R27/'source'/f'identity_{role}.png').convert('RGBA')
  else:
   layer=numbering(role,p['number'],base.size);final=Image.alpha_composite(base,layer)
  assert np.array_equal(np.asarray(final)[np.asarray(layer)[:,:,3]==0],np.asarray(base)[np.asarray(layer)[:,:,3]==0])
  dest=TARGET/'numbered'/f"{p['id']}_{role}.png";final.save(dest);layer.save(HERE/'number_layers'/f"{p['id']}_{role}.png")
  if p['id']=='P12':assert dest.read_bytes()==(ROOT/'assets/art/room1_pod_age_r27'/f'{role}.png').read_bytes()
  numbers.append({'id':p['id'],'number':p['number'],'role':role,'variant':p[variant_key],'output':dest.relative_to(ROOT).as_posix(),'changed_only_functional_plate':True})
(HERE/'composite_validation.json').write_text(json.dumps({'result':'PASS','variant_surfaces':records,'numbered':numbers,'P12_exact':True,'new_AI_outputs':8,'reused_A_outputs':3,'creative_resizing':False,'procedural_aging':False},indent=2),encoding='utf8')
print('R28_COMPOSITE_PASS11variantmaps40numberedexports')
