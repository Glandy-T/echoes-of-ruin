"""Static index of real same-camera Godot captures, with synchronized views."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
usage=sum(json.loads(p.read_text())['usage']['generations'] for p in EXP.glob('result_*.json'))
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Room 1 · 局部像素对比 r21</title><style>
body{margin:28px auto;max-width:1600px;padding:0 24px;background:#142022;color:#e0e5dd;font:16px/1.65 system-ui}h1{font-size:30px;margin-bottom:8px}p{max-width:1100px}a{color:#b3d7db}button,select{padding:9px 15px;margin:5px 6px 5px 0;background:#273b3d;color:#e0e5dd;border:1px solid #647b79;border-radius:4px;font:inherit}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px}article{background:#1d2e30;padding:12px}article h2{font-size:20px;margin:0 0 4px}article p{font-size:14px;margin-top:0;color:#bccdc8}img{width:100%;display:block;image-rendering:pixelated}.controls{margin:24px 0}figure{margin:25px 0;max-width:1100px}figcaption{padding:8px 0;color:#b2c5bf}small{color:#b2c5bf}@media(max-width:900px){.grid{grid-template-columns:1fr}}
</style><h1>Room 1 · 局部像素颗粒与块面加强 r21</h1>
<p>仅左墙两块墙板与 P12 三块外壳。模型、UV、布局、镜头参数与原始光图保持，正式 F5 仍是 r19。下列是独立候选的实际 Godot 截图。</p>
<p><a href="README.md">范围与技术说明</a> · <a href="source/runtime_validation.json">局部不变性检查</a> · <a href="source/artifact_validation.json">贴图／Aseprite 核验</a> · <a href="editable/">可编辑母版</a></p>
<div class="controls"><label>观察位置 <select id="view"><option value="gameplay_distance">正常游戏视距 · P12</option><option value="left_distance">正常视距 · 左墙样段</option><option value="p12">P12 外壳近景</option><option value="left_bay">左墙两块墙板近景</option></select></label><label>状态 <select id="pose"><option value="closed">闭盖</option><option value="open">开盖</option></select></label></div>
<div class="grid">
<article><h2>A · 原版 r19</h2><p>原像素贴图与原光照，完整保留作基准。</p><a class="frame-link"><img id="mode1" alt="原版同机位截图"></a></article>
<article><h2>B · 上轮 r20</h2><p>上一轮 2× 材料网格；保持原光照。</p><a class="frame-link"><img id="mode2" alt="只调整像素贴图"></a></article>
<article><h2>C · 本轮 r21 加强</h2><p>本轮 4× 材料网格与更明确的 PixelLab 块面；同原光照。</p><a class="frame-link"><img id="mode3" alt="新贴图与局部明暗候选"></a></article>
</div><p><small>三列使用同一个位置／开闭选择；点击图片看 1280×720 原帧。没有故意模糊 A、改变曝光或对全室添加像素滤镜。近景便于查颗粒，正常游戏视距用于判断实际可见程度。</small></p>
<h2>原贴图像素对照</h2><figure><a href="evidence/texture_comparison.png"><img loading="lazy" src="evidence/texture_comparison.png" alt="原材质与PixelLab新图的最近邻放大对比"></a><figcaption>只做最近邻放大与排列，未修饰截图／像素图。左：原整室 r19；中：上轮 r20；右：本轮 r21。三组均为同一光照。</figcaption></figure>
<details><summary>颜色图诊断与恢复原版证据</summary><div class="grid"><article><h2>上轮 r20 颜色图</h2><a href="evidence/2_left_bay_base_color.png"><img loading="lazy" src="evidence/2_left_bay_base_color.png"></a></article><article><h2>本轮 r21 颜色图</h2><a href="evidence/3_left_bay_base_color.png"><img loading="lazy" src="evidence/3_left_bay_base_color.png"></a></article><article><h2>切回 A</h2><a href="evidence/1_restore_p12_closed.png"><img loading="lazy" src="evidence/1_restore_p12_closed.png"></a></article></div><p><a href="evidence/capture_record.json">逐张机位／分辨率记录</a> · <a href="source/visual_validation.json">同机位／恢复／截图哈希核验</a></p></details>
<p>本轮共 PIXELLAB_USAGE 次 PixelLab generations；原始输出、实际提示、任务 ID 和用量均保留。没有提交第三方参考图，没有手绘／程序化做旧。</p>
<p>本轮只比较 PixelLab 贴图绘画，三组均使用 r19 原 shader／光照；没有套用上一轮明暗分级。未重烘新颜色的间接反弹，也未更改全画面像素网格。局部候选不等于整室批准。</p>
<script>const view=document.getElementById('view'),pose=document.getElementById('pose');function refresh(){for(let n=1;n<=3;n++){const img=document.getElementById('mode'+n);img.src='evidence/'+n+'_'+view.value+'_'+pose.value+'.png';img.parentElement.href=img.src;}}view.onchange=pose.onchange=refresh;refresh();</script></html>'''
html=html.replace('</style>', '.native-frame{max-width:1280px;overflow:auto;background:#0d1517}.native-frame img{width:1280px;max-width:none}.native-controls button[aria-pressed=true]{background:#526d69}.native-controls{margin-bottom:12px}</style>')
hero='<h2>大图切换比较</h2><p><small>默认按原始 1280×720 显示，可横向滚动；也可点“适应窗口”。三列缩略图会缩小颗粒，建议先看这里。</small></p><div class="native-controls"><button data-mode="1">原整室 r19</button><button data-mode="2">上轮 r20</button><button data-mode="3">本轮 r21</button><button id="fit">适应窗口</button><span id="native-label"></span></div><div class="native-frame"><a id="native-link"><img id="native-image" alt="同机位原尺寸切换"></a></div>'
html=html.replace('<div class="grid">',hero+'<details><summary>三列缩略对照</summary><div class="grid">',1)
html=html.replace('</div><p><small>三列','</div></details><p><small>三列',1)
old_script=html[html.index('<script>'):html.index('</script>')+9]
new_script="<script>const view=document.getElementById('view'),pose=document.getElementById('pose'),nativeImage=document.getElementById('native-image');let selected=3,fit=false;function refresh(){for(let n=1;n<=3;n++){const img=document.getElementById('mode'+n);img.src='evidence/'+n+'_'+view.value+'_'+pose.value+'.png';img.parentElement.href=img.src;}nativeImage.src='evidence/'+selected+'_'+view.value+'_'+pose.value+'.png';document.getElementById('native-link').href=nativeImage.src;document.getElementById('native-label').textContent=['','原整室 r19','上轮 r20','本轮 r21'][selected];document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',Number(b.dataset.mode)===selected));}document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{selected=Number(b.dataset.mode);refresh();});document.getElementById('fit').onclick=()=>{fit=!fit;nativeImage.style.width=fit?'100%':'1280px';document.getElementById('fit').textContent=fit?'恢复 1:1 像素':'适应窗口';};view.onchange=pose.onchange=refresh;refresh();</script>"
html=html.replace(old_script,new_script)
(EXP/'preview.html').write_text(html.replace('PIXELLAB_USAGE',str(int(usage))),encoding='utf-8')
print('R21_PREVIEW_BUILT')
