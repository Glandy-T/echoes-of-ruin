"""Import exact official PixelLab download names and build a native contact sheet."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageStat
import re, hashlib, json, shutil, argparse

SRC=Path(__file__).resolve().parent; EXP=SRC.parent
ap=argparse.ArgumentParser();ap.add_argument('--downloads',type=Path,default=Path.home()/'Downloads');ns=ap.parse_args()
ids=[j['name'] for j in json.loads((SRC/'requests.json').read_text(encoding='utf-8'))]
ids += [id+'-R1' for id in ids]
items=[]; raw=EXP/'raw'; raw.mkdir(exist_ok=True)
for id in ids:
    pp=sorted(ns.downloads.glob(f'pixellab--CRYO-{id}--*.png'))
    if not pp: continue
    values={hashlib.sha256(p.read_bytes()).hexdigest() for p in pp}
    if len(values)!=1:raise RuntimeError(f'Multiple different files with same task tag: {id}')
    p=pp[0];out=raw/(id+'.png');shutil.copy2(p,out)
    im=Image.open(out).convert('RGBA');items.append({'task':id,'name':p.name,'sha256':values.pop(),'size':list(im.size),'standard_deviation':ImageStat.Stat(im).stddev,'unique_pixels':len(im.getcolors(1_000_000))})
sheet=Image.new('RGB',(5*265,((len(items)+4)//5)*287),(37,44,47)); draw=ImageDraw.Draw(sheet)
for i,r in enumerate(items):
    x=(i%5)*265;y=(i//5)*287
    draw.text((x+3,y+4),r['task'],fill='white');im=Image.open(raw/(r['task']+'.png')).convert('RGB');sheet.paste(im,(x,y+20))
ev=EXP/'evidence/materials';ev.mkdir(parents=True,exist_ok=True);sheet.save(ev/'raw_native_contact_sheet.png')
(SRC/'official_downloads.json').write_text(json.dumps(items,indent=2)+'\n',encoding='utf8')
print('Observed exact official outputs:',len(items))
