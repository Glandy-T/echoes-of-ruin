from pathlib import Path
import sys
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parent.parent
old=p.parent/'protagonist_r5_pixel_skin_v1'
sys.path.insert(0,str(old/'source'))
from model import Model
m=Model(old/'walk_pixel.glb')
face=m.faces()
uv=m.attribute('TEXCOORD_0')[face]*128
xyz=m.attribute('POSITION')[face]
points={}
for t,w in zip(uv,xyz):
    if t[:,0].min()>24 or t[:,1].max()<15 or t[:,1].min()>40 or w[:,1].min()<.78:continue
    for y in range(max(0,int(t[:,1].min())),min(40,int(t[:,1].max())+1)):
        for x in range(max(0,int(t[:,0].min())),min(24,int(t[:,0].max())+1)):
            v=(np.array([x+.5,y+.5])-t[0])@np.linalg.inv((t[1:]-t[0]).astype(float))
            if min(v)>=0 and sum(v)<=1:points[x,y]=w[0]+v@(w[1:]-w[0])
if __name__=='__main__':
    im=Image.open(old/'skin.png').convert('RGB')
    for y in range(17,36):
        print(y,' '.join(f'{x}:{q[1]:.3f}/{-q[2]:+.3f}' for (x,yy),q in sorted(points.items()) if yy==y and x%3==0))
