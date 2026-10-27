"""Verify exact pixel scope, editable source export, and actual capture restoration."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib,struct
ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT.parents[3]
old=np.asarray(Image.open(PROJECT/'assets/art/room1_surface_structure_r2/wall_sample.png').convert('RGB'))
new=np.asarray(Image.open(PROJECT/'assets/art/room1_wall_joints_r3/wall_sample.png').convert('RGB'))
readback=np.asarray(Image.open(ROOT/'source/aseprite_visible_readback.png').convert('RGB'))
assert np.array_equal(new,readback)
changed=(new!=old).any(2);allowed=np.zeros(changed.shape,bool)
for x in [64,192]:allowed[44:249,x-4:x+4]=True
assert not (changed&~allowed).any()
assert np.array_equal(old[18:36],new[18:36])
data=(ROOT/'editable/wall_joints_r3.aseprite').read_bytes()
assert struct.unpack_from('<H',data,4)[0]==0xA5E0
pos=144;layers=[]
while pos<len(data):
    size,kind=struct.unpack_from('<IH',data,pos)
    if kind==0x2004:
        flags=struct.unpack_from('<H',data,pos+6)[0]
        length=struct.unpack_from('<H',data,pos+22)[0]
        layers.append({'name':data[pos+24:pos+24+length].decode('utf-8'),'visible':bool(flags&1)})
    pos+=size
assert len(layers)==4 and all(x['visible'] for x in layers)
record={'status':'User-review candidate; not project-wide wall module approval.',
 'texture_size':[256,272],'changed_pixels':int(changed.sum()),
 'outside_joint_profiles_unchanged':True,'diffuser_pixels_unchanged':True,
 'actual_aseprite_visible_export_matches_png':True,'layers':layers,
 'geometry_uv_and_lights':'Inherited r2 scene/r4 data, not edited.',
 'new_generation_usage':0}
compare_file=ROOT/'evidence/capture_record.json';survey_file=ROOT/'survey/capture_record.json'
if compare_file.exists() and survey_file.exists():
    compare=json.loads(compare_file.read_text());survey=json.loads(survey_file.read_text())
    assert len(compare['captures'])==9 and len(survey['captures'])==13
    for group,directory in [(compare,'evidence'),(survey,'survey')]:
        for row in group['captures']:assert Image.open(ROOT/directory/row['file']).size==(1280,720)
    camera_fields=['camera_position','camera_basis','fov']
    rows={row['file']:row for row in compare['captures']}
    for prefix in ['game','technical']:
        for suffix in ['lit','base_color']:
            before=rows[f'{prefix}_r2_{suffix}.png'];after=rows[f'{prefix}_r3_{suffix}.png']
            for field in camera_fields:assert before[field]==after[field]
    assert rows['game_r2_after_n_roundtrip.png']['fov']==50
    reference=np.asarray(Image.open(ROOT.parent/'room1_surface_structure_r2/evidence/game_03_both.png').convert('RGB'),dtype=int)
    roundtrips={}
    for filename in ['game_r2_lit.png','game_r2_after_n_roundtrip.png']:
        image=np.asarray(Image.open(ROOT/'evidence'/filename).convert('RGB'),dtype=int)
        delta=abs(reference-image)
        roundtrips[filename]={'changed_pixels':int((delta.max(2)>0).sum()),'max_channel_difference':int(delta.max())}
        assert roundtrips[filename]['changed_pixels']==0
    record.update({'actual_comparison_captures':len(compare['captures']),'actual_survey_captures':len(survey['captures']),
       'baseline_against_r2_and_N_roundtrip':roundtrips,'capture_size':[1280,720]})
(ROOT/'quality_record.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record))
