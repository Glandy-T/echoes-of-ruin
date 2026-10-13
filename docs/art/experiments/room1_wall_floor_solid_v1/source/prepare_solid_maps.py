"""Create strict one-color maps, separate from the AI connection test image."""
from pathlib import Path
from PIL import Image
import json

ROOT=Path(__file__).resolve().parents[1]
COLORS={'wall':(211,212,198),'floor':(90,108,115)}
# Palette samples from accepted pod v2. Trial values, not project standards.
for name,rgb in COLORS.items():
    p=ROOT/'textures'/f'{name}_solid.png'
    p.parent.mkdir(parents=True,exist_ok=True)
    Image.new('RGB',(32,32),rgb).save(p)
(ROOT/'colors.json').write_text(json.dumps({
    'status':'temporary solid-color architecture trial',
    'source':'accepted pod v2 lid dominant ivory / slate colors',
    'colors':COLORS,'dimensions':[32,32],
    'pixel_density':'not meaningful for constant maps; no global parameter locked',
    'authorship':'deterministic original solid maps; not AI output',
},indent=2),encoding='utf-8')
