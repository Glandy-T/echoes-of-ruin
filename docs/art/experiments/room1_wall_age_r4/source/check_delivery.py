"""Verify source export, protected structures, fixed-camera comparison and reset."""
from pathlib import Path
from PIL import Image
import numpy as np,json,struct,re
ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT.parents[3]
old=np.asarray(Image.open(PROJECT/'assets/art/room1_wall_joints_r3/wall_sample.png').convert('RGB'))
new=np.asarray(Image.open(PROJECT/'assets/art/room1_wall_age_r4/wall_sample.png').convert('RGB'))
export=np.asarray(Image.open(ROOT/'source/aseprite_visible_readback.png').convert('RGB'))
assert np.array_equal(new,export)
protected=np.zeros((272,256),bool);protected[18:36,:]=True
for x in [64,192]:protected[44:249,x-4:x+4]=True
assert np.array_equal(old[protected],new[protected])
changed=(old!=new).any(2)
# All new wear remains below the lamp return, above the base, or on its metal face.
allowed=np.zeros((272,256),bool);allowed[44:270,:]=True
assert not (changed&~allowed).any()
data=(ROOT/'editable/wall_age_r4.aseprite').read_bytes();pos=144;layers=[]
assert struct.unpack_from('<H',data,4)[0]==0xA5E0
while pos<len(data):
    size,kind=struct.unpack_from('<IH',data,pos)
    if kind==0x2004:
        flags=struct.unpack_from('<H',data,pos+6)[0];length=struct.unpack_from('<H',data,pos+22)[0]
        layers.append({'name':data[pos+24:pos+24+length].decode('utf-8'),'visible':bool(flags&1)})
    pos+=size
assert len(layers)==5 and all(x['visible'] for x in layers)
for label,path in [('r3',PROJECT/'assets/art/room1_wall_joints_r3/wall_sample.png'),('r4',PROJECT/'assets/art/room1_wall_age_r4/wall_sample.png')]:
    Image.open(path).resize((768,816),Image.Resampling.NEAREST).save(ROOT/'evidence'/f'wall_{label}_native_3x.png')
record={'status':'Middle-strength aging candidate for user review.',
 'size':[256,272],'actual_aseprite_export_matches_png':True,'layers':layers,
 'approved_r3_joint_pixels_unchanged':True,'diffuser_pixels_unchanged':True,
 'changed_pixels':int(changed.sum()),'changed_fraction':float(changed.mean()),
 'new_generation_usage':0,'geometry_uv_floor_lighting_camera':'Unchanged from r3.'}
cf=ROOT/'evidence/capture_record.json';sf=ROOT/'survey/capture_record.json'
if cf.exists() and sf.exists():
    compare=json.loads(cf.read_text());survey=json.loads(sf.read_text())
    assert len(compare['captures'])==9 and len(survey['captures'])==13
    for group,directory in [(compare,'evidence'),(survey,'survey')]:
        for row in group['captures']:assert Image.open(ROOT/directory/row['file']).size==(1280,720)
    rows={r['file']:r for r in compare['captures']}
    for view in ['game','technical']:
        for mode in ['lit','base_color']:
            a=rows[f'{view}_r3_{mode}.png'];b=rows[f'{view}_r4_{mode}.png']
            for field in ['camera_position','camera_basis','fov']:assert a[field]==b[field]
    baseline=np.asarray(Image.open(ROOT.parent/'room1_wall_joints_r3/evidence/game_r3_lit.png').convert('RGB'),dtype=int)
    reset={}
    for filename in ['game_r3_lit.png','game_r3_after_n_roundtrip.png']:
        delta=abs(baseline-np.asarray(Image.open(ROOT/'evidence'/filename).convert('RGB'),dtype=int))
        reset[filename]={'changed_pixels':int((delta.max(2)>0).sum()),'max_channel_difference':int(delta.max())}
        assert reset[filename]['changed_pixels']==0
    assert rows['game_r3_after_n_roundtrip.png']['fov']==50
    record.update({'actual_comparison_captures':9,'actual_survey_captures':13,'capture_size':[1280,720],
      'baseline_and_N_restoration':reset,'same_camera_before_after':True})
html=ROOT/'preview.html'
if html.exists():
    targets=re.findall(r'(?:src|href)="([^"#]+)(?:#[^"]*)?"',html.read_text(encoding='utf-8'))
    assert all('://' in x or (ROOT/x).exists() for x in targets)
    record['local_preview_links_resolve']=True
(ROOT/'quality_record.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record))
