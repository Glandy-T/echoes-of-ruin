from pathlib import Path
import json,html
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
records=json.loads((EXP/'evidence/capture_record.json').read_text());files={r['file'] for r in records}
views=sorted({n[2:-4] for n in files if n.startswith('1_') and '2_'+n[2:] in files})
assert views
labels={'game_front_left_closed':'游戏镜头 · 前排左','game_front_middle_closed':'游戏镜头 · 前排中','game_front_right_closed':'游戏镜头 · 前排右','game_back_left_closed':'游戏镜头 · 后排左','game_back_middle_closed':'游戏镜头 · 后排中','game_back_right_closed':'游戏镜头 · 后排右','whole_room_closed':'整室总览','corner_rear_left':'后左墙角','corner_rear_right':'后右墙角','corner_front_left':'前左墙角','corner_front_right':'前右墙角','door_header_and_sides':'门楣及门洞两侧','front_wall_lamp':'前墙／灯槽接头','front_wall_full':'前墙局部','left_wall_full':'左墙局部','right_wall_full':'右墙局部','rear_wall_full':'后墙局部','game_front_left_open':'P12开盖 · 游戏镜头','p12_oblique_open':'P12开盖近景'}
scan_views=[]
for side,title,count in [('front','前墙',4),('rear','后墙',4),('left','左墙',2),('right','右墙',2)]:
    for i in range(1,count+1):
        key=f'scan_{side}_{i:02d}';labels[key]=f'无遮挡巡检 · {title}第{i}段';scan_views.append(key)
preferred=['game_front_middle_closed','game_front_left_closed','game_front_right_closed','game_back_middle_closed','game_back_left_closed','game_back_right_closed','door_header_and_sides','left_wall_full','right_wall_full','rear_wall_full','front_wall_full']+scan_views
views=sorted(views,key=lambda v:preferred.index(v) if v in preferred else 999)
options=''.join('<option value="'+html.escape(v)+'">'+html.escape(labels.get(v,v))+'</option>' for v in views)
usage=sum(json.loads(p.read_text())['usage']['generations'] for p in EXP.glob('result_*.json'))
diagnostics=[]
for name,title in [('2_raw_door_header.png','r24门楣 · 原始GI'),('2_denoised_door_header.png','r24门楣 · 降噪GI'),('2_raw_rear_corner.png','r24后墙角 · 原始GI'),('2_denoised_rear_corner.png','r24后墙角 · 降噪GI')]:
    if name in files:diagnostics.append(f'<article>{title}<a href="evidence/{name}"><img loading="lazy" src="evidence/{name}"></a></article>')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Room 1 · 全墙细节推广 r24</title>
<style>body{max-width:1400px;margin:28px auto;padding:0 22px;background:#152225;color:#dce4dc;font:16px/1.7 system-ui}a{color:#aed7da}h1{font-size:29px}button,select{font:inherit;background:#294143;color:#e1e8df;border:1px solid #6a8580;border-radius:4px;padding:9px 13px;margin:4px 5px 4px 0}button[aria-pressed=true]{background:#54766c}.native{max-width:1280px;overflow:auto}.native img{display:block;width:1280px;max-width:none;image-rendering:pixelated}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.grid img,figure img{display:block;width:100%;image-rendering:pixelated}figure{margin:22px 0;max-width:1100px}small{color:#b4c8bf}details{margin:22px 0}@media(max-width:800px){.grid{grid-template-columns:1fr}}</style>
<h1>Room 1 · 全墙细节推广 r24</h1><p>按用户认可的r23完成度返修四墙。8组独立双墙板／16个半板及门洞周边，分布有别、丰富度相近；不保留几乎空白的差分。地坪、舱体、门、灯带、模型、布局与原GI保持。</p>
<p><a href="README.md">范围／来源与验证</a> · <a href="editable/">四墙Aseprite母版</a> · <a href="room1_wall_detail_full_r24.blend">Blender材质源</a> · <a href="source/artifact_validation.json">素材核验</a> · <a href="source/runtime_validation.json">场景不变性</a> · <a href="source/capture_validation.json">同机位证据</a></p>
<label>观察位置 <select id="view">OPTIONS</select></label><div><button data-mode="1">r22 · 旧稀疏墙面</button><button data-mode="2">r24 · 全墙返修</button><button id="fit">适应窗口</button><small id="label"></small></div>
<div class="native"><a id="full"><img id="main" alt="真实Godot同机位四墙材质比较"></a></div><p><small>默认1280×720原尺寸，可横向滚动；切换前后版本比较同一机位。正常游戏图保留全部舱体。标为“无遮挡巡检”的分段视图临时隐藏舱体，只供检查墙面；地面仍保留原烘焙影子，切面外灰色是背景。技术镜头／显隐状态均未保存进游戏场景。</small></p>
<details><summary>同时看两版缩略图</summary><div class="grid"><article>r22旧稀疏材质<img id="before"></article><article>r24全墙返修<img id="after"></article></div></details>
<h2>逐组原生材质检查</h2><figure><a href="evidence/native_variants_review.png"><img src="evidence/native_variants_review.png" alt="16个半板原生像素排列"></a></figure>
<figure><a href="evidence/wall_atlases_review.png"><img loading="lazy" src="evidence/wall_atlases_review.png" alt="四墙实际完整颜色图"></a></figure>
<details><summary>原始／降噪GI实际对照</summary><div class="grid">DIAGNOSTICS</div><p>两组都使用r24材质与原r19配套光图；仅诊断光图噪声，不把烘焙噪声当作像素贴图。</p></details>
<p>材料创作和返修均由PixelLab完成，新增实际用量USAGE generations，含拒用图与返修。A/B复用已认可r23原图；原始输入、输出、任务ID和用量保留。没有上传Pixel Canals内容，没有脚本／手绘做旧。</p>
<p>门洞周边按现有开口核对遮罩，覆盖旧遮罩遗漏的可见墙面；开口与门本身保持。灯面和结构保护区逐像素保留。沿用r19既有GI，本轮是四墙材质交付，不是新烘焙。</p>
<script>const view=document.getElementById('view'),main=document.getElementById('main');let mode=2,fit=false;function refresh(){main.src='evidence/'+mode+'_'+view.value+'.png';document.getElementById('full').href=main.src;document.getElementById('before').src='evidence/1_'+view.value+'.png';document.getElementById('after').src='evidence/2_'+view.value+'.png';document.getElementById('label').textContent=mode===1?'r22旧墙':'r24全墙';document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',Number(b.dataset.mode)===mode));}document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{mode=Number(b.dataset.mode);refresh()});document.getElementById('fit').onclick=()=>{fit=!fit;main.style.width=fit?'100%':'1280px';document.getElementById('fit').textContent=fit?'恢复1:1像素':'适应窗口';};view.onchange=refresh;refresh();</script></html>'''
(EXP/'preview.html').write_text(page.replace('OPTIONS',options).replace('USAGE',str(int(usage))).replace('DIAGNOSTICS',''.join(diagnostics)),encoding='utf-8')
print('R24_PREVIEW',len(views),'matched views')
