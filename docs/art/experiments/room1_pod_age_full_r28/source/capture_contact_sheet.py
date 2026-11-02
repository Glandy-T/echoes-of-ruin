"""Inspection thumbnails derived from final actual GPU captures, not game assets."""
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
sheet=Image.new('RGB',(1280,1000),(22,31,33));d=ImageDraw.Draw(sheet)
for i in range(20):
 pid=f'P{i+1:02d}';path=EXP/'evidence'/f'2_pod_{pid.lower()}_exterior_closed.png';assert path.is_file()
 im=Image.open(path).convert('RGB');im.thumbnail((320,180));x=(i%4)*320;y=(i//4)*200
 d.text((x+8,y+3),pid,fill=(226,235,229));sheet.paste(im,(x,y+20))
sheet.save(EXP/'evidence/pod_contact_sheet.png');print('R28_CONTACT_SHEET20finalGPUviews')
