from pathlib import Path
from PIL import Image
import json,subprocess
p=Path(__file__).resolve().parents[1]
raw=Image.open(p/'raw/master.png').convert('RGBA')
mask=Image.open(p.parent/'protagonist_l2_front_silhouette_v1/front_silhouette.png').convert('RGBA').getchannel('A')
cloth=Image.open(p/'source/cloth.png').convert('L')
def runs(xs):
 out=[]
 for x in xs:
  if not out or x!=out[-1][-1]+1:out.append([])
  out[-1].append(x)
 return out
def line(im,y):
 return runs([x for x in range(128) if im.getpixel((x,y))>127])
src=raw.getchannel('A')
diff=sum(a!=b for a,b in zip(mask.getdata(),src.getdata()))
body=Image.new('RGB',(128,128));gown=body.copy();colors=[None]
landmarks=[(6,3),(25,25),(29,28),(44,43),(76,74),(86,86),(87,88),(117,121),(122,127)]
for y in range(6,123):
 for (a,b),(c,d) in zip(landmarks,landmarks[1:]):
  if a<=y<=c:
   sy=round(b+(d-b)*(y-a)/(c-a));break
 dest=line(mask,y); orig=line(src,sy)
 if len(dest)!=len(orig):
  options=[j for j in range(max(3,sy-3),min(128,sy+4)) if len(line(src,j))==len(dest)]
  if options:sy=min(options,key=lambda j:abs(j-sy));orig=line(src,sy)
 for i,grp in enumerate(dest):
  row=orig[i] if len(orig)==len(dest) else min(orig,key=lambda r:abs(sum(r)/len(r)-sum(grp)/len(grp)))
  for k,x in enumerate(grp):
   sx=row[round(k*(len(row)-1)/max(1,len(grp)-1))]
   color=raw.getpixel((sx,sy))[:3]
   iscloth=bool(cloth.getpixel((x,y)))
   skin=color[0]>color[1]+9
   if 6<=y<=25:
    sx=round(64+(x-64)*1.20)
    sy2=round(3+(y-6)*21/19)
    sample=raw.getpixel((sx,sy2))
    color=sample[:3] if sample[3] else (49,59,58)
   if 26<=y<=32 and not iscloth:
    color=(197,168,145) if 61<=x<=67 else (49,59,58)
   if iscloth and skin:
    color=(216,218,213) if x<=69 else (177,181,174)
   if iscloth and max(color)<110:color=(128,144,140)
   if y>=43 and not iscloth and not skin:
    color=(197,168,145) if x<64 else (153,128,123)
   key=(iscloth,color)
   if key not in colors:colors.append(key)
   idx=colors.index(key)
   (gown if iscloth else body).putpixel((x,y),(idx,idx,idx))
for name,im in [('body',body),('gown',gown)]:im.save(p/(name+'_index.png'))
for v in 'AB':
 palette=[(0,0,0)]
 for iscloth,rgb in colors[1:]:
  if iscloth and rgb in [(216,218,213),(177,181,174),(139,142,135)]:
   rgb=dict(A={(216,218,213):(225,223,215),(177,181,174):(182,181,173),(139,142,135):(144,145,138)},B={(216,218,213):(231,223,207),(177,181,174):(190,182,167),(139,142,135):(150,145,135)})[v][rgb]
  palette.append(rgb)
 (p/f'palette_{v}.gpl').write_text('GIMP Palette\nName: Gown '+v+'\nColumns: 8\n#\n'+''.join('%d %d %d slot%d\n'%(*rgb,i) for i,rgb in enumerate(palette)))
print('raw alpha diff',diff)
subprocess.run(['C:/文件类/Aseprite/Aseprite/aseprite.exe','-b','--script-param','root='+p.as_posix(),'--script',str(p/'source/export.lua')],check=True)
