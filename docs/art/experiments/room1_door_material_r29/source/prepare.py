"""Owned flat structural door guide + protected native wall context. No aging painted."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
for n in ['raw','editable','evidence','source/layers']:(EXP/n).mkdir(parents=True,exist_ok=True)
(ROOT/'assets/art/room1_door_material_r29').mkdir(parents=True,exist_ok=True)
for name in ['pixellab_api.py','jobs.py']:
 (HERE/name).write_text((ROOT/'docs/art/experiments/room1_pod_age_full_r28/source'/name).read_text(encoding='utf8').replace('R28_PIXELLAB_QUEUE_COMPLETE','R29_PIXELLAB_QUEUE_COMPLETE'),encoding='utf8')
old_path=ROOT/'assets/art/room1_integrated_door_pixellab_v7/door_front.png';old=Image.open(old_path).convert('RGBA')
assert old.size==(112,184)
mask=Image.new('L',old.size,0);d=ImageDraw.Draw(mask);d.rectangle((3,3,108,180),fill=255);d.rectangle((45,61,66,74),fill=0)
flat=Image.new('RGBA',old.size,(211,214,201,255));door=Image.composite(flat,old,mask)
door.save(HERE/'door_clean_structure.png');mask.save(HERE/'door_mask.png')
wall_path=ROOT/'assets/art/room1_wall_detail_full_r24/wall_rear.png';wall=Image.open(wall_path).convert('RGBA').crop((172,56,284,240));assert wall.size==old.size
canvas=Image.new('RGBA',(256,192),(211,214,201,255));canvas.paste(door,(4,4));canvas.paste(wall,(140,4))
edit=Image.new('L',canvas.size,0);edit.paste(mask,(4,4));canvas.save(HERE/'guide_door.png');edit.save(HERE/'mask_door.png')
prompt=('Edit ONLY the LEFT door UV material inside the white mask. LEFT door is112x184 pixels at x4,y4; RIGHT is our OWN approved wall material context and is protected. '
 'Match its fine native pixel clusters, matte mineral/ceramic composite coating, related muted warm ivory and cool gray material tones. '
 'The door is a long-life flush institutional composite-coated panel, NOT stainless steel, brushed metal, chrome or silver. '
 'This is FLAT ALBEDO: remove all fake reflections, diagonal shine bands, metallic gradients and smooth directional shading. No new lighting or perspective. '
 'Create clearly readable medium aging from decades in a sealed facility: irregular connected old film at real top/side gaskets, recess contacts and lower corners, with smaller1-3 pixel broken fringes. '
 'Main face also has shallow related-tone coating changes and selected small weathered clusters, not an empty polished slab. Retain intact coating between groups. '
 'Top, sides and bottom share one detailed pixel vocabulary; no thick continuous dirty header or uniform perimeter border. '
 'Preserve the exact existing outline and tiny authentication status recess at the supplied location. Keep the single flat panel, no added inner frame, panel joints, bevel, handle, bolts, labels, screen or equipment. '
 'Door opens automatically: no handle handprints or invented touch-wear arcs. No rust, yellow/brown/green, black soot, giant peeling blocks, holes, cracks, wet streaks or pepper noise. '
 'Replace the white region completely with fresh matte material. Black mask is exact protected structure/status/reference, never redesign it. Do not copy the reference wall seam onto the door.')
assert len(prompt)<=2000;(HERE/'prompt_door.txt').write_text(prompt,encoding='utf8')
jobs=[{'name':'door','endpoint':'/inpaint-v3','prompt':'prompt_door.txt','guide':'guide_door.png','mask':'mask_door.png','seed':2026110270,'native_size':[256,192],'output_door_crop':[4,4,116,188]}]
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf8')
(HERE/'input_provenance.json').write_text(json.dumps({'original_door':old_path.relative_to(ROOT).as_posix(),'old_sha256':hashlib.sha256(old_path.read_bytes()).hexdigest(),'flat_guide_color':'#D3D6C9','removed_from_guide':['old diagonal broad light bands','old material age in white edit area'],'owned_style_context':wall_path.relative_to(ROOT).as_posix(),'wall_sha256':hashlib.sha256(wall_path.read_bytes()).hexdigest(),'wall_crop_native':[172,56,284,240],'door_native_crop':[4,4,116,188],'creative_resize':False,'third_party_AI_input':False},indent=2),encoding='utf8')
(EXP/'.gitignore').write_text('*.log\n*.log.*\n*.err\n*.blend1\n__pycache__/\nsource/balance_*.json\n',encoding='utf8')
print('R29_PREPARED1nativePixelLabrequest;estimated10generations')
