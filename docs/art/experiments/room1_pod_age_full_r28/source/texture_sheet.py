"""Diagnostic nearest enlargement only; never used as runtime material."""
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4];TARGET=ROOT/'assets/art/room1_pod_age_full_r28'
sheet=Image.new('RGB',(900,790),(29,41,43));d=ImageDraw.Draw(sheet)
for col,v in enumerate('abcd'):
 x=12+col*222;d.text((x,10),v.upper()+(' approved r27' if v=='a' else ' new PixelLab'),fill=(221,233,227))
 im=Image.open(TARGET/f'variant_{v}'/'lid.png').convert('RGB');sheet.paste(im.resize((192,368),Image.Resampling.NEAREST),(x,30))
 if v!='d':
  im=Image.open(TARGET/f'variant_{v}'/'shell_end.png').convert('RGB');sheet.paste(im.resize((192,112),Image.Resampling.NEAREST),(x,415))
 else:d.text((x,445),'3 accepted end maps: A/B/C',fill=(221,233,227))
for row,v in enumerate('abcd'):
 im=Image.open(TARGET/f'variant_{v}'/'shell_side.png').convert('RGB');d.text((12,550+row*58),v.upper(),fill=(221,233,227));sheet.paste(im,(40,550+row*58))
sheet.save(EXP/'evidence/native_variation_sheet.png');print('R28_VARIATION_INSPECTION_SHEET')
