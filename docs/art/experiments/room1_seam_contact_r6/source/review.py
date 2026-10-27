from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
import numpy as np,json,hashlib
ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT.parents[3]
OLD=PROJECT/'assets/art/room1_surface_full_r5';NEW=PROJECT/'assets/art/room1_seam_contact_r6'
checks={};joint_count=0
for name in ['left','right','front','rear']:
    old=Image.open(OLD/f'wall_{name}.png').convert('RGBA');new=Image.open(NEW/f'wall_{name}.png').convert('RGBA')
    read=Image.open(ROOT/f'source/readback/wall_{name}.png').convert('RGBA');assert ImageChops.difference(new,read).getbbox() is None
    a,b=np.array(old),np.array(new);changed=np.any(a!=b,axis=2);allowed=np.zeros(changed.shape,dtype=bool)
    film=np.array(Image.open(ROOT/f'source/wall_layers/{name}_joint_seal_film.png'))
    old_film=np.array(Image.open(PROJECT/f'docs/art/experiments/room1_surface_full_r5/source/wall_layers/{name}_joint_seal_film.png'))
    for x in range(48,new.width,128):
        joint_count+=1;allowed[44:249,x-4:x+4]=True
        assert np.array_equal(a[44:249,x-1:x+1],b[44:249,x-1:x+1])
        for y in range(44,249):
            if old_film[y,x-5,3]>0:assert film[y,x-2,3]>0
            if old_film[y,x+4,3]>0:assert film[y,x+1,3]>0
    assert not np.any(changed & ~allowed)
    assert np.array_equal(a[18:36],b[18:36])
    checks[name]={'changed_pixels':int(changed.sum()),'changes_only_in_seam_shoulders':True,'two_pixel_seal_core_exact':True,'old_film_reaches_core_neighbor':True,'diffuser_exact':True,'aseprite_reopen_exact':True,'sha256':hashlib.sha256((NEW/f'wall_{name}.png').read_bytes()).hexdigest()}
for station in ['left','center','right']:
    a=Image.open(ROOT/f'evidence/game_{station}_r5.png').convert('RGB');b=Image.open(ROOT/f'evidence/independent_r5_{station}.png').convert('RGB')
    assert ImageChops.difference(a,b).getbbox() is None
assert ImageChops.difference(Image.open(ROOT/'evidence/game_right_r6.png'),Image.open(ROOT/'evidence/game_right_after_n.png')).getbbox() is None
checks['runtime']={'r5_baselines_exact':True,'r6_n_roundtrip_exact':True,'size':[1280,720],'seams_checked':joint_count,'new_gi_bake':False}
(ROOT/'source/quality_check.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
# Nearest-neighbor diagnostic crop, not a new runtime image.
crop=Image.new('RGB',(560,584),'#171D21');d=ImageDraw.Draw(crop)
for i,folder in enumerate([OLD,NEW]):
    d.text((i*280+10,8),'R5 CLEAN GAP' if i==0 else 'R6 EDGE CONTACT',fill='#E7E7D4')
    cut=Image.open(folder/'wall_right.png').convert('RGB').crop((32,70,67,139)).resize((280,552),Image.Resampling.NEAREST);crop.paste(cut,(i*280,32))
crop.save(ROOT/'evidence/seam_pixels_before_after.png')
fig=lambda p,t:f'<figure><a href="{p}"><img src="{p}"></a><figcaption>{t}</figcaption></figure>'
s=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Room 1 接缝接触修正 r6</title><style>body{background:#171D21;color:#D9DDD5;font:16px/1.7 system-ui;max-width:1450px;margin:auto;padding:30px}a{color:#B3D9DE}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}img{max-width:100%;display:block}figure{margin:0 0 20px}figcaption{padding:8px}</style><h1>接缝旧化接触修正 · r6</h1><p>原因：旧图保护了整条8px接缝，连亮倒角也被清空旧化，形成干净隔离边。现只保护中央2px密封芯，旧化连接到相邻肩部。全室38条接缝统一处理；接缝以外像素、地坪、舱体、模型、UV和灯光保持。</p><p><a href="README.md">制作与验证说明</a> · <a href="source/quality_check.json">逐像素检查</a> · <a href="editable/">四墙分层Aseprite</a></p>',fig('evidence/seam_pixels_before_after.png','原生贴图最近邻放大：左r5／右r6，旧化不再隔着亮边悬浮。')]
for station in ['right','left','center']:
    s.append('<h2>'+station+' · 同机位原照明</h2><div class="grid">')
    for version in ['r5','r6']:s.append(fig(f'evidence/game_{station}_{version}.png',version))
    s.append('</div>')
s.append('<h2>前墙／转角技术检查</h2><p>前墙仅在技术图中临时解除剖切隐藏，拍后恢复；游戏截图保持原剖切。</p><div class="grid">')
for name in ['front_wall','corner_front_left','corner_rear_right']:s.append(fig('evidence/'+name+'.png',name))
s.append('</div><p>正常游戏图不提亮，新固有色反射未重新烘焙。旧r5全部保留。</p></html>')
(ROOT/'preview.html').write_text('\n'.join(s),encoding='utf-8');print(json.dumps(checks,indent=2))
