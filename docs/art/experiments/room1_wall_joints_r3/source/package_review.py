from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def pair(title,a,b,ca='r2 · 无模块接缝',cb='r3 · 宽幅模块接缝'):
    return f'<h2>{title}</h2><div class="pair"><figure><a href="evidence/{a}.png"><img src="evidence/{a}.png"></a><figcaption>{ca}</figcaption></figure><figure><a href="evidence/{b}.png"><img src="evidence/{b}.png"></a><figcaption>{cb}</figcaption></figure></div>'
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Room 1 · 墙面模块接缝 r3</title><style>body{margin:0;background:#202828;color:#e2e5da;font:16px/1.65 system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:28px}h1{font-size:27px}h2{font-size:21px;margin-top:30px}p{color:#c6cec7}a{color:#afd1d4}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}figure{margin:0}img{width:100%;display:block}figcaption{padding:7px 0}.note{background:#2d3835;border-left:3px solid #b5c8ba;padding:12px 16px}@media(max-width:850px){.pair{grid-template-columns:1fr}}</style><main><h1>Room 1 / 墙面模块接缝 r3 · 待审</h1><p>按最新要求增加可读的装配结构。两条纵向拼接缝，间距约1.6m；暗芯、内收阴影与倒角亮边用独立像素层表达。</p><p><a href="README.md">制作与验证</a> · <a href="editable/wall_joints_r3.aseprite">分层Aseprite</a> · <a href="../../../../scenes/dev/room1_wall_joints_r3.tscn">Godot场景</a> · <a href="../room1_surface_structure_r2/preview.html">r2保留</a></p><p class="note">以下均为实际Godot截图；原镜头、曝光、照明和地面相同，仅墙面接缝有变化。纯颜色图单独标明，不代表正式照明。接缝停在灯槽和保护带边界，不切断发光面。</p>'''
html+=pair('实际游戏镜头 · 原应急光照','game_r2_lit','game_r3_lit')
html+=pair('技术近景 · 同照明','technical_r2_lit','technical_r3_lit')
html+=pair('技术近景 · Base Color检查','technical_r2_base_color','technical_r3_base_color','r2 / Base Color','r3 / Base Color')
html+=pair('实际游戏镜头 · Base Color检查','game_r2_base_color','game_r3_base_color','r2 / Base Color','r3 / Base Color')
html+=pair('原生像素图 · 最近邻3倍显示','wall_r2_native_3x','wall_r3_native_3x')
html+='<h2>全室回归 · 13机位</h2><div class="pair">'
for file in sorted((ROOT/'survey').glob('*.png')):
    html+=f'<figure><a href="survey/{file.name}"><img loading="lazy" src="survey/{file.name}"></a><figcaption>{file.stem}</figcaption></figure>'
html+='</div></main></html>'
(ROOT/'preview.html').write_text(html,encoding='utf-8')
print('Actual r2/r3 wall-joint review page saved.')
