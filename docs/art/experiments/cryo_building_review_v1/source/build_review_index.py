"""Build matching local and GitHub review indexes from verified Godot evidence."""
from hashlib import sha256
from html import escape
import json
from pathlib import Path
from PIL import Image

base=Path(__file__).resolve().parent.parent
assets='../../../../assets/art/cryo_building_review_v1'
cap='evidence/godot'
def read(name):
    return json.loads((base/name).read_text(encoding='utf8'))
def write(name,content):
    (base/name).write_text(content.rstrip()+'\n',encoding='utf8')

pairs=[
 ('HR 扶手',('HR-A','连续圆管＋细竖杆'),('HR-B','折板＋独立握持轨'),'rail',
  [('occupied','感应增亮'),('baseline','保底光'),('side','下段'),('upper','上段'),('neutral','中性检查')]),
 ('FD 楼梯分区门',('FD-A','等宽双扇'),('FD-B','65/35＋窄侧检修带'),'closed',
  [('rear','室内侧'),('release','机械释放'),('open90','打开 90°'),('sweep','独立样段扫掠')]),
 ('EL 电梯入口',('EL-A','两片中分'),('EL-B','三片侧收套叠'),'caution',
  [('closed','断电无警示'),('touch','熄灭的操作件'),('pass','穿过警示、停在门外')]),
 ('EN 首层人员出口',('EN-A','矿物门套，无雨棚'),('EN-B','折板门套，浅雨檐'),'transition',
  [('closed','室外闭合'),('rear','室内侧'),('release','机械释放'),('open90','打开 90°'),('sweep','开扇扫掠')]),
 ('FA 建筑外壳',('FA-A','水平矿物板带'),('FA-B','层高竖板＋金属节点'),'overall',
  [('north','北'),('south','南'),('east','东'),('west','西'),('detail10m','10 m 片段'),('corner','转角'),('node','交通节点'),('ground','首层'),('roof','屋顶'),('b4','B4–B1 技术图')]),
]
limits=[
    'HR-A/B：扶手内缘净宽约 1.62 m，未达到冻结的 1.80 m；均是独立样段，暂不安装。',
    'FD-A/B：已核对独立样段的开合与碰撞，冻结楼梯平台上的整扇扫掠仍须在安装前验证。',
    'EL-A/B：均断电关闭；可穿过的 CAUTION 是显示层，门叶有碰撞。没有新增电梯功能。',
    'EN-A/B：均为 ASSET ONLY，首层外门没有确认的锚点。现有内核 D089–D096 是 2.4 m 旁通开口，缺门高及封闭门定义；K-01 保留这些通路，不在外墙或核心新装门。',
    'FA-A/B：共用冻结体量，地上 16 层＋地下 4 层。天气和外部照明是临时审图条件。独立场景使用实时光；正式光照图未重烘。',
]
records=read(f'{cap}/capture_record.json')
probes=read(f'{cap}/runtime_probes.json')
shots={r['file']:r for r in records}
assert len(shots)==177 and all(not r['missing_textures'] for r in records)
assert all(p['closed_leaf_blocks'] and (
    p['hinge_count']==2 and p['open_center_ray_clear'] if 'hinge_count' in p else
    p['capsule_crosses_caution'] and p['capsule_stops_at_closed_leaf'] and not p['auth_or_operation']
) for p in probes)

def shot(id,view):
    name=id.lower()+'_'+view+'.png'
    assert name in shots and (base/cap/name).is_file(), name
    return f'{cap}/{name}'

def verify_pairs():
    for _,a,b,first,others in pairs:
        for view in [first,*(v for v,_ in others)]:
            ar=shots[Path(shot(a[0],view)).name];br=shots[Path(shot(b[0],view)).name]
            assert all(ar[k]==br[k] for k in ('view','resolution','camera','ortho_m','rt_light_energy')), (a,b,view)
verify_pairs()

md=['# 标准休眠楼｜10 款建筑候选对比','',
    '以下均为独立 Godot 场景的 1280×720 实拍。左列为 A 组合，右列为 B 组合；各组可独立选择。点图看原尺寸。','']
web=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
     '<title>标准休眠楼｜建筑候选对比</title><style>',
     ':root{color-scheme:dark;font:16px/1.6 system-ui,sans-serif;background:#111a1e;color:#dce4df}body{max-width:1600px;margin:auto;padding:26px}h1{font-size:clamp(1.65rem,4vw,2.8rem)}h2{margin:0 0 1rem}a{color:#a9dbd3}nav{display:flex;gap:1.1rem;flex-wrap:wrap}section{margin:36px 0;padding:24px;background:#1b292d;border:1px solid #33464b;border-radius:12px}.pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.pair article{min-width:0}img{display:block;width:100%;height:auto;background:#111a1e;object-fit:contain}p{margin:.65em 0}article strong{display:block;margin-bottom:.35rem}.actions{display:flex;gap:.7rem;flex-wrap:wrap;margin-top:.5em}.assets{columns:2}.assets li{break-inside:avoid;margin:0 0 .4rem}details{margin-top:1em}summary{cursor:pointer}li{margin-bottom:.4em}.still{max-width:960px}@media(max-width:640px){body{padding:10px}section{padding:12px}.assets{columns:1}.pair{gap:6px}}</style>',
     '<header><h1>标准休眠楼｜建筑候选对比</h1><p>10 款造型 · 真实 Godot 画面 · 1280×720。左列 A、右列 B；可以分组选择。点图看原尺寸。</p>',
     '<nav>'+''.join(f'<a href="#{a[0][:2]}">{title}</a>' for title,a,_,_,_ in pairs)+'<a href="#motion">楼梯灯光</a><a href="#materials">贴图与源文件</a></nav></header>']
for title,a,b,first,others in pairs:
    md+=['## '+title,'',f'| {a[0]} · {a[1]} | {b[0]} · {b[1]} |','|---|---|']
    md+=['| '+' | '.join(f'[![{x[0]}]({shot(x[0],first)})]({shot(x[0],first)})' for x in (a,b))+' |']
    md+=['| '+' | '.join(' · '.join(f'[{label}]({shot(x[0],v)})' for v,label in others) for x in (a,b))+' |','']
    web += [f'<section id="{a[0][:2]}"><h2>{title}</h2><div class="pair">']
    for id,description in (a,b):
        file=shot(id,first)
        detail=''.join(f'<a href="{shot(id,v)}">{label}</a>' for v,label in others)
        web += [f'<article><strong>{id} · {description}</strong><a href="{file}"><img src="{file}" width="1280" height="720" loading="lazy" alt="{id} Godot"></a><div class="actions">{detail}</div></article>']
    web+=['</div></section>']

motion='evidence/stair_motion_28s.gif'
st=shot('ST-01','whole')
md+=['## ST-01 楼梯照明与适用范围','',f'[双跑样段]({st}) · [28 秒 Godot 灯光动画]({motion})','',*[f'- {s}' for s in limits],'']
web+=[f'<section id="motion"><h2>ST-01｜楼梯与分区感应照明</h2><p><a href="{st}">双跑样段</a> · <a href="{motion}">打开 28 秒原尺寸 GIF</a>（接近、停留、转身、离开与渐灭）</p><details><summary>在页内播放 28 秒 GIF</summary><img class="still" loading="lazy" src="{motion}" alt="Godot 楼梯动态光" width="1280" height="720"></details><ul>',''.join(f'<li>{s}</li>' for s in limits),'</ul></section>']

md+=['## 原生贴图与工程','',
     '[室内 Blender](model/interior_accessories.blend) · [立面 Blender](model/facade_assembly_v1.blend) · [制作与验证说明](README.md) · [GLB](../../../../assets/art/cryo_building_review_v1/models/)','',
     '| 材料 | 原始 PixelLab | 原生 PNG | Nearest 4× 无光裁片 | Aseprite |','|---|---|---|---|---|']
web+=['<section id="materials"><h2>原生贴图与工程</h2><p><a href="model/interior_accessories.blend">室内 Blender</a> · <a href="model/facade_assembly_v1.blend">立面 Blender</a> · <a href="README.md">制作与验证说明</a></p><ul class="assets">']
pack=read('source/material_packaging.json')
for rec in pack:
    key=rec['material']; wh='×'.join(map(str,rec['size']))
    original=f'raw/pixellab/{rec["selected_raw"]}' if 'selected_raw' in rec else ''
    if original and not (base/original).is_file():
        original=next(p.relative_to(base).as_posix() for p in (base/'raw').rglob(rec['selected_raw']))
    native=f'{assets}/textures/{key}.png'
    near=f'evidence/materials/{key}_nearest4.png'
    if not (base/near).exists():
        with Image.open(base/native) as im:
            w,h=im.size
            left=max(0,(w-96)//2)
            top=max(0,(h-96)//2)
            crop=im.crop((left,top,min(w,left+96),min(h,top+96)))
            crop.resize((crop.width*4,crop.height*4),Image.Resampling.NEAREST).save(base/near)
    editable=f'editable/{key}.aseprite'
    files=[('原图',original),('PNG',native),('4×',near if (base/near).exists() else ''),('分层',editable if (base/editable).exists() else '')]
    md+=['| '+f'{key} · {wh} | '+' | '.join(f'[{title}]({path})' if path else '沿用' for title,path in files)+' |']
    web+=[f'<li>{key} · {wh} &nbsp; '+' · '.join(f'<a href="{escape(path)}">{title}</a>' for title,path in files if path)+'</li>']
web+=['</ul></section></html>']
write('preview.md','\n'.join(md));write('preview.html','\n'.join(web))

candidate_rows=[]
for title,a,b,first,others in pairs:
    for id,description in (a,b):
        name=id+'_complete_envelope' if id.startswith('FA') else id
        candidate_rows.append({'id':id,'type':title,'appearance':description,'status':'rendered / art selection pending','glb':f'{assets}/models/{name}.glb','primary_evidence':shot(id,first)})
manifest={
  'source_commit':'f7fa9e8342f77106daad9b9199f34333fca53c89',
  'formal_assets_changed':False,
  'render_scene':'scenes/dev/cryo_building_review_v1.tscn',
  'renderer':'Godot 4.6.2 Compatibility, NVIDIA RTX 4070 Laptop GPU',
  'uv0_target_native_texels_per_m':80,'capture_resolution':[1280,720],
  'candidates':candidate_rows,'constraints':limits,'support_models':['ST-01_stair_sample','K-01_accessories','EXTERIOR_K01_common'],
  'capture_count':len(shots),'still_count':len(shots)-112,'motion_frame_count':112,
  'capture_details':f'{cap}/capture_record.json','motion_gif':motion,
  'runtime_probes':f'{cap}/runtime_probes.json','uv0_report':'evidence/uv0_density.json',
  'usage':'source/usage_summary.json','texture_provenance':'source/material_packaging.json',
  'asset_hashes':{f'{folder}/{p.name}':sha256(p.read_bytes()).hexdigest() for folder in ('models','textures') for p in sorted((base/assets/folder).glob('*.glb' if folder=='models' else '*.png'))},
}
write('review_manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
print(f"Indexed {len(candidate_rows)} candidates, {len(pack)} maps, {manifest['still_count']} stills")
