from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
checks={}
def check(k,v):checks[k]=bool(v);assert v,k
base=np.asarray(Image.open(ROOT/'assets/art/room1_pixel_unify_r22/floor_with_leaks.png').convert('RGBA'))
final=np.asarray(Image.open(ROOT/'assets/art/room1_floor_detail_full_r26/floor_with_leaks.png').convert('RGBA'))
readback=np.asarray(Image.open(HERE/'readback_floor.png').convert('RGBA'))
approved=np.asarray(Image.open(ROOT/'assets/art/room1_floor_detail_r25/floor_candidate.png').convert('RGBA'))
edit=np.asarray(Image.open(HERE/'world_edit_mask.png').convert('L'))>0
keep=np.asarray(Image.open(HERE/'approved_r25_material_mask.png').convert('L'))>0
occupied=np.asarray(Image.open(HERE/'occupied_mask.png').convert('L'))>0
ids=np.asarray(Image.open(HERE/'pixel_source_ids.png'))
check('native canvas1648x728',final.shape==(728,1648,4))
check('ASE exact readback',np.array_equal(final,readback))
check('opaque',bool((final[:,:,3]==255).all()))
c_raw=np.asarray(Image.open(EXP/'raw/c_reintegrate.png').convert('RGBA'));c_mask=np.asarray(Image.open(HERE/'mask_c_reintegrate.png').convert('L'))>0
check('C area exact new PixelLab native pixels',np.array_equal(final[96:352,168:424][c_mask],c_raw[c_mask]))
check('current occupied hidden floor exact',np.array_equal(final[occupied],base[occupied]))
check('no protected material conflicts',not bool((occupied&keep).any()))
check('new world plus reintegrated C covers every unoccupied floor pixel',bool((edit|keep|occupied).all()))
check('no old layer exposed in new material',bool((ids[edit]>0).all()) and not bool((ids[edit]==255).any()))
layout=json.loads((HERE/'tile_layout.json').read_text())
selection=json.loads((HERE/'selection.json').read_text())
for index,tile in enumerate(layout['tiles'],1):
    actual=selection.get(tile['name'],tile['name'])
    x,y=tile['origin_px'];raw=np.asarray(Image.open(EXP/'raw'/f'{actual}.png').convert('RGBA'))
    pick=ids[y:y+256,x:x+256]==index
    check('actually used '+tile['name'],bool(pick.any()))
    check('exact raw native pixels '+tile['name'],np.array_equal(final[y:y+256,x:x+256][pick],raw[pick]))
    check('native256 '+tile['name'],raw.shape==(256,256,4))
    mask=np.asarray(Image.open(HERE/f"mask_{tile['name']}.png").convert('L'))>0
    check('world mask consistent '+tile['name'],np.array_equal(mask,edit[y:y+256,x:x+256]))
    check('selected raw pixels are editable '+tile['name'],bool(mask[pick].all()))
    result=json.loads((EXP/f'result_{actual}.json').read_text())
    check('actual completed API '+tile['name'],result['status']=='completed' and result['native_size']==[256,256])
check('C reintegration source id exact',bool((ids[keep]==100).all()))
check('C source used only in original sample material area',np.array_equal(ids==100,keep))
check('all new pixel sources accounted',set(np.unique(ids[edit|keep])).issubset(set(range(1,22))|{100}))
check('no rejected join layer used',not any((ids==i).any() for i in [101,102,103,255]))
baseline=json.loads((HERE/'baseline_file_hashes.json').read_text())
for p,sha in baseline.items():check('immutable '+p,hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha)
optional=json.loads((HERE/'optional_local_legacy_hashes.json').read_text());optional_skipped=[]
for p,sha in optional.items():
    if (ROOT/p).exists():check('local legacy unchanged '+p,hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha)
    else:optional_skipped.append(p)
assembly=json.loads((HERE/'assembly.json').read_text())
check('final hash',hashlib.sha256((ROOT/'assets/art/room1_floor_detail_full_r26/floor_with_leaks.png').read_bytes()).hexdigest()==assembly['output_sha256'])
results=[json.loads(p.read_text()) for p in EXP.glob('result_*.json')]
report={'result':'PASS','checks':checks,'immutable_portable_files':len(baseline),'optional_local_legacy_files_absent':optional_skipped,'legacy_note':'Two original standalone v8 raw irradiance caches are not tracked/delivered or needed by current r26. Preserve them if present; do not require them on school checkout.','native_world_canvas':[1648,728],'new_independent_material_originals':len(layout['tiles']),'C_area_reintegration_originals':1,'actual_successful_requests':len(results),'generations_used':sum(r['usage']['generations'] for r in results),'C_area_new_PixelLab_pixels':int(keep.sum()),'old_C_material_reused':False,'new_material_pixels':int((edit|keep).sum()),'resampling':False,'manual_or_procedural_material_art':False,'user_art_approval':False}
(HERE/'artifact_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('R26_ARTIFACTS_PASS',len(checks),'checks,',report['generations_used'],'actual generations')
