"""Package existing PixelLab pixels and prepare proportional review displays."""
from pathlib import Path
from hashlib import sha256
import json
import shutil
import struct
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent.parent
raw_path = HERE / 'raw/front.png'
raw = Image.open(raw_path).convert('RGBA')
readback = Image.open(HERE / 'evidence/aseprite_readback.png').convert('RGBA')
assert raw.size == (96, 160) and readback.size == raw.size
assert raw.getchannel('A').tobytes() == readback.getchannel('A').tobytes()
visible_mismatches = sum(a != b for a, b in zip(raw.getdata(), readback.getdata()) if a[3])
assert visible_mismatches == 0
shutil.copyfile(raw_path, HERE / 'front_candidate.png')
font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 21)
small = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 15)
canvas = Image.new('RGB', (1080, 570), '#273033')
draw = ImageDraw.Draw(canvas)
columns = [
    ('source/legacy_identity.png', '旧主角 · 身份参考', '只取发型、白袍和配色'),
    ('source/rejected_big_head_v1.png', '上一张 · 头太大', '已否决，不作为生成输入'),
    ('raw/front.png', '本轮 · 成人比例试稿', 'PixelLab原生96×160／24色'),
]
for index, (file, title, caption) in enumerate(columns):
    image = Image.open(HERE / file).convert('RGBA')
    figure = image.crop(image.getbbox())
    scale = 416 / figure.height
    figure = figure.resize((round(figure.width * scale), 416), Image.Resampling.NEAREST)
    canvas.paste(figure, (360 * index + (360 - figure.width) // 2, 77), figure)
    draw.text((360 * index + 20, 15), title, font=font, fill='#e4ece8')
    draw.text((360 * index + 20, 48), caption, font=small, fill='#abbdb6')
draw.text((22, 526), '可见人物等高排列，仅比较比例和画法；不代表原生像素密度相同。', font=small, fill='#bacbc5')
canvas.save(HERE / 'evidence/identity_comparison.png')
raw.resize((384, 640), Image.Resampling.NEAREST).save(HERE / 'evidence/candidate_4x.png')
# A second view holds one source pixel to the same four display pixels.
native = Image.new('RGB', (900, 720), '#273033')
nd = ImageDraw.Draw(native)
for index, (file, title) in enumerate([('source/legacy_identity.png', '旧精灵原生96×128'), ('raw/front.png', '本轮原生96×160')]):
    figure = Image.open(HERE / file).convert('RGBA')
    figure = figure.resize((figure.width * 4, figure.height * 4), Image.Resampling.NEAREST)
    native.paste(figure, (30 + index * 440, 45), figure)
    nd.text((30 + index * 440, 10), title, font=small, fill='#e4ece8')
nd.text((30, 692), '两张均为整数4倍显示，一个原生像素对应4×4显示像素。', font=small, fill='#bacbc5')
native.save(HERE / 'evidence/native_grid_comparison.png')
binary = (HERE / 'editable/front_candidate.aseprite').read_bytes()
chunk_count = struct.unpack_from('<H', binary, 134)[0]
offset = 144
layers = []
for _ in range(chunk_count):
    size, kind = struct.unpack_from('<IH', binary, offset)
    data = binary[offset + 6:offset + size]
    if kind == 0x2004:
        flags = struct.unpack_from('<H', data)[0]
        length = struct.unpack_from('<H', data, 16)[0]
        layers.append({'name': data[18:18 + length].decode('utf8'), 'visible': bool(flags & 1)})
    offset += size
assert len(layers) == 4
assert all(not layer['visible'] for layer in layers if layer['name'].endswith('_hidden'))
report = {
    'raw_native_size': list(raw.size),
    'visible_rgb_colours': len({pixel[:3] for pixel in raw.getdata() if pixel[3]}),
    'alpha_values': sorted(set(raw.getchannel('A').getdata())),
    'visible_bounds': list(raw.getbbox()),
    'raw_sha256': sha256(raw_path.read_bytes()).hexdigest(),
    'final_png_byte_identical_to_raw': raw_path.read_bytes() == (HERE / 'front_candidate.png').read_bytes(),
    'aseprite_visible_pixel_mismatches': visible_mismatches,
    'aseprite_alpha_exact': True,
    'aseprite_layers': layers,
    'local_painted_pixels': 0,
    'user_visual_review': 'pending',
    'not_verified': ['final character identity/proportion approval', 'side/back views', '3D/rig/UV', 'Godot replacement'],
}
(HERE / 'source/validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
html = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>主角成人比例像素试稿 v2</title><style>body{margin:24px auto;padding:0 20px;max-width:1120px;background:#1c2528;color:#e0e8e4;font:16px/1.7 system-ui}a{color:#a8dcd5}img{max-width:100%;height:auto}.pixel{image-rendering:pixelated}figure{margin:22px 0}.native{background:#273033;padding:24px;display:inline-block}h1{font-size:25px}</style>
<h1>成人比例像素试稿 v2 · 一张待审正面</h1>
<p>2026-11-17。按用户选定的《武士零》《SIGNALIS》成人比例与像素概括方向，保留旧主角发型和白袍。没有上传第三方作品图像。</p>
<p><a href="README.md">制作说明</a> · <a href="front_candidate.png">原生PNG</a> · <a href="editable/front_candidate.aseprite">Aseprite母版</a> · <a href="source/generation_record.json">来源／实扣</a></p>
<figure><img src="evidence/identity_comparison.png" alt="旧主角、被否决的大头稿、本轮成人比例"><figcaption>可见人物等高，比较头部和身体关系。</figcaption></figure>
<figure class="native"><img class="pixel" src="front_candidate.png" width="96" height="160" alt="96×160原生候选"><figcaption>原生1倍</figcaption></figure>
<figure class="native"><img class="pixel" src="front_candidate.png" width="288" height="480" alt="整数3倍显示"><figcaption>最近邻3倍显示</figcaption></figure>
<figure><img src="evidence/native_grid_comparison.png" alt="两个原生像素网格均整数4倍"><figcaption>此图固定每个原生像素的显示大小，不把不同画布冒称统一纹素密度。</figcaption></figure>
<p>独立试稿：96×160、24色、二值透明。像素主体由PixelLab Pro绘制，没有本地重画。该画布不是未来角色3D贴图密度规格。</p>
<p>两张输入分工：成人比例导图控制头身、肩颈、四肢；旧精灵只作发型和服装身份参考。上一张大头稿不作为输入。用户外观审查、侧背面、3D和动画均未完成。</p>
<figure><img src="evidence/pixellab_result.jpg" alt="PixelLab官网实际结果和设置"></figure></html>'''
(HERE / 'preview.html').write_text(html + '\n', encoding='utf8')
markdown = '''# 主角成人比例像素试稿 v2

2026-11-17，待用户审查。PixelLab官网Pro一次生成；96×160／24色。旧主角提供发型与白袍身份，成人导图提供比例。没有修改正式角色或3D模型。

![等高比例对比](evidence/identity_comparison.png)

[原生PNG](front_candidate.png) · [Aseprite母版](editable/front_candidate.aseprite) · [制作说明](README.md) · [来源与实扣](source/generation_record.json)

![本轮整数4倍显示](evidence/candidate_4x.png)

![原生网格对比](evidence/native_grid_comparison.png)
'''
(HERE / 'preview.md').write_text(markdown.rstrip() + '\n', encoding='utf8')
print(json.dumps(report, ensure_ascii=False))
