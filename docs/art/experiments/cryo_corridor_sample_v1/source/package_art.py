"""Package untouched native PixelLab results, plus layered OpenRaster sources."""
from pathlib import Path
import shutil,zipfile,json,hashlib
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
DEST=ROOT/'assets/art/cryo_corridor_sample_v1';DEST.mkdir(parents=True,exist_ok=True)
report=[]
for name,rawname,expected in [('wall','wall',(256,256)),('floor','floor_256',(256,192))]:
 raw=EXP/'raw'/f'{rawname}.png';im=Image.open(raw);assert im.size==expected
 shutil.copy2(raw,DEST/f'{name}.png')
 # OpenRaster is an editable, named source layer; no painting/retouch is applied.
 with zipfile.ZipFile(EXP/'editable'/f'{name}.ora','w') as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  z.writestr('stack.xml',f'<image version="0.0.3" w="{im.width}" h="{im.height}" name="{name}"><stack><layer name="PixelLab original - unchanged" src="data/layer0.png" opacity="1.0" visibility="visible" composite-op="svg:src-over" x="0" y="0"/></stack></image>')
  z.write(raw,'data/layer0.png');z.write(raw,'mergedimage.png')
 colors=len(im.convert('RGB').getcolors(im.width*im.height))
 report.append({'name':name,'source':str(raw.relative_to(ROOT)),'native_size':list(im.size),'sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'resampled':False,'retouched':False,'unique_colors':colors,'art_status':'rejected: flat placeholder only' if colors==1 else 'candidate pending user review','editable':'OpenRaster, original-only layer; no Aseprite edits'})
(HERE/'art_validation.json').write_text(json.dumps(report,indent=2))
print('Native art packaged without resampling or paint changes')
