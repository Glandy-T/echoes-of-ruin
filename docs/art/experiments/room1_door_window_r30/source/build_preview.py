from pathlib import Path
import json
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
names={r['file'] for r in json.loads((EXP/'evidence/capture_record.json').read_text())}
pairs=[(a,'2_b_'+a[4:]) for a in sorted(names) if a.startswith('1_a_') and '2_b_'+a[4:] in names]
def fig(n,label):return f'<figure><figcaption>{label}</figcaption><a href="evidence/{n}"><img src="evidence/{n}" loading="lazy"></a></figure>'
page='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Room 1 认证窗白边修复 r30</title><style>body{background:#131b1c;color:#d9e3de;font:16px/1.6 system-ui;margin:24px auto;padding:0 20px;max-width:1600px}a{color:#a7d3d8}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;background:#202b2c;padding:10px}img{display:block;width:100%;height:auto;image-rendering:pixelated}h2{font-size:19px;margin-top:28px}@media(max-width:800px){.pair{grid-template-columns:1fr}}</style><h1>Room 1 · 认证小窗去白边 r30</h1><p>只精修小窗外围224个原生像素：接回门面哑光涂层，留一像素暗色凹口。内部状态灯、r29主体PixelLab材质、全室与开闭保持。Aseprite独立局部层；新增PixelLab消耗为0。正式F5未切换。</p><p><a href="README.md">来源与检查</a> · <a href="editable/door_front_r30.aseprite">Aseprite母版</a> · <a href="room1_door_window_r30.blend">Blender源</a></p>'''
for a,b in pairs:page+=f'<h2>{a[4:-4]}</h2><div class="pair">'+fig(a,'A · r29 原浅色包边')+fig(b,'B · r30 局部精修')+'</div>'
page+='<h2>近景、认证和开启状态</h2><div class="pair">'+''.join(fig(n,n[4:-4]) for n in sorted(names) if n.startswith('2_b_') and not any(n==b for _,b in pairs))+'</div><h2>原生贴图</h2><img style="width:224px" src="source/readback_door.png"></html>'
(EXP/'preview.html').write_text(page,encoding='utf8');print('R30_PREVIEW',len(pairs),'A/B pairs')
