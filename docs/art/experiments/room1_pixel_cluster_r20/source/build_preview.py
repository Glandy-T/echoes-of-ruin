"""Static index of real same-camera Godot captures, with synchronized views."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
usage=sum(json.loads(p.read_text())['usage']['generations'] for p in EXP.glob('result_*.json'))
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Room 1 · 局部像素对比 r20</title><style>
body{margin:28px auto;max-width:1600px;padding:0 24px;background:#142022;color:#e0e5dd;font:16px/1.65 system-ui}h1{font-size:30px;margin-bottom:8px}p{max-width:1100px}a{color:#b3d7db}button,select{padding:9px 15px;margin:5px 6px 5px 0;background:#273b3d;color:#e0e5dd;border:1px solid #647b79;border-radius:4px;font:inherit}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px}article{background:#1d2e30;padding:12px}article h2{font-size:20px;margin:0 0 4px}article p{font-size:14px;margin-top:0;color:#bccdc8}img{width:100%;display:block;image-rendering:pixelated}.controls{margin:24px 0}figure{margin:25px 0;max-width:1100px}figcaption{padding:8px 0;color:#b2c5bf}small{color:#b2c5bf}@media(max-width:900px){.grid{grid-template-columns:1fr}}
</style><h1>Room 1 · 局部像素颗粒与明暗 r20</h1>
<p>仅左墙两块墙板与 P12 三块外壳。模型、UV、布局、镜头参数与原始光图保持，正式 F5 仍是 r19。下列是独立候选的实际 Godot 截图。</p>
<p><a href="README.md">范围与技术说明</a> · <a href="source/runtime_validation.json">局部不变性检查</a> · <a href="source/artifact_validation.json">贴图／Aseprite 核验</a> · <a href="editable/">可编辑母版</a></p>
<div class="controls"><label>观察位置 <select id="view"><option value="gameplay_distance">正常游戏视距 · P12</option><option value="left_distance">正常视距 · 左墙样段</option><option value="p12">P12 外壳近景</option><option value="left_bay">左墙两块墙板近景</option></select></label><label>状态 <select id="pose"><option value="closed">闭盖</option><option value="open">开盖</option></select></label></div>
<div class="grid">
<article><h2>A · 原版 r19</h2><p>原像素贴图与原光照，完整保留作基准。</p><a class="frame-link"><img id="mode1" alt="原版同机位截图"></a></article>
<article><h2>B · PixelLab 新颗粒</h2><p>材料细节由 PixelLab 在较粗网格重绘；光照保持 A。</p><a class="frame-link"><img id="mode2" alt="只调整像素贴图"></a></article>
<article><h2>C · B＋局部明暗概括</h2><p>同一套 B 贴图；局部受光用保色相的温和亮度分级。</p><a class="frame-link"><img id="mode3" alt="新贴图与局部明暗候选"></a></article>
</div><p><small>三列使用同一个位置／开闭选择；点击图片看 1280×720 原帧。没有故意模糊 A、改变曝光或对全室添加像素滤镜。近景便于查颗粒，正常游戏视距用于判断实际可见程度。</small></p>
<h2>原贴图像素对照</h2><figure><a href="evidence/texture_comparison.png"><img loading="lazy" src="evidence/texture_comparison.png" alt="原材质与PixelLab新图的最近邻放大对比"></a><figcaption>只做最近邻放大与排列，未修饰截图／像素图。左 A，右 B；C 与 B 使用同一套贴图。</figcaption></figure>
<details><summary>颜色图诊断与恢复原版证据</summary><div class="grid"><article><h2>A 原颜色图</h2><a href="evidence/1_left_bay_base_color.png"><img loading="lazy" src="evidence/1_left_bay_base_color.png"></a></article><article><h2>B 新颜色图</h2><a href="evidence/2_left_bay_base_color.png"><img loading="lazy" src="evidence/2_left_bay_base_color.png"></a></article><article><h2>切回 A</h2><a href="evidence/1_restore_p12_closed.png"><img loading="lazy" src="evidence/1_restore_p12_closed.png"></a></article></div><p><a href="evidence/capture_record.json">逐张机位／分辨率记录</a> · <a href="source/visual_validation.json">同机位／恢复／截图哈希核验</a></p></details>
<p>本轮共 PIXELLAB_USAGE 次 PixelLab generations，含两次弃用墙图；原始输出、实际提示、任务 ID 和弃用原因均保留。没有提交第三方参考图，没有手绘／程序化做旧。</p>
<p>C 是风格原型，不代表 Pixel Canals 的已知 Shader。沿用 r19 受光基线，未重烘新颜色的间接反弹；不把此次局部结果当成整室已完成返修。</p>
<script>const view=document.getElementById('view'),pose=document.getElementById('pose');function refresh(){for(let n=1;n<=3;n++){const img=document.getElementById('mode'+n);img.src='evidence/'+n+'_'+view.value+'_'+pose.value+'.png';img.parentElement.href=img.src;}}view.onchange=pose.onchange=refresh;refresh();</script></html>'''
(EXP/'preview.html').write_text(html.replace('PIXELLAB_USAGE',str(int(usage))),encoding='utf-8')
print('R20_PREVIEW_BUILT')
