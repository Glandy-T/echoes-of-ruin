"""Comparison page indexing actual same-camera GPU captures, never simulated art."""
from pathlib import Path
import json,html
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
records=json.loads((EXP/'evidence/capture_record.json').read_text())
files={r['file'] for r in records}
pairs=sorted(n[2:-4] for n in files if n.startswith('1_') and '2_'+n[2:] in files)
assert pairs
labels={'game_front_left_closed':'游戏镜头 · 前排左','game_front_middle_closed':'游戏镜头 · 前排中','game_front_right_closed':'游戏镜头 · 前排右','game_back_left_closed':'游戏镜头 · 后排左','game_back_middle_closed':'游戏镜头 · 后排中','game_back_right_closed':'游戏镜头 · 后排右','game_front_left_open':'游戏镜头 · P12 开盖','p12_oblique_closed':'P12 近景 · 闭合','p12_oblique_open':'P12 近景 · 开盖','whole_room_closed':'整室总览','floor_contacts':'连续地面／舱底接触','door_header':'门洞／上部灯带','front_wall_lamp':'真实前墙／灯带','corner_rear_left':'后左墙角','corner_rear_right':'后右墙角','corner_front_left':'前左墙角','corner_front_right':'前右墙角'}
preferred=['game_front_middle_closed','game_front_left_closed','game_front_right_closed','game_back_middle_closed','game_back_left_closed','game_back_right_closed','game_front_left_open','p12_oblique_closed','p12_oblique_open','whole_room_closed','floor_contacts','door_header','front_wall_lamp','corner_rear_left','corner_rear_right','corner_front_left','corner_front_right']
pairs=sorted(pairs,key=lambda p:preferred.index(p) if p in preferred else 999)
options=''.join('<option value="'+html.escape(p)+'">'+html.escape(labels.get(p,p))+'</option>' for p in pairs)
gallery=''.join('<a href="evidence/'+html.escape(n)+'"><img loading="lazy" src="evidence/'+html.escape(n)+'" alt="'+html.escape(n)+'"><small>'+html.escape(n)+'</small></a>' for n in sorted(files) if n.startswith('2_pod_'))
usage=sum(json.loads(p.read_text())['usage']['generations'] for p in EXP.glob('result_*.json'))
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Room 1 · 整室像素材质统一 r22</title>
<style>body{margin:28px auto;max-width:1400px;padding:0 22px;background:#152225;color:#dce4dc;font:16px/1.7 system-ui}h1{font-size:29px;margin-bottom:8px}a{color:#a9d5da}button,select{background:#2b4143;color:#e0e9df;border:1px solid #69817f;border-radius:4px;padding:9px 14px;font:inherit;margin:5px 6px 5px 0}button[aria-pressed=true]{background:#53716b}.native{max-width:1280px;overflow:auto;background:#0b1315}.native img{display:block;width:1280px;max-width:none;image-rendering:pixelated}.pair,.gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.pair img,.gallery img{width:100%;image-rendering:pixelated;display:block}.gallery{grid-template-columns:repeat(4,minmax(0,1fr))}small{color:#b4c6c1}details{margin:24px 0}figure{margin:18px 0}figure img{max-width:100%;image-rendering:pixelated}@media(max-width:800px){.pair,.gallery{grid-template-columns:1fr}}</style>
<h1>Room 1 · 整室像素材质统一 r22</h1><p>以较顺眼的 r20 为材料尺度基准；保持模型、UV、布局、镜头、灯光与原 Shader。四墙、连续地坪、20 舱外壳统一待审，正式 F5 仍为 r19。没有沿用 r21 的 4× 大颗粒。</p>
<p><a href="README.md">范围／来源／限制</a> · <a href="editable/">Aseprite 母版</a> · <a href="source/artifact_validation.json">素材核验</a> · <a href="source/runtime_validation.json">运行核验</a> · <a href="source/capture_validation.json">同机位证据</a></p>
<label>观察位置 <select id="view">OPTIONS</select></label><div><button data-mode="1">A · 当前 r19</button><button data-mode="2">B · 新整室 r22</button><button id="fit">适应窗口</button><small id="label"></small></div>
<div class="native"><a id="full"><img id="main" alt="实际 Godot 原尺寸对比"></a></div><p><small>默认 1280×720 原尺寸，可横向滚动；切换 A/B 比较相同机位。缩小的缩略图会弱化颗粒，建议先看原尺寸。</small></p>
<details><summary>同时看两版缩略图</summary><div class="pair"><article><h3>当前 r19</h3><img id="before"></article><article><h3>整室候选 r22</h3><img id="after"></article></div></details>
<details><summary>全部 20 舱技术近景</summary><div class="gallery">GALLERY</div><p>用于检查绑定、编号、接触与材质。技术机位没有保存进游戏相机。</p></details>
<h2>原生贴图检查</h2><figure><a href="evidence/texture_comparison.png"><img loading="lazy" src="evidence/texture_comparison.png" alt="真实像素材质前后排列"></a></figure>
<p>本轮实际 PixelLab 用量：USAGE generations。原始输出、提示、导图、遮罩与任务 ID 保留；参考作品内容未上传。Aseprite／脚本仅作导图、遮罩、配准、功能编号和导出。</p>
<p>仍沿用 r19 原 GI，未重烘新颜色的间接反弹；本轮是材料协调待审，非最终配套光照交付。门、玻璃、内腔、屏幕和灯管保持。</p>
<script>const view=document.getElementById('view'),main=document.getElementById('main');let mode=2,fit=false;function refresh(){const path='evidence/'+mode+'_'+view.value+'.png';main.src=path;document.getElementById('full').href=path;document.getElementById('before').src='evidence/1_'+view.value+'.png';document.getElementById('after').src='evidence/2_'+view.value+'.png';document.getElementById('label').textContent=mode===1?'当前 r19':'整室候选 r22';document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',Number(b.dataset.mode)===mode));}document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{mode=Number(b.dataset.mode);refresh()});document.getElementById('fit').onclick=()=>{fit=!fit;main.style.width=fit?'100%':'1280px';document.getElementById('fit').textContent=fit?'恢复 1:1 像素':'适应窗口';};view.onchange=refresh;refresh();</script></html>'''
(EXP/'preview.html').write_text(page.replace('OPTIONS',options).replace('GALLERY',gallery).replace('USAGE',str(int(usage))),encoding='utf-8')
print('R22_PREVIEW',len(pairs),'matched views',len(files),'actual frames')
