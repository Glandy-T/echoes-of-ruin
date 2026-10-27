"""Package actual Godot captures without changing or enhancing their pixels."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def pair(title,a,b,ca='r4原材质',cb='r2局部结构贴图'):
    return f'<section><h2>{title}</h2><div class="pair"><figure><a href="evidence/{a}.png"><img src="evidence/{a}.png"></a><figcaption>{ca}</figcaption></figure><figure><a href="evidence/{b}.png"><img src="evidence/{b}.png"></a><figcaption>{cb}</figcaption></figure></div></section>'

html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Room 1 · 局部结构像素 r2</title><style>
body{margin:0;background:#202828;color:#e2e5da;font:16px/1.65 system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:28px}h1{font-size:28px}h2{font-size:21px;margin-top:32px}p{color:#c5cec6}a{color:#afd1d4}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}figure{margin:0}img{display:block;width:100%;height:auto}figcaption{padding:7px 0}.note{border-left:3px solid #a9bcb4;padding:12px 16px;background:#2d3835}.native{image-rendering:pixelated}.links{display:flex;gap:18px;flex-wrap:wrap}@media(max-width:850px){.pair{grid-template-columns:1fr}}</style><main>
<h1>Room 1 / 局部结构像素 r2 · 待审</h1><p>按 Pixel Canals 的实际观察组织结构明暗与材质像素层。仅替换左墙3.2m及相邻3.2×3.2m地坪，模型、布局、游戏镜头及r4照明保持。</p>
<p class="links"><a href="README.md">来源与限制</a><a href="../../../../scenes/dev/room1_surface_structure_r2.tscn">独立Godot场景</a><a href="editable/wall_structure_r2.aseprite">墙面Aseprite</a><a href="editable/floor_structure_r2.aseprite">地面Aseprite</a><a href="../room1_surface_full_room_r1/preview.html">上轮整室候选</a></p>
<p class="note">本页所有3D图均为实际Godot截图，未调曝光或后期增强。技术近景用于检查表面，不是新游戏镜头；Base Color只用于隔离贴图贡献。新图的间接反射未重烘焙，当前仍是局部美术候选。</p>'''
html+=pair('技术近景 · 原应急照明','technical_baseline','technical_both')
html+=pair('技术近景 · 纯颜色基线','technical_baseline_base_color','technical_both_base_color','r4原材质 / Base Color','r2局部贴图 / Base Color')
html+=pair('原游戏机位 · 同照明、同曝光','game_00_baseline','game_03_both')
html+=pair('原游戏机位 · 纯颜色基线','game_baseline_base_color','game_04_both_base_color','r4原材质 / Base Color','r2局部贴图 / Base Color')
html+='''<h2>原生像素图 · 最近邻3倍显示</h2><div class="pair"><figure><a href="evidence/wall_native_3x.png"><img class="native" src="evidence/wall_native_3x.png"></a><figcaption>墙面256×272：暖灰主面、连续灯槽与下沿金属保护带；没有新增竖向面板缝</figcaption></figure><figure><a href="evidence/floor_native_3x.png"><img class="native" src="evidence/floor_native_3x.png"></a><figcaption>地坪256×256：统一蓝灰、硬边材料簇；仅实际墙边有轻微接触收口</figcaption></figure></div><h2>全室回归检查 · 13机位</h2><p>局部以外继续使用r4原材质；技术检查真正显示前墙，两个总览覆盖20舱。截图不代表用户美术认可。</p><div class="pair">'''
for file in sorted((ROOT/'survey').glob('*.png')):
    html+=f'<figure><a href="survey/{file.name}"><img loading="lazy" src="survey/{file.name}"></a><figcaption>{file.stem}</figcaption></figure>'
html+='</div></main></html>'
(ROOT/'preview.html').write_text(html,encoding='utf-8')
print('Review page links actual unmodified captures.')
