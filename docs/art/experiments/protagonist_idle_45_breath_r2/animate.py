"""Render six held drawings from the unmodified D through a shared deformation mesh."""
from pathlib import Path
from shutil import copyfile
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import Delaunay

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "protagonist_idle_45_breath_r1"
sys.path.insert(0, str(PREVIOUS))
from build import DURATION, SOURCE, loop

OUT = HERE / "45"
Y, X = np.indices((128, 128))
# Load at the pelvis, rib expansion, upper-back counterbalance, trailing arm,
# head (rigid x/y), trailing hair (rigid x/y), pressure off the free heel.
POSES = [
    (0,    0,    0,    0,    (0,0),  (0,0),  0),
    (.40,  .65,  .12,  .04,  (0,0),  (0,0),  .08),
    (.88,  1,    .70,  .35,  (0,-1), (0,0),  .28),
    (1,    .85,  1,    .88,  (1,-1), (0,-1), .76),
    (.64,  .18,  .85,  1,    (1,-1), (1,-1), .87),
    (.16,  0,    .25,  .42,  (0,0),  (1,0),  .30),
]


def controls(pose):
    load, inhale, balance, drag, head, hair, heel = pose
    anchors = {}

    def point(x,y,dx=0,dy=0):
        anchors[x,y] = (dx,dy)

    for y in (0,27,70,87,127):
        point(0,y)
        point(127,y)
    # Rigid head connects through a short mobile neck to both clavicles.
    for x in (40,62,86):
        point(x,25,*head)
    point(63,28,.8*balance,-.9*inhale)
    point(55,32,-.6*balance,-1.15*inhale-.55*load)
    point(71,33,.7*balance,-.85*inhale+1.1*load)
    # Expansion on the front of the three-quarter rib cage, with spine above pelvis.
    point(54,42,-1.15*inhale+.5*balance,-.7*inhale)
    point(63,42,.3*balance,-.6*inhale)
    point(71,42,.75*balance+.35*inhale,.6*load-.55*inhale)
    point(55,53,1.25*load-.5*inhale,-.2*inhale)
    point(65,53,1.4*load,0)
    point(72,55,1.7*load,.1*load)
    # The pelvis leads. The weight-bearing hip rises; the opposite waist settles.
    point(53,65,2.4*load,.65*load)
    point(64,65,2.7*load,0)
    point(72,65,3*load,-.95*load)
    # Elbows follow the shoulder arc; wrists hang a little behind it.
    point(51,50,-.8*balance,-.65*inhale)
    point(76,51,1.1*balance,.8*load-.5*inhale)
    point(47,63,-.8*drag,-.55*drag)
    point(47,72,.8*drag,-drag)
    point(76,63,1.2*drag,.7*drag)
    point(75,72,1.35*drag,.7*drag)
    # Fabric loses the hip excursion toward the fixed bottom edge.
    point(54,75,1.3*load,.3*load)
    point(66,75,1.4*load,0)
    point(77,77,.6*load,-.3*load)
    for x in (47,55,63,71,80):
        point(x,83)
        point(x,87)
    # The loaded knee moves over its ankle; the free knee bends inward.
    point(55,96,1.65*load, .65*load)
    point(70,96,.8*load,-.45*load)
    point(57,107,1.05*load, .05*load)
    point(70,107,.35*load,0)
    point(58,116,.45*load,-.8*heel)
    point(70,116)
    point(59,121,.2*load,-heel)
    point(54,122,0,-.2*heel)
    for x,y in ((45,119),(50,121),(53,123),(60,124),(63,119),(73,119),(65,126),(75,126)):
        point(x,y)
    return np.array(list(anchors),float), np.array(list(anchors.values()),float)


def draw(src, pose):
    source, offsets = controls(pose)
    dest = source + offsets
    # Same topology for every exposure. Invert each displaced triangle into D.
    triangles = Delaunay(source).simplices
    sample_x, sample_y = X.copy(), Y.copy()
    for indices in triangles:
        tri = dest[indices]
        x0,y0 = np.floor(tri.min(0)).astype(int).clip(0,127)
        x1,y1 = np.ceil(tri.max(0)).astype(int).clip(0,127)
        roi = np.s_[y0:y1+1,x0:x1+1]
        pixels = np.stack((X[roi],Y[roi]),axis=-1)
        uv = (pixels-tri[0]) @ np.linalg.inv(tri[1:]-tri[0])
        inside = (uv.min(-1)>=-1e-7) & (uv.sum(-1)<=1+1e-7)
        origin = source[indices]
        xy = np.rint(origin[0] + uv @ (origin[1:]-origin[0])).astype(int)
        sample_x[roi][inside] = xy[:,:,0][inside]
        sample_y[roi][inside] = xy[:,:,1][inside]
    hx,hy = pose[4]
    tx,ty = pose[5]
    upper = Y <= 25
    sample_x[upper] = X[upper]-hx
    sample_y[upper] = Y[upper]-hy
    # Small trailing ends outside the facial features.
    wisps = (((X>=50)&(X<=54)&(Y>=13)&(Y<=17)) |
             ((X>=53)&(X<=55)&(Y>=21)&(Y<=25)) |
             ((X>=70)&(X<=75)&(Y>=21)&(Y<=25)))
    sample_x[wisps] = X[wisps]-tx
    sample_y[wisps] = Y[wisps]-ty
    out = src[sample_y.clip(0,127),sample_x.clip(0,127)]
    r,g = src[:,:,0].astype(int),src[:,:,1].astype(int)
    fy,fx = np.where((Y<=25)&(src[:,:,3]>0)&(r-g>=14))
    assert np.array_equal(out[fy+hy,fx+hx],src[fy,fx])
    assert np.array_equal(out[83:88],src[83:88])
    assert np.array_equal(out[119:,63:],src[119:,63:])
    assert np.array_equal(out[121:,:54],src[121:,:54])
    return out


def tile(image):
    bg=Image.new("RGB",image.size,"#555b5e")
    bg.paste(image,mask=image.getchannel("A"))
    return bg


def build():
    OUT.mkdir(exist_ok=True)
    src=np.array(Image.open(SOURCE).convert("RGBA"))
    tiles, pairs = [], []
    font=ImageFont.truetype("msyh.ttc",14)
    for i,pose in enumerate(POSES,1):
        out=draw(src,pose)
        path=OUT/f"{i:02}.png"
        if i==1:
            assert np.array_equal(out,src)
            copyfile(SOURCE,path)
        else:
            Image.fromarray(out).save(path)
        current=tile(Image.open(path).convert("RGBA"))
        tiles.append(current)
        older=tile(Image.open(PREVIOUS/"45"/path.name).convert("RGBA"))
        pair=Image.new("RGB",(256,281),"#424849")
        pen=ImageDraw.Draw(pair)
        for j,(im,label) in enumerate(((older,"上一版"),(current,"这版"))):
            pair.paste(im.crop((32,0,96,128)).resize((128,256),Image.Resampling.NEAREST),(128*j,24))
            pen.text((128*j+8,3),label,font=font,fill="white")
        pairs.append(pair)
    loop(pairs,OUT/"compare.gif")
    for scale in (1,3):
        loop([im.resize((128*scale,128*scale), Image.Resampling.NEAREST) for im in tiles],OUT/f"breath_{scale}x.gif")
    sheet=Image.new("RGB",(6*132,282),"#424849")
    pen=ImageDraw.Draw(sheet)
    for i,im in enumerate(tiles):
        sheet.paste(im.crop((31,0,96,128)).resize((130,256),Image.Resampling.NEAREST),(132*i,24))
        pen.text((132*i+6,4),f"{i+1:02}    {DURATION[i]} ms",fill="white")
    sheet.save(OUT/"six_frames.png")


if __name__=="__main__":
    build()
