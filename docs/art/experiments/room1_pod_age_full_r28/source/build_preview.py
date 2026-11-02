from pathlib import Path
import json
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
record=json.loads((EXP/'evidence/capture_record.json').read_text(encoding='utf8'))
# Derive genuine matching A/B pairs from final capture names, never from old records.
names={r['file'] for r in record};pairs=[]
for name in sorted(names):
 if not name.startswith('1_'):continue
 other='2_'+name[2:]
 if other in names:pairs.append((name,other))
sections=[]
for a,b in pairs:
 title=a[2:-4].replace('_',' ')
 sections.append('<section><h2>'+title+'</h2><div class="pair">'+''.join('<figure><figcaption>'+label+'</figcaption><a href="evidence/'+name+'"><img loading="lazy" src="evidence/'+name+'"></a></figure>' for name,label in [(a,'A · 已认可P12＋其余旧舱'),(b,'B · r28全20舱差分')])+'</div></section>')
details=[n for n in sorted(names) if n.startswith('2_') and not any(n==b for _,b in pairs)]
gallery=''.join('<figure><figcaption>'+n[:-4].replace('_',' ')+'</figcaption><a href="evidence/'+n+'"><img loading="lazy" src="evidence/'+n+'"></a></figure>' for n in details)
layout=json.loads((HERE/'layout_variants.json').read_text());rows=''.join('<tr><td>'+p['id']+'</td><td>'+p['lid_variant'].upper()+'</td><td>'+p['side_variant'].upper()+'</td><td>'+p['end_variant'].upper()+'</td></tr>' for p in layout['pods'])
head='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Room 1 全舱做旧差分 r28</title><style>body{background:#131b1c;color:#d9e3de;font:16px/1.6 system-ui;margin:24px auto;padding:0 20px;max-width:1600px}h1{font-size:26px}h2{font-size:19px;margin-top:32px}a{color:#a7d3d8}.pair,.gallery{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;background:#202b2c;padding:10px}figcaption{margin-bottom:8px;color:#c5d3cf}img{width:100%;height:auto;display:block;image-rendering:pixelated}table{border-collapse:collapse}td,th{padding:5px 16px;border-bottom:1px solid #405151}p{max-width:1080px}@media(max-width:800px){.pair,.gallery{grid-template-columns:1fr}}</style><h1>Room 1 · 全20舱颗粒与做旧差分 r28</h1><p>沿用已认可r27，保留A并新增PixelLab B/C/D三套不同痕迹。每类面4种来源，错开为20个不重复的盖板／侧壳／端面组合；不是宣称20套独立AI原图。P12与已认可版本逐像素一致，编号01–20。模型、UV、位置、灯光、玻璃、屏幕、功能与动画保持。</p><p>未重新烘焙GI；只有P12有实际开闭玩法，其他舱保持关闭。正式F5仍r19，本页为独立全室美术审查。<a href="README.md">来源与检查</a> · <a href="room1_pod_age_full_r28.blend">完整Blender候选</a></p>'''
head=head.replace('每类面4种来源','4种盖板、4种侧壳、3种端面')
page=head+''.join(sections)+'<h2>全20舱检查一览</h2><a href="evidence/pod_contact_sheet.png"><img src="evidence/pod_contact_sheet.png"></a><details><summary>展开逐舱与四角技术检查</summary><div class="gallery">'+gallery+'</div></details><h2>合格原生做旧来源</h2><a href="evidence/native_variation_sheet.png"><img style="max-width:900px" src="evidence/native_variation_sheet.png"></a><h2>固定差分安排</h2><table><tr><th>编号</th><th>盖板</th><th>侧壳</th><th>端面</th></tr>'+rows+'</table></html>'
(EXP/'preview.html').write_text(page,encoding='utf8');print('R28_PREVIEW',len(pairs),'A/B pairs;',len(details),'detail frames')
