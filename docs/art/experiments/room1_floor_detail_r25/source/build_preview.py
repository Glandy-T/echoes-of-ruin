from pathlib import Path
import json,html
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
records=json.loads((EXP/'evidence/capture_record.json').read_text());files={r['file'] for r in records}
views=sorted(set.intersection(*[{f[2:-4] for f in files if f.startswith(str(i)+'_') and f.endswith('.png')} for i in [1,2,3]]));assert views
labels={'game_floor_patch_closed':'正常游戏机位 · 闭盖','game_floor_patch_open':'正常游戏机位 · 开盖','floor_patch_oblique':'局部斜视 · 床脚与空地','floor_patch_full':'局部斜视 · 床脚与空地','p12_p13_contact_detail':'P12／P13 接触细节','floor_patch_unoccluded':'无遮挡技术诊断（暂隐舱体）','floor_patch_close':'床脚接触近景','floor_patch_topdown':'俯视技术诊断','floor_patch_base_color':'原色材质诊断','base_color_floor_patch':'原色材质诊断','base_color_floor_unoccluded':'原色／无遮挡技术诊断','floor_patch_raw':'原始 GI','floor_patch_denoised':'降噪 GI'}
# Prefer a local view to avoid hiding the subject in a whole-room thumbnail.
views.sort(key=lambda x:(0 if 'full' in x or 'oblique' in x else 1 if 'detail' in x or 'close' in x else 2 if 'game' in x else 3,x))
options=''.join('<option value="'+html.escape(v)+'">'+html.escape(labels.get(v,v))+'</option>' for v in views)
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Room 1 · 地板局部细节 r25</title>
<style>body{max-width:1400px;margin:28px auto;padding:0 22px;background:#152225;color:#dce4dc;font:16px/1.7 system-ui}a{color:#aed7da}h1{font-size:29px}button,select{font:inherit;background:#294143;color:#e1e8df;border:1px solid #6a8580;border-radius:4px;padding:9px 13px;margin:4px 5px 4px 0}button[aria-pressed=true]{background:#54766c}.native{max-width:1280px;overflow:auto}.native img{display:block;width:1280px;max-width:none;image-rendering:pixelated}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.grid img{display:block;width:100%;image-rendering:pixelated}.crop img{width:256px;max-width:100%;image-rendering:pixelated}small{color:#b4c8bf}details{margin:22px 0}@media(max-width:800px){.grid{grid-template-columns:1fr}}</style>
<h1>Room 1 · 地板局部细节 r25</h1><p>只比较 P12／P13 舱边与邻近空地的一块 3.2×3.2m 地坪。四墙维持已认可 r24；模型、布局、灯、地面其余区域不改。</p>
<p><strong>当前观察：</strong>正常暗光下整体差异较弱，改善主要在床脚细碎过渡；可切换“原色材质诊断”分开查看贴图和光照影响。本轮仍是局部待选。</p>
<p>A 是当前 r22 地板；B 在同一区域恢复 r15 原始密度，仅作诊断；C 是 PixelLab 原生 256px 新返修，不再放大像素。不增加砖缝、路线、漏液位置或黄褐色沉积。</p>
<p><a href="README.md">制作与范围</a> · <a href="editable/floor_candidate_r25.aseprite">候选 Aseprite 母版</a> · <a href="source/artifact_validation.json">局部不变性</a> · <a href="source/runtime_validation.json">运行验证</a></p>
<div><select id="view">OPTIONS</select><button data-mode="1">A 当前</button><button data-mode="2">B 原密度参考</button><button data-mode="3">C PixelLab 新返修</button><button id="fit">适合窗口</button></div>
<p id="caption"></p><div class="native" id="frame"><img id="main" alt="实际 Godot 同机位截图"></div>
<small>三版使用相同的1280×720画面、镜头与照明。技术机位仅供审图；若有无遮挡诊断，无遮挡图暂隐舱体，暗色舱位仍是既有GI投影；原色图供区分贴图层次，说明见下方记录，不代表游戏场景变化。</small>
<h2>并排比较当前机位</h2><div class="grid"><article>A 当前<img id="a"></article><article>B 原密度参考<img id="b"></article><article>C PixelLab 新返修<img id="c"></article></div>
<h2>局部颜色图原尺寸</h2><div class="grid crop"><article>A 当前<img src="source/current_r22_crop.png"></article><article>B 参考<img src="source/final_patch_reference.png"></article><article>C 新返修<img src="source/final_patch_candidate.png"></article></div>
<p>边界8px与实际舱底遮罩区域精确保留当前像素，用于保护已有配准；黑遮罩内 PixelLab 原始输出中的其他图形完全未使用。仅白遮罩内整片替换，不叠旧做旧层。原色／无遮挡诊断还会显示舱底保护区的旧像素轮廓；正常游戏图保持完整舱体，用于检查真实可见接触。B/C仍为局部待审，不推广全室。</p>
<details><summary>原色与GI诊断（仅C）</summary><div class="grid"><article>原生颜色诊断<img src="evidence/3_base_color_floor_patch.png"></article><article>原始GI<img src="evidence/3_raw_floor_patch.png"></article><article>降噪GI<img src="evidence/3_denoised_floor_patch.png"></article></div></details>
<details><summary>实际截图及状态记录</summary><a href="evidence/capture_record.json">capture_record.json</a> · <a href="source/capture_validation.json">capture_validation.json</a></details>
<script>const sel=document.getElementById('view');let mode=3,fit=false;const names={1:'A 当前地板',2:'B r15原始密度诊断',3:'C PixelLab新局部'};function update(){const v=sel.value;document.getElementById('main').src=`evidence/${mode}_${v}.png`;document.getElementById('caption').textContent=names[mode]+' / '+sel.selectedOptions[0].text;for(const [id,n] of [['a',1],['b',2],['c',3]])document.getElementById(id).src=`evidence/${n}_${v}.png`;document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',Number(b.dataset.mode)===mode));}document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{mode=Number(b.dataset.mode);update()});sel.onchange=update;document.getElementById('fit').onclick=()=>{fit=!fit;document.getElementById('main').style.width=fit?'100%':'1280px';document.getElementById('fit').textContent=fit?'原始大小':'适合窗口';};update();</script></html>'''
page=page.replace('OPTIONS',options)
(EXP/'preview.html').write_text(page,encoding='utf8');print('R25_PREVIEW',len(views),'matched A/B/C views')
