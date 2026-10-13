"""Technical planar lid color guide; not a finished production texture."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
im = Image.new('RGB', (128, 256), '#c4cbce')
d = ImageDraw.Draw(im)
d.rectangle((12, 0, 115, 255), fill='#d8dddc')
d.rectangle((23, 0, 104, 255), fill='#e1e4df')
d.rectangle((12, 225, 115, 255), fill='#a5b0b5')
im.save(ROOT / 'lid_planar_color_GUIDE.png')
