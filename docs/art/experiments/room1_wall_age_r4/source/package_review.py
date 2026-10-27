from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def pair(title,a,b,ca='r3 · 原轻旧化',cb='r4 · 中等强度旧化'):
    return f'<h2>{title}</h2><div class="pair"><figure><a href="evidence/{a}.png"><img src="evidence/{a}.png"></a><figcaption>{ca}</figcaption></figure><figure><a href="evidence/{b}.png"><img src="evidence/{b}.png"></a><figcaption>{cb}</figcaption></figure></div>'
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Room 1 · 中等强度墙面旧化 r4</title><style>body{margin:0;background:#202828;color:#e2e5da;font:16px/1.65 system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:28px}h1{font-size:27px}h2{font-size:21px;margin-top:30px}p{color:#c6cec7}a{color:#afd1d4}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}figure{margin:0}img{width:100%;display:block}figcaption{padding:7px 0}.note{background:#2d3835;border-left:3px solid #b5c8ba;padding:12px 16px}@media(max-width:850px){.pair{grid-template-columns:1fr}}</style><main><h1>Room 1 / 墙面旧化 r4 · 中等强度候选</h1><p>保留用户认可的r3装配缝，以Pixel Canals实际观察到的沿边连片色块、阶梯轮廓和主面留白组织旧化。提高可见度，同时减小参考中室外侵蚀的覆盖范围。</p><p><a href="README.md">制作与验证</a> · <a href="editable/wall_age_r4.aseprite">五层Aseprite</a> · <a href="../../../../scenes/dev/room1_wall_age_r4.tscn">Godot场景</a> · <a href="../room1_wall_joints_r3/preview.html">r3保留</a></p><p class="note">以下为实际Godot图：原照明、同曝光、同机位，仅墙面旧化改变。Base Color单独标明，不以增亮截图代替材质效果。接缝和发光面像素保持原样。</p>'''
html+=pair('原游戏机位 · 实际应急光照','game_r3_lit','game_r4_lit')
html+=pair('技术近景 · 同照明','technical_r3_lit','technical_r4_lit')
html+=pair('技术近景 · Base Color检查','technical_r3_base_color','technical_r4_base_color','r3 / Base Color','r4 / Base Color')
html+=pair('原游戏机位 · Base Color检查','game_r3_base_color','game_r4_base_color','r3 / Base Color','r4 / Base Color')
html+=pair('原生像素图 · 最近邻3倍显示','wall_r3_native_3x','wall_r4_native_3x')
html+='<h2>全室回归 · 13机位</h2><div class="pair">'
for file in sorted((ROOT/'survey').glob('*.png')):
    html+=f'<figure><a href="survey/{file.name}"><img loading="lazy" src="survey/{file.name}"></a><figcaption>{file.stem}</figcaption></figure>'
html+='</div></main></html>'
(ROOT/'preview.html').write_text(html,encoding='utf-8')
print('Original-exposure aging comparison page saved.')
