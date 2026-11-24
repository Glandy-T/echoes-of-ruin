from pathlib import Path
from collections import deque
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

out = Path(__file__).resolve().parent
views = [('front','正面','protagonist_front_c_raw_v2/B_original.png'),
         ('right','右侧','protagonist_side_eye_v4/side.png'),
         ('back','背面','protagonist_back_v1/back.png')]
palette = [(69,78,72),(234,193,157),(231,223,207)]
scale = 8

def simplify(points, tol):
    a,b = points[0],points[-1]
    dx,dy = b[0]-a[0],b[1]-a[1]
    distances = []
    for x,y in points:
        t = max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy or 1)))
        distances.append(math.hypot(x-a[0]-t*dx,y-a[1]-t*dy))
    k = int(np.argmax(distances))
    if distances[k] <= tol:
        return [a,b]
    return simplify(points[:k+1],tol)[:-1]+simplify(points[k:],tol)

def smooth_mask(mask):
    edges = {}
    for y,x in zip(*np.where(mask)):
        x,y=int(x),int(y)
        for a,b in [((x,y),(x+1,y)),((x+1,y),(x+1,y+1)),((x+1,y+1),(x,y+1)),((x,y+1),(x,y))]:
            if (b,a) in edges: del edges[b,a]
            else: edges[a,b] = True
    links = {}
    for a,b in edges: links.setdefault(a,[]).append(b)
    paths=[]
    while links:
        a=next(iter(links)); path=[a]
        while True:
            b=links[a].pop()
            if not links[a]: del links[a]
            if b==path[0]: break
            path.append(b); a=b
        pts=np.asarray(path)
        area=np.sum(pts[:,0]*np.roll(pts[:,1],-1)-pts[:,1]*np.roll(pts[:,0],-1))/2
        if abs(area)<2: continue
        # Average along the perimeter to round one-pixel ledges on long limbs.
        weights=np.array([1,3,6,8,6,3,1],dtype=float)/28
        pts=sum(w*np.roll(pts,j-3,axis=0) for j,w in enumerate(weights))
        path=list(pts)
        k=np.argmax(np.sum((pts-pts[0])**2,axis=1))
        curve=np.array(simplify(path[:k+1],0.35)[:-1]+simplify(path[k:]+[path[0]],0.35)[:-1])
        for _ in range(2):
            after=np.roll(curve,-1,axis=0)
            curve=np.stack((curve*.82+after*.18,curve*.18+after*.82),axis=1).reshape(-1,2)
        paths.append((area,curve))
    im=Image.new('L',(1024,1024)); d=ImageDraw.Draw(im)
    for area,curve in sorted(paths,key=lambda i:-abs(i[0])):
        d.polygon([tuple(v) for v in curve*scale],fill=255 if area>0 else 0)
    return im

sheet=Image.new('RGB',(936,490),'#66736f')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
for i,(name,title,source) in enumerate(views):
    original=Image.open(out.parent/source).convert('RGBA')
    pix=np.asarray(original).astype(int)
    alpha=pix[:,:,3]>0
    r,g,b=pix[:,:,:3].transpose(2,0,1)
    y,x=np.indices(alpha.shape)
    labels=np.full(alpha.shape,2)
    labels[r-g>13]=1
    head=(y<=(27 if name=='right' else 26))
    labels[head & (r<130) & (r-g<13)]=0
    # Remove eye accents, preserving the hairline above and the locks at the cheek.
    if name=='front':
        labels[(x>=59)&(x<=68)&(y>=17)&(y<=23)]=1
        labels[(x>=65)&(x<=67)&(y>=15)&(y<=18)]=1
    if name=='right':
        labels[(x>=69)&(x<=74)&(y>=17)&(y<=23)]=1
    labels[(y>=88)&alpha]=1
    # Extend material IDs outside the silhouette for clean clipping at its outline.
    queue=deque(zip(*np.where(alpha))); seen=alpha.copy()
    while queue:
        yy,xx=queue.popleft()
        for ny,nx in ((yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)):
            if 0<=ny<128 and 0<=nx<128 and not seen[ny,nx]:
                seen[ny,nx]=True; labels[ny,nx]=labels[yy,xx]; queue.append((ny,nx))
    flat=Image.new('RGB',(1024,1024),palette[2])
    for k in (1,0): flat.paste(palette[k],(0,0,1024,1024),smooth_mask(labels==k))
    flat.putalpha(smooth_mask(alpha))
    flat.save(out/(name+'.png'))
    for j,im in enumerate([original,flat]):
        factor=1 if j==0 else scale
        crop=im.crop((41*factor,0,87*factor,128*factor))
        crop=crop.resize((138,384),Image.Resampling.NEAREST if not j else Image.Resampling.LANCZOS)
        cx=i*312+78+j*156
        sheet.paste(crop,(cx-69,46),crop)
        ImageDraw.Draw(sheet).text((cx,445),['定稿','建模平涂'][j],font=font,anchor='mt',fill='white')
    ImageDraw.Draw(sheet).text((i*312+156,10),title,font=font,anchor='mt',fill='white')
sheet.save(out/'comparison.png')
