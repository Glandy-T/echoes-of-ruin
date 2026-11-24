from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent
reference = Image.open(root.parent / 'protagonist_front_c_raw_v2' / 'B_original.png').convert('RGBA')
reference_array = np.array(reference)
palette = np.unique(reference_array[reference_array[:, :, 3] == 255, :3], axis=0)
angles = (0, 45, 90, 135, 180)
metrics = {'B_palette_colors': len(palette), 'frames': {}}

for angle in angles:
    source = Image.open(root / f'input_{angle}.png').convert('RGBA')
    pixels = np.array(source)
    assert source.size == (128, 128)
    alpha = pixels[:, :, 3]
    assert set(np.unique(alpha)) == {0, 255}
    mask = alpha == 255
    rgb = pixels[mask, :3].astype('int32')
    distance = ((rgb[:, None] - palette.astype('int32')) ** 2).sum(axis=2)
    pixels[mask, :3] = palette[distance.argmin(axis=1)]
    pixels[~mask, :3] = 0
    output = Image.fromarray(pixels)
    output.save(root / f'input_{angle}_Bpalette.png')
    bounds = output.getbbox()
    metrics['frames'][angle] = {
        'bbox': bounds,
        'height': bounds[3] - bounds[1],
        'colors': len(np.unique(pixels[mask, :3], axis=0)),
        'opaque': int(mask.sum()),
    }

font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 15)
sheet = Image.new('RGB', (128 * len(angles), 160), '#343939')
draw = ImageDraw.Draw(sheet)
for index, angle in enumerate(angles):
    image = Image.open(root / f'input_{angle}_Bpalette.png').convert('RGBA')
    sheet.paste(image, (128 * index, 25), image)
    draw.text((128 * index + 64, 4), f'{angle}°', anchor='mt', font=font, fill='white')
sheet.save(root / 'inputs_Bpalette_compare.png')
(root / 'input_metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
print(json.dumps(metrics, indent=2))
