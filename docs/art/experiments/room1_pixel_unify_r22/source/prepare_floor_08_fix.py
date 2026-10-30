"""Reject white missing-material output and request a complete PixelLab redraw."""
from pathlib import Path
import json,shutil
HERE=Path(__file__).resolve().parent
for stem in ['guide','mask','guide_full','mask_full']:shutil.copyfile(HERE/f'{stem}_floor_tile_08.png',HERE/f'{stem}_floor_08_fix.png')
prompt='Flat TOP-DOWN ALBEDO of continuous opaque MATTE BLUE-GRAY mineral flooring. Repaint the editable material while preserving exact occupied areas from the original project guide. Every generated pixel must be floor, with muted cool blue-gray colors close to #4D626B #526771 #566B74 #5A6C73 #5E727B #627780 #687D85 #70858D. There is no white surface, empty background, transparent area, pale fog, snow, chalk, light or highlight anywhere in this texture. Cover the entire editable area with actual blue-gray floor material. Keep coherent small connected pixel clusters, restrained broad coating differences, old contact film tightly attached to existing footprints and perimeter. Preserve existing localized cool residue sites, never create new puddles. No white/pale patches or borders, brickwork, tile seams, grid, routes, scratches, text, objects, perspective, cast shadows, glow, gloss, gradients, yellow, green, brown or rust. Keep broad regions quiet and intact. Native pixel art, consistent modest contrast and uniform mineral material family. Do not leave any blank or white area.'
(HERE/'prompt_floor_08_fix.txt').write_text(prompt,encoding='utf-8')
jobs=json.loads((HERE/'requests.json').read_text())
if not any(j['name']=='floor_08_fix' for j in jobs):
    job=dict(next(j for j in jobs if j['name']=='floor_tile_08'));job.update(name='floor_08_fix',guide='guide_floor_08_fix.png',mask='mask_floor_08_fix.png',prompt='prompt_floor_08_fix.txt',seed=2026103212);jobs.append(job)
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
rejected=json.loads((HERE/'rejected_outputs.json').read_text());rejected['floor_tile_08']={'reason':'Extensive white missing-material/paint-like output instead of blue-gray floor; rejected before runtime','raw_preserved':'raw/floor_tile_08.png','replacement_request':'floor_08_fix','manual_painting_used':False}
(HERE/'rejected_outputs.json').write_text(json.dumps(rejected,indent=2),encoding='utf-8')
print('R22_FLOOR_08_FIX_PREPARED')
