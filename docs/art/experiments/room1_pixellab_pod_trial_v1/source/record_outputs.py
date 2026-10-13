"""Record raw image file properties and generation observations, not visual acceptance."""
from pathlib import Path
import json, hashlib
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
record_path = ROOT/'source/generation_record.json'
record = json.loads(record_path.read_text(encoding='utf-8'))
record['status'] = 'Two completed web edits; raw downloads preserved; awaiting user visual review'
record['final_generation_usage_observed'] = '19 / 2000'
record['verified_consumption'] = 19
record['upload_succeeded'] = True
record['download_note'] = 'Flash output saved in Downloads with a temporary filename; fully decoded as 128x256 RGBA PNG and copied byte-for-byte into the artifact directory'
record['requests'] = [
    {'model':'Pro', 'ui_cost':10, 'file':'lid_edit01_rejected.png',
     'input':'lid_planar_color_GUIDE.png', 'prompt':record['prompt'],
     'observation':'Broad color bands retained, but unwanted seams and fastener-like dots invented; rejected'},
    {'model':'Pro Flash BETA', 'ui_cost':9, 'file':'lid_edit02.png',
     'input':'lid_planar_color_GUIDE.png',
     'observation':'Broad color bands retained; no first-output seams/fasteners observed; sparse gray clusters still read as arbitrary flecks rather than final surface design',
     'prompt':'Edit this abstract color swatch very minimally. Keep the exact image size and all existing flat color bands and the bottom gray rectangle in exactly the same positions. Inside those same colors add ONLY a few small low-contrast hard-edged pixel clusters. The large ivory central band must remain one continuous blank unbroken painted surface. Absolutely no horizontal or vertical drawn lines, no outlines, rectangles, seams, edges, fasteners, bolts, screws, grooves, vents, text or symbols. Do not depict manufactured panels, any object, pod, wall, metal plate or machinery. Preserve the image as abstract flat colors. No lighting, gradients or shadows. All pixels opaque.'}
]
inventory = []
for file in sorted((ROOT/'textures').glob('*.png')):
    im = Image.open(file).convert('RGBA')
    inventory.append({'file':file.name,'size':list(im.size),
                      'rgba_colors':len(set(im.getdata())),
                      'alpha_range':list(im.getchannel('A').getextrema()),
                      'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
(ROOT/'source/image_inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
record_path.write_text(json.dumps(record,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(inventory))
