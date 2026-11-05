"""Native-size crop/package only. No painted pixels, noise, palette remap or resizing."""
from pathlib import Path
import json,hashlib
from PIL import Image
HERE=Path(__file__).resolve().parent
EXP=HERE.parent
ROOT=HERE.parents[4]
ASSET=ROOT/'assets/art/cryo_stair_material_sample_v1'
records=[]
for job in json.loads((HERE/'requests.json').read_text()):
    if job.get('adopted') is False:continue
    raw=EXP/'raw'/f"{job['name']}.png"
    image=Image.open(raw)
    assert image.size==(256,256)
    crop=image.crop(tuple(job['retained_crop']))
    out=ASSET/f"{job.get('output_name',job['name'])}.png"
    crop.save(out)
    if job.get('output_name')=='mineral_a':
        (HERE/'layers').mkdir(exist_ok=True)
        crop.save(HERE/'layers/mineral_a_PixelLab_native.png')
    records.append({'name':job['name'],'output_name':job.get('output_name',job['name']),'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'crop':job['retained_crop'],'export_size':list(crop.size),'native_crop_png_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'operation':'native crop; see declared Aseprite local layer and final-file verification'})
(EXP/'texture_provenance.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print('Native exports packaged.')
