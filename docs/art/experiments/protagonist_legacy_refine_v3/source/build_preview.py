"""Validate original PixelLab pixels and assemble review layouts; never paint art."""
from pathlib import Path
from hashlib import sha256
import json
import shutil
import struct
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
raw_path = ROOT / 'raw/front.png'
raw = Image.open(raw_path).convert('RGBA')
readback = Image.open(ROOT / 'evidence/aseprite_readback.png').convert('RGBA')
assert raw.size == (96, 128) and readback.size == raw.size
assert raw.getchannel('A').tobytes() == readback.getchannel('A').tobytes()
mismatches = sum(a != b for a, b in zip(raw.getdata(), readback.getdata()) if a[3])
assert mismatches == 0
shutil.copyfile(raw_path, ROOT / 'front_candidate.png')
raw.resize((384, 512), Image.Resampling.NEAREST).save(ROOT / 'evidence/candidate_4x.png')
font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 21)
small = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 15)
sources = [
    (ROOT / 'source/legacy_identity.png', '旧主角 · 身份参考', '保持发型与白袍，不沿用大头比例'),
    (ROOT / 'source/adult_v2_original.png', '上一轮 v2 · 偏细长', '96×160／可见147像素'),
    (raw_path, '本轮 v3 · 紧凑粗像素', '96×128／PixelLab重新绘制'),
]
canvas = Image.new('RGB', (1080, 570), '#273033')
draw = ImageDraw.Draw(canvas)
for i, (path, title, caption) in enumerate(sources):
    image = Image.open(path).convert('RGBA')
    figure = image.crop(image.getbbox())
    figure = figure.resize((round(figure.width * 416 / figure.height), 416), Image.Resampling.NEAREST)
    canvas.paste(figure, (360*i+(360-figure.width)//2, 78), figure)
    draw.text((360*i+18, 14), title, font=font, fill='#e4ece8')
    draw.text((360*i+18, 48), caption, font=small, fill='#b8cbc4')
draw.text((20, 529), '人物等可见高度，仅比较比例与画法；实际游戏尺度见下方Godot截图。', font=small, fill='#bacbc5')
canvas.save(ROOT / 'evidence/identity_comparison.png')
binary = (ROOT / 'editable/front_candidate.aseprite').read_bytes()
count = struct.unpack_from('<H', binary, 134)[0]
offset = 144
layers = []
for _ in range(count):
    size, kind = struct.unpack_from('<IH', binary, offset)
    data = binary[offset+6:offset+size]
    if kind == 0x2004:
        flags = struct.unpack_from('<H', data)[0]
        length = struct.unpack_from('<H', data, 16)[0]
        layers.append({'name': data[18:18+length].decode('utf8'), 'visible': bool(flags & 1)})
    offset += size
assert len(layers) == 4
assert all(not x['visible'] for x in layers if x['name'].endswith('_hidden'))
report = {
    'raw_native_size': list(raw.size),
    'visible_rgb_colours': len({p[:3] for p in raw.getdata() if p[3]}),
    'alpha_values': sorted(set(raw.getchannel('A').getdata())),
    'visible_bounds': list(raw.getbbox()),
    'visible_height_pixels': raw.getbbox()[3]-raw.getbbox()[1],
    'raw_sha256': sha256(raw_path.read_bytes()).hexdigest(),
    'final_png_byte_identical_to_raw': raw_path.read_bytes() == (ROOT/'front_candidate.png').read_bytes(),
    'aseprite_visible_pixel_mismatches': mismatches,
    'aseprite_alpha_exact': True, 'aseprite_layers': layers,
    'local_painted_pixels': 0, 'user_visual_review': 'pending',
    'not_verified': ['final design approval', 'side/back views', '3D mesh/rig/UV', 'final 3D lighting'],
}
(ROOT / 'source/validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
record = json.loads((ROOT/'source/generation_record.json').read_text(encoding='utf8'))
record.update(status='generated_game_context_review_pending', raw_sha256=report['raw_sha256'], actual_canvas=report['raw_native_size'], actual_visible_height=report['visible_height_pixels'], actual_visible_rgb_colours=report['visible_rgb_colours'])
(ROOT/'source/generation_record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
