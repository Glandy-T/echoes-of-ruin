"""Package untouched native PixelLab results, plus layered OpenRaster sources."""
from pathlib import Path
import shutil,zipfile,json,hashlib
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
DEST=ROOT/'assets/art/cryo_corridor_sample_v1';DEST.mkdir(parents=True,exist_ok=True)
report=[]
for name,rawname,expected in [('wall','wall',(256,256)),('floor','floor_reused_r26',(256,192))]:
 raw=EXP/'raw'/f'{rawname}.png'
 if name=='floor':
  origin=ROOT/'assets/art/room1_floor_detail_full_r26/floor_with_leaks.png'
  Image.open(origin).crop((768,256,1024,448)).save(raw)
  (HERE/'floor_reuse_provenance.json').write_text(json.dumps({'source':origin.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(origin.read_bytes()).hexdigest(),'crop_xyxy':[768,256,1024,448],'source_region':'central aisle, between both pod rows; excludes rectangular pod footprints and leaks','native_size':[256,192],'world_size_m':[3.2,2.4],'resampled':False,'paint_changes':False,'new_generations':0},indent=2))
 im=Image.open(raw);assert im.size==expected
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
