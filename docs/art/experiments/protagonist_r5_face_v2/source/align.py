from island import *
from PIL import ImageDraw
palette=Image.open(old/'skin.png').convert('RGB')
ref=Image.open(old.parent/'protagonist_front_c_raw_v2/B_original.png').convert('RGB')
assert not set(verts)&set(face[np.setdiff1d(np.arange(len(face)),group)].flatten())
target=tex.copy()
x,y,z=positions[verts].T
target[verts,0]=(58.5+9*np.arctan2(-z,x+.018))/128
target[verts,1]=(48.5+(.957-y)*152)/128
def surface(t,margin=0):
    low=np.floor(t.min(0)).astype(int)-margin
    high=np.ceil(t.max(0)).astype(int)+margin
    for iy in range(low[1],high[1]):
        for ix in range(low[0],high[0]):
            w=(np.array([ix+.5,iy+.5])-t[0])@np.linalg.inv((t[1:]-t[0]).astype(float))
            if min(w)>=0 and sum(w)<=1:yield (ix,iy),w
img=Image.new('RGBA',palette.size)
field={}
for i in group:
    t=target[face[i]]*128
    for xy,w in surface(t):
        a=uv[i,0]+w@(uv[i,1:]-uv[i,0])
        rgb=palette.getpixel(tuple(np.floor(a).astype(int)))
        ix,iy=xy
        if 52<=iy<=64 and 48<=ix<=68:
            rgb=(231,195,157) if abs(ix-58)<=6 else (215,175,140)
            u=int(np.floor(64.5+(ix-58)*.95))
            row=17+iy-58
            if (row in (17,18) and 60<=u<=68) or (row in (20,22) and 63<=u<=65):
                rgb=ref.getpixel((u,row))
        field[xy]=rgb
for xy,rgb in field.items():img.putpixel(xy,(*rgb,255))
for x,y in list(field):
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            xy=x+dx,y+dy
            if xy not in field and img.getpixel(xy)[3]==0:img.putpixel(xy,(*field[x,y],255))
# Verify clearance against the other islands at native pixel resolution.
occupied=set()
for i in np.setdiff1d(np.arange(len(face)),group):
    if not (uv[i,:,0].min()<85 and uv[i,:,0].max()>32 and uv[i,:,1].min()<82 and uv[i,:,1].max()>38):continue
    for xy,_ in surface(uv[i]):
        occupied.add(xy)
pixels=set(zip(*np.where(np.array(img)[:,:,3].T>0)))
offsets=sorted(((i,j) for i in range(-5,6) for j in range(-4,6)),key=lambda a:a[0]**2+a[1]**2)
dx,dy=next((a,b) for a,b in offsets if all((x+a,y+b) not in occupied for x,y in pixels))
target[verts]+=np.array([dx,dy])/128
shifted=Image.new('RGBA',img.size)
shifted.paste(img,(dx,dy))
img=shifted
img.save(p/'source/face_overlay.png')
np.save(p/'source/face_uv.npy',target)


