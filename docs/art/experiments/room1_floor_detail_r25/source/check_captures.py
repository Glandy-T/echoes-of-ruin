from pathlib import Path
import json, hashlib
from PIL import Image

HERE=Path(__file__).resolve().parent
EVIDENCE=HERE.parent/'evidence'
records=json.loads((EVIDENCE/'capture_record.json').read_text(encoding='utf-8'))
expected=[]
for mode in [1,2,3]:
    expected += [f'{mode}_{name}.png' for name in ['game_floor_patch_closed','floor_patch_full','p12_p13_contact_detail','floor_patch_topdown','floor_patch_unoccluded','game_floor_patch_open','base_color_floor_patch','base_color_floor_unoccluded']]
expected += ['1_restore_floor_patch.png','3_raw_floor_patch.png','3_denoised_floor_patch.png']
assert {item['file'] for item in records}==set(expected)
checks={}
for item in records:
    image=Image.open(EVIDENCE/item['file']).convert('RGB')
    nonblack=sum(max(pixel)>8 for pixel in image.getdata())
    assert image.size==(1280,720) and nonblack>20000,item['file']
    checks[item['file']]={'size':image.size,'nonblack_pixels':nonblack,'diagnostic':item['diagnostic'],'pods_hidden':item['pods_hidden']}
assert hashlib.sha256((EVIDENCE/'1_floor_patch_full.png').read_bytes()).hexdigest()==hashlib.sha256((EVIDENCE/'1_restore_floor_patch.png').read_bytes()).hexdigest()
assert (EVIDENCE/'3_raw_floor_patch.png').read_bytes() != (EVIDENCE/'3_denoised_floor_patch.png').read_bytes()
(HERE/'capture_validation.json').write_text(json.dumps({'result':'PASS','frames':len(records),'checks':checks,'scope':'A/B/C floor patch; normal game views keep pods, while unoccluded/topdown/base-color views are labelled diagnostics.'},indent=2),encoding='utf-8')
print('R25_CAPTURE_PASS',len(records))
