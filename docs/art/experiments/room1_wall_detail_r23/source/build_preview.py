"""Native-size same-camera viewer of actual Godot frames; no image simulation."""
from pathlib import Path
import json,html,re
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
records=json.loads((EXP/'evidence/capture_record.json').read_text())
files={r['file'] for r in records};sets=[]
for n in range(1,5):sets.append({s[2:-4] for s in files if s.startswith(str(n)+'_') and s.endswith('.png')})
views=sorted(set.intersection(*sets));assert views
labels={'game_rear_patch_closed':'正常游戏视距 · 闭盖','game_rear_patch_open':'正常游戏视距 · 开盖','rear_patch_whole_closed':'完整两块墙板 · 闭盖','rear_patch_whole_open':'完整两块墙板 · 开盖','rear_patch_full_closed':'墙面材质近景 · 闭盖','rear_patch_full_open':'墙面材质近景 · 开盖','rear_patch_joint_detail_closed':'接缝／墙脚细节','rear_patch_base_color':'原生颜色图诊断'}
preferred=['game_rear_patch_closed','rear_patch_whole_closed','rear_patch_full_closed','rear_patch_joint_detail_closed','game_rear_patch_open','rear_patch_whole_open','rear_patch_full_open','rear_patch_base_color']
views=sorted(views,key=lambda x:preferred.index(x) if x in preferred else 999)
options=''.join('<option value="'+html.escape(v)+'">'+html.escape(labels.get(v,v))+'</option>' for v in views)
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Room 1 · 墙面细节返修 r23</title>
<style>body{max-width:1400px;margin:28px auto;padding:0 22px;background:#152225;color:#dce4dc;font:16px/1.7 system-ui}a{color:#abd8dc}h1{font-size:29px}button,select{font:inherit;background:#2a4143;color:#e0e8df;border:1px solid #6b8581;border-radius:4px;padding:9px 12px;margin:4px 5px 4px 0}button[aria-pressed=true]{background:#55766d}.native{max-width:1280px;overflow:auto}.native img{display:block;width:1280px;max-width:none;image-rendering:pixelated}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.grid img,figure img{display:block;max-width:100%;image-rendering:pixelated}.grid img{width:100%}figure{margin:20px 0}small{color:#b3c7bf}details{margin:20px 0}@media(max-width:800px){.grid{grid-template-columns:1fr}}</style>
<h1>Room 1 · 墙面细节密度返修 r23</h1><p>仅后墙两块现有墙板。恢复接缝附近成组沉积、细碎边缘及逐渐变稀的过渡；两份差分改变分布，保持相近完成度。其他材质、模型、布局、灯光和镜头在四组中完全一致，均以 r22 为底。</p>
<p><a href="README.md">范围与制作说明</a> · <a href="editable/">Aseprite 母版</a> · <a href="source/artifact_validation.json">素材检查</a> · <a href="source/runtime_validation.json">场景不变性</a> · <a href="source/capture_validation.json">同机位证据</a></p>
<label>位置 <select id="view">OPTIONS</select></label><div><button data-mode="1">图二风格 · 原墙细节参考</button><button data-mode="2">r22 · 过于稀疏</button><button data-mode="3">新 A</button><button data-mode="4">新 B 差分</button><button id="fit">适应窗口</button><small id="label"></small></div>
<div class="native"><a id="full"><img id="main" alt="相同实际Godot镜头下的墙板比较"></a></div><p><small>默认1280×720原尺寸；切换按钮比较同一位置。缩略图会弱化细节，建议先看原尺寸。参考组只替换墙板材料，不改变其他场景内容。</small></p>
<details><summary>四组同时看</summary><div class="grid"><article>旧墙细节参考<img id="m1"></article><article>r22 稀疏版<img id="m2"></article><article>新 A<img id="m3"></article><article>新 B<img id="m4"></article></div></details>
<h2>原生材质排列</h2><figure><a href="evidence/native_material_comparison.png"><img src="evidence/native_material_comparison.png" alt="原参考、稀疏版、新A、新B的原生像素排列"></a></figure>
<p>新A/B由PixelLab直接在256×256原生画布编辑，没有缩小再放大。仅提交项目自有PixelLab墙图和结构遮罩；未提交Pixel Canals内容，未手绘或程序生成污斑。可编辑区完整替换，不叠加旧做旧。</p>
<p>这是局部待审，没有推广整室；F5仍保持现行版。本轮沿用原GI，不是新烘焙光照。</p>
<script>const view=document.getElementById('view'),main=document.getElementById('main');let mode=3,fit=false;function refresh(){main.src='evidence/'+mode+'_'+view.value+'.png';document.getElementById('full').href=main.src;for(let n=1;n<=4;n++)document.getElementById('m'+n).src='evidence/'+n+'_'+view.value+'.png';document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',Number(b.dataset.mode)===mode));document.getElementById('label').textContent=['','旧墙参考','r22稀疏版','新A','新B'][mode];}document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{mode=Number(b.dataset.mode);refresh()});document.getElementById('fit').onclick=()=>{fit=!fit;main.style.width=fit?'100%':'1280px';document.getElementById('fit').textContent=fit?'恢复1:1像素':'适应窗口';};view.onchange=refresh;refresh();</script></html>'''
(EXP/'preview.html').write_text(page.replace('OPTIONS',options),encoding='utf-8')
print('R23_PREVIEW',len(views),'matched views')
