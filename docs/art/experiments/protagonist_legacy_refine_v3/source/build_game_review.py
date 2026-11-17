"""Validate capture consistency and compose explicitly labelled screenshot crops."""
from pathlib import Path
from hashlib import sha256
import json
from PIL import Image, ImageDraw, ImageFont, ImageChops

ROOT = Path(__file__).resolve().parent.parent
GAME = ROOT / 'evidence/game'
record_path = GAME / 'capture_record.json'
record = json.loads(record_path.read_text(encoding='utf8'))
shots = record['shots']
assert len(shots) == 12
for shot in shots:
    old_name = shot['file']
    new_name = old_name.replace('%', 'pct')
    if old_name != new_name:
        (GAME / old_name).rename(GAME / new_name)
        shot['file'] = new_name
record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n',encoding='utf8')
font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 19)
small = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 15)
labels = ['旧占位 · 身份参考', '上一轮 v2 · 相同身高', '本轮 v3 · 相同身高', '本轮 v3 · 身高95%']
checks = []
contact = Image.new('RGB', (1280, 636), '#243034')
draw = ImageDraw.Draw(contact)
for view_index in range(3):
    group = shots[view_index*4:view_index*4+4]
    first = group[0]
    baseline = Image.open(GAME / first['file']).convert('RGB')
    for mode_index, shot in enumerate(group):
        assert shot['viewport'] == [1280, 720]
        assert shot['internal_viewport'] == [1280, 720]
        assert shot['review_camera'] == first['review_camera']
        assert shot['render_camera'] == first['render_camera']
        assert shot['camera_matches_frozen_view']
        assert shot['fov'] == first['fov'] == 50
        image = Image.open(GAME / shot['file']).convert('RGB')
        assert image.size == (1280,720)
        diff = ImageChops.difference(baseline,image)
        bbox = diff.getbbox()
        # Deliberately generous actor-only region, fixed before comparison.
        outside = diff.copy()
        outside.paste((0,0,0),(540,240,740,530))
        assert outside.getbbox() is None, ('Room changed outside actor region',shot['file'])
        checks.append({'file':shot['file'],'image_sha256':sha256((GAME/shot['file']).read_bytes()).hexdigest(),'difference_bounds_vs_legacy':bbox,'outside_character_region_identical':True})
        x,y = mode_index*320,view_index*212
        draw.text((x+6,y+3),labels[mode_index],font=small,fill='#e1ece7')
        contact.paste(image.resize((320,180),Image.Resampling.LANCZOS),(x,y+28))
contact.save(ROOT/'evidence/game_contact_sheet.png')
# Same exact source rectangle for every mode.  Enlargement is display-only.
crop = (560,250,720,510)
closeup = Image.new('RGB',(1280,580),'#243034')
draw = ImageDraw.Draw(closeup)
for mode_index,shot in enumerate(shots[4:8]):
    draw.text((mode_index*320+9,7),labels[mode_index],font=font,fill='#e1ece7')
    image = Image.open(GAME/shot['file']).convert('RGB').crop(crop).resize((320,520),Image.Resampling.NEAREST)
    closeup.paste(image,(mode_index*320,37))
draw.text((12,559),'中央通道实际1280×720截图的同区域裁片，最近邻整数2倍；非改镜头、非另打光。',font=small,fill='#c1d0ca')
closeup.save(ROOT/'evidence/game_closeup_2x.png')
report = {'shots':12,'native_output':[1280,720],'native_internal':[1280,720],'views':3,'modes':4,'same_camera_within_each_view':True,'same_fov':50,'outside_actor_region_exact_same_pixels':True,'actor_region':[540,240,740,530],'closeup_crop':list(crop),'closeup_display_scale':2,'images':checks,'user_visual_approval':'pending','boundary':'Existing paper strip-light approximation; no final 3D mesh lighting validation.'}
(ROOT/'source/game_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
cards = []
for view in range(3):
    rows = []
    for mode,shot in enumerate(shots[view*4:view*4+4]):
        rows.append(f'<figure><figcaption>{labels[mode]}</figcaption><a href="evidence/game/{shot["file"]}"><img src="evidence/game/{shot["file"]}" alt="{labels[mode]}实机截图"></a></figure>')
    cards.append('<h2>'+['左侧通道','中央通道','右侧通道'][view]+'</h2><div class="grid">'+''.join(rows)+'</div>')
html = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>主角粗像素与实机尺度 v3</title>
<style>body{margin:24px auto;padding:0 20px;max-width:1400px;background:#1c2528;color:#dfe9e4;font:16px/1.7 system-ui}a{color:#a9dcd4}img{max-width:100%;height:auto}h1{font-size:26px}h2{font-size:21px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:14px 0}.native{image-rendering:pixelated;background:#273033}.note{color:#b2c5bc}table{border-collapse:collapse}td,th{padding:7px 14px;border:1px solid #586b64}@media(max-width:700px){.grid{grid-template-columns:1fr}}</style>
<h1>主角粗像素／身高对比 v3 · 待审</h1><p>2026-11-17。保留成人小头比例、蓝黑长发和白袍，PixelLab重新概括衣褶与明暗。正式角色与场景没有替换。</p>
<p><a href="README.md">制作记录</a> · <a href="front_candidate.png">原生PNG</a> · <a href="editable/front_candidate.aseprite">分层Aseprite</a> · <a href="source/generation_record.json">来源和额度</a></p>
<h2>先看实际游戏里的区别</h2><p>同一位置先等可见高度比较v2/v3像素画法，再只把v3统一缩小5%。房间镜头、灯光和布局相同。下图为中央机位同区域裁片，最近邻整数2倍；点击后可看原图。</p><a href="evidence/game_closeup_2x.png"><img class="native" src="evidence/game_closeup_2x.png" alt="四种角色在中央通道同区域对比"></a>
<p class="note">角色沿用现有纸片灯带受光近似，并非最终3D模型的受光验收。1.4025与1.3324米是继承测试角色后用于此对比的可见尺寸，不是新设定的主角真实身高。</p>
<table><tr><th>模式</th><th>原生可见高度</th><th>此测试可见高度</th><th>原生像素／米</th></tr><tr><td>旧占位</td><td>96px</td><td>1.4025m</td><td>68.45</td></tr><tr><td>v2等高</td><td>147px</td><td>1.4025m</td><td>104.81</td></tr><tr><td>v3等高</td><td>117px</td><td>1.4025m</td><td>83.42</td></tr><tr><td>v3短5%</td><td>117px</td><td>1.3324m</td><td>87.81</td></tr></table>
<h2>独立画稿</h2><img src="evidence/identity_comparison.png" alt="旧形象、上一稿、本轮等高图"><p>上图仅为人物等高排版，判断比例和绘画处理，不代表原生像素一致。</p><div class="grid"><figure><img class="native" src="front_candidate.png" width="96" height="128" alt="原生一倍"><figcaption>96×128原生1倍；可见人物117像素高／16色。</figcaption></figure><figure><img class="native" src="front_candidate.png" width="384" height="512" alt="整数四倍"><figcaption>最近邻整数4倍显示。</figcaption></figure></div>
<h2>完整实机截图</h2><p>全部1280×720，图片可点击打开原生尺寸。每组只换纸片素材及其统一缩放，图中角色区域以外像素完全相同。</p>'''+''.join(cards)+'''<h2>PixelLab实际结果</h2><img src="evidence/pixellab_result.jpg" alt="PixelLab网站完成结果"><p>共两次Pro请求，第一张大头稿已隔离否决，第二次锁定成人比例；56→76／2000，实扣20。没有上传任何第三方作品图片，没有本地绘画改像素。</p></html>'''
(ROOT/'preview.html').write_text(html+'\n',encoding='utf8')
(ROOT/'preview.md').write_text('# 主角粗像素与实机尺度 v3\n\n[制作记录](README.md) · [并排对比页](preview.html) · [分层Aseprite](editable/front_candidate.aseprite)\n\n![游戏同区域整数2倍](evidence/game_closeup_2x.png)\n\n![等高形象比较](evidence/identity_comparison.png)\n\n实际截图为1280×720；上方裁片只作整数2倍查看。正式角色、场景与3D没有替换。\n',encoding='utf8')
print('Validated 12 Godot captures; same camera and identical room pixels outside actor region.')
