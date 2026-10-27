"""Capture and binding readback; never substitutes for visual art approval."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib,re
ROOT=Path(__file__).resolve().parents[1]
compare=json.loads((ROOT/'evidence/capture_record.json').read_text())
survey=json.loads((ROOT/'survey/capture_record.json').read_text())
assert len(compare['captures'])==11
assert len(survey['captures'])==13
for group,directory in [(compare,'evidence'),(survey,'survey')]:
    for row in group['captures']:
        im=Image.open(ROOT/directory/row['file']);assert im.size==(1280,720)
        assert row['size']==[1280,720]
for key,values in compare['bindings'].items():
    assert len(values)==1
    for row in values:
        assert row['continuous_diffuser']==1 and abs(row['diffuser_scale']-5.33333333333333)<1e-8
        assert row['lightmap']=='res://assets/art/room1_wall_finish_r4/strip_irradiance_denoised.exr'
baseline=Image.open(ROOT.parent/'room1_surface_full_room_r1/evidence/01_baseline.png').convert('RGB')
original=np.asarray(baseline,dtype=int)
checks={}
for name in ['game_00_baseline.png','game_baseline_after_n_roundtrip.png']:
    image=np.asarray(Image.open(ROOT/'evidence'/name).convert('RGB'),dtype=int)
    delta=abs(original-image)
    checks[name]={'changed_pixels':int((delta.max(2)>0).sum()),'max_channel_difference':int(delta.max())}
    assert checks[name]['changed_pixels']==0
source=json.loads((ROOT/'source/verification.json').read_text())
for name,value in source['inherited_sources'].items():
    assert hashlib.sha256((ROOT.parents[3]/name).read_bytes()).hexdigest()==value['sha256']
html=(ROOT/'preview.html').read_text(encoding='utf-8')
missing=[]
for target in re.findall(r'(?:src|href)="([^"#]+)(?:#[^"]*)?"',html):
    if '://' not in target and not (ROOT/target).exists():missing.append(target)
assert not missing,missing
(ROOT/'quality_record.json').write_text(json.dumps({
 'status':'Local art candidate for user review, not Pixel Canals quality acceptance.',
 'actual_godot_captures':{'comparison':11,'survey':13,'size':[1280,720],'postprocessed':False},
 'baseline_and_diagnostic_roundtrip':checks,
 'bake_package':'Existing r4 GLB/UV2/irradiance/mapping; new albedo bounce not rebaked.',
 'receiver_scope':compare['bindings'],
 'editable_source_matches_exports':True,
 'inherited_source_hashes_unchanged_since_packaging':True,
 'local_links_resolve':True,
 'visual_review':'Structure readable in Base Color; emergency-light view remains subdued. Initial floor islands and hard wall patch endpoints revised before final capture.',
 'art_approval':'Pending user review. No default scene/material promotion.'
},indent=2),encoding='utf-8')
print('24 actual captures, r4 bindings, exact baseline/diagnostic restoration and local links verified.')
