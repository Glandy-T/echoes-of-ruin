"""Geometric guide with the actual generated material and preserved footprint."""
from pathlib import Path
from PIL import Image
import numpy as np
HERE=Path(__file__).resolve().parent
base=Image.open(HERE.parent/'raw/base3.png').convert('RGB')
body=Image.open(HERE/'canonical_footprint.png').convert('L')
base.paste((37,57,67),mask=body)
base.save(HERE/'guide_leak_d.png')
mask=np.array(Image.open(HERE/'mask_leak_b.png').convert('L'))
y,x=np.indices(mask.shape)
mask[(x>88)|(y<115)]=0
Image.fromarray(mask).save(HERE/'mask_leak_d.png')
prompt='''Top-down flat PIXEL ART texture edit. A worn cool blue-gray mineral composite floor is already present; preserve it and the central dark occupied pod footprint. Within the white mask beside its LOWER LEFT edge create an old dried coolant seep connected directly to the pod contact. Irregular elongated low-contrast cool dark blue-gray discolored coating with smaller finely pixelated fragments, tapering away from the base. Several tonal layers of residue and a fine fragmented faded dry tide edge. Existing floor texture should show through. The patch is about 16-28 pixels wide and 60 pixels long. Use the existing cool floor colors, avoid the pod's darkest color for heavy outlining. This is flat aged material, not an object or a hole. No circular puddles, closed dark outlines, gloss, glow, yellow, brown, large hard blocks or added equipment.'''
(HERE/'prompt_leak_d.txt').write_text(prompt,encoding='utf-8')
