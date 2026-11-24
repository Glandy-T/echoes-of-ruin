from pathlib import Path
from PIL import Image,ImageDraw
import json
s=Path(__file__).resolve().parent
e=s.parent.parent
q=e/'protagonist_l2_front_silhouette_v1'
g=json.loads((q/'source/shape_record.json').read_text())['old_geometry']
a=Image.open(q/'front_silhouette.png').getchannel('A')
t=Image.open(e/'protagonist_l2_front_twotone_v1/front_twotone.png')
cloth=Image.open(q/'source/parts/gown_A_line.png').getchannel('A')
d=ImageDraw.Draw(cloth)
for pts in [g['sleeve'],[(128-x,y) for x,y in g['sleeve']]]:d.polygon(list(map(tuple,pts)),fill=255)
cloth.save(s/'cloth.png')
