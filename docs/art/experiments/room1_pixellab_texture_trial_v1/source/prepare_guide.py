"""Produce a flat color layout guide, not a production texture or AI artwork."""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parent
image = Image.new('RGB', (128, 128), (188, 194, 197))
draw = ImageDraw.Draw(image)
draw.rectangle((16, 18, 25, 21), fill=(185, 191, 194))
draw.rectangle((70, 78, 82, 80), fill=(190, 196, 199))
draw.rectangle((98, 33, 102, 37), fill=(186, 192, 195))
image.save(root / 'wall_color_layout_GUIDE.png')
