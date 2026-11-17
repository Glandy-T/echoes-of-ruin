"""Review packaging only: never paints or resamples the production PNG."""
from pathlib import Path
from hashlib import sha256
import json
import shutil
from PIL import Image, ImageDraw, ImageFont, ImageChops

HERE = Path(__file__).resolve().parent.parent
raw_path = HERE / 'raw/front.png'
raw = Image.open(raw_path).convert('RGBA')
readback = Image.open(HERE / 'evidence/aseprite_readback.png').convert('RGBA')
guide = Image.open(HERE / 'source/legacy_reference_2x_GUIDE.png').convert('RGBA')
legacy = Image.open(HERE / 'source/legacy_idle_frame.png').convert('RGBA')
assert raw.size == (192, 256) and readback.size == raw.size
assert guide.tobytes() == legacy.resize(raw.size, Image.Resampling.NEAREST).tobytes()
assert raw.tobytes() != guide.tobytes(), 'A guide enlargement is not a generated redraw'
assert raw.getchannel('A').tobytes() == readback.getchannel('A').tobytes()
visible_mismatches = sum(a != b for a, b in zip(raw.getdata(), readback.getdata()) if a[3])
assert visible_mismatches == 0
shutil.copyfile(raw_path, HERE / 'front_candidate.png')
font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 22)
small = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 15)
canvas = Image.new('RGB', (1080, 570), '#273033')
draw = ImageDraw.Draw(canvas)
columns = [
    ('source/legacy_idle_frame.png', '原来的主角', '形象基准 · 游戏内一直沿用'),
    ('source/previous_realistic_front_v2.png', '后来偏写实的一版', '历史对照 · 不作为本轮外形输入'),
    ('raw/front.png', '本轮 PixelLab 试稿', '旧形象为输入 · 192×256 原生输出'),
]
for index, (file, title, caption) in enumerate(columns):
    image = Image.open(HERE / file).convert('RGBA')
    figure = image.crop(image.getbbox())
    scale = 416 / figure.height
    figure = figure.resize((round(figure.width * scale), 416), Image.Resampling.NEAREST)
    canvas.paste(figure, (360 * index + (360 - figure.width) // 2, 77), figure)
    draw.text((360 * index + 20, 15), title, font=font, fill='#e4ece8')
    draw.text((360 * index + 20, 48), caption, font=small, fill='#abbdb6')
draw.text((22, 526), '仅将可见人物等高排列，便于看形象；显示缩放不代表三张素材的原生密度一致。', font=small, fill='#bacbc5')
canvas.save(HERE / 'evidence/identity_comparison.png')
raw.resize((384, 512), Image.Resampling.NEAREST).save(HERE / 'evidence/candidate_2x.png')
report = {
    'raw_native_size': list(raw.size),
    'visible_rgb_colours': len({pixel[:3] for pixel in raw.getdata() if pixel[3]}),
    'alpha_values': sorted(set(raw.getchannel('A').getdata())),
    'visible_bounds': list(raw.getbbox()),
    'raw_sha256': sha256(raw_path.read_bytes()).hexdigest(),
    'final_png_byte_identical_to_raw': raw_path.read_bytes() == (HERE / 'front_candidate.png').read_bytes(),
    'guide_exact_2x_nearest_reference_only': True,
    'output_is_not_unchanged_guide': True,
    'aseprite_visible_pixel_mismatches': visible_mismatches,
    'aseprite_alpha_exact': True,
    'local_painted_pixels': 0,
    'user_visual_review': 'pending',
    'not_verified': ['strict orthographic modeling reference', 'final proportions', 'side/back views', '3D/rig/UV', 'Godot character replacement'],
}
(HERE / 'source/validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
html = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>旧主角形象精修候选</title><style>body{margin:24px auto;padding:0 20px;max-width:1120px;background:#1c2528;color:#e0e8e4;font:16px/1.7 system-ui}a{color:#a8dcd5}img{max-width:100%;height:auto}.pixel{image-rendering:pixelated}figure{margin:22px 0}.native{background:#273033;padding:24px;display:inline-block}h1{font-size:25px}</style>
<h1>旧主角形象精修 · 一张待审正面</h1>
<p>2026-11-17。身份参考回到游戏一直沿用的旧精灵；PixelLab 官网 Pro 重绘。没有替换游戏角色或继续3D制作。</p>
<p><a href="README.md">制作说明</a> · <a href="front_candidate.png">原生PNG</a> · <a href="editable/front_candidate.aseprite">Aseprite母版</a> · <a href="source/generation_record.json">来源／实扣</a></p>
<figure><img src="evidence/identity_comparison.png" alt="旧主角、写实历史稿、本轮新稿的等高对比"><figcaption>等高排列仅用于比较形象与画法，不代表原生密度相同。</figcaption></figure>
<p>保留蓝黑长发、柔和脸部、宽松浅色休眠服。仍待确认：风格化比例是否合适、袍长偏长、脸部略侧转和眼部信息量。尚非最终建模图。</p>
<figure class="native"><img class="pixel" src="front_candidate.png" width="192" height="256" alt="192×256原生候选"><figcaption>原生1倍</figcaption></figure>
<figure class="native"><img class="pixel" src="front_candidate.png" width="384" height="512" alt="仅显示最近邻2倍"><figcaption>最近邻2倍显示</figcaption></figure>
<p>一次生成消耗10，账户36→46／2,000，剩1,954；重置／续费显示12月13日。主体没有手绘修改。</p>
<figure><img src="evidence/pixellab_result.jpg" alt="PixelLab官网实际结果"><figcaption>实际官网结果和设置。</figcaption></figure></html>'''
(HERE / 'preview.html').write_text(html + '\n', encoding='utf8')
markdown = '''# 旧主角形象精修候选

2026-11-17，待用户审查。旧精灵为身份输入，PixelLab 官网 Edit image Pro 一次生成，192×256／32色。没有改模型或正式游戏角色。

![三版等高比较](evidence/identity_comparison.png)

[原生PNG](front_candidate.png) · [Aseprite母版](editable/front_candidate.aseprite) · [制作说明](README.md) · [来源和用量](source/generation_record.json)

待审：保留旧角色的感觉是否到位、风格化比例、袍长偏长、脸部略侧转与眼部信息量。原生画布不是未来3D纹素规格。

![原始试稿](front_candidate.png)
'''
(HERE / 'preview.md').write_text(markdown.rstrip() + '\n', encoding='utf8')
print(json.dumps(report, ensure_ascii=False))
