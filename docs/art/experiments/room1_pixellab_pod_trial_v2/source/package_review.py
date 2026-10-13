"""Mechanical review packaging: native-pixel enlargement and file inventory.
No artistic filtering, repainting or AI source modification.
"""
from pathlib import Path
import json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
im=Image.open(ROOT/'evidence/06_pixel_native.png')
im.resize((1440,1000),Image.Resampling.NEAREST).save(ROOT/'evidence/07_pixel_2x.png')
records=[]
for folder in ('raw','textures','guides'):
    for path in sorted((ROOT/folder).glob('*.png')):
        im=Image.open(path).convert('RGBA')
        records.append({'file':str(path.relative_to(ROOT)).replace('\\','/'),
                        'size':list(im.size),'rgba_colors':len(set(im.getdata())),
                        'alpha_range':list(im.getchannel('A').getextrema()),
                        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(ROOT/'source/image_inventory.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print('Packaged native-pixel presentation and image inventory.')
