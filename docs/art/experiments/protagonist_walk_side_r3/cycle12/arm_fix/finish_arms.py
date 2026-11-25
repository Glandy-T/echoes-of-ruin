"""Keep the approved cycle and merge only the selected limb and silhouette edits."""
from regenerate import OUT
from finish import HEAD_Y, matte, save_gif
from PIL import Image, ImageDraw
import numpy as np

BASE = OUT.parent
ZOOM = Image.Resampling.NEAREST
DARK = [(111,99,93),(137,112,105),(153,128,123),(162,133,122)]


def manual_far_arm(donor, frame):
    # Re-pose the approved frame-2 bare arm below its cuff, one row at a time.
    src = np.asarray(donor)
    out = Image.new("RGBA", donor.size)
    for y in range(46,77):
        row = src[y]
        skin = (row[:,0].astype(int)-row[:,1].astype(int)>14) & (row[:,3]>0)
        xs = np.where(skin & (np.arange(128)>=65))[0]
        if not len(xs):
            continue
        t = (y-46)/30
        cx = round(np.interp(t,[0,.38,1],[68,71,75] if frame==9 else [58,54,47]))
        target_y = y-(6 if frame==9 else 7)
        for x in range(xs[0],xs[-1]+1):
            offset = x-round(xs.mean())
            if frame==11:
                offset = -offset
            shade = np.searchsorted([151,179,211],int(row[x,0]))
            out.putpixel((cx+offset,target_y),(*DARK[shade],255))
    return out


def rear_from_generation(base, new, donor, frame):
    src = np.array(new)
    arm = Image.new("RGBA",base.size)
    for y in range(40,73):
        row = src[y]
        skin = (row[:,0].astype(int)-row[:,1].astype(int)>14) & (row[:,3]>0)
        xs = np.where(skin & (np.arange(128)>=71))[0]
        if len(xs):
            for x in range(xs[0],xs[-1]+1):
                if row[x,3]:
                    shade = np.searchsorted([143,155,174],int(row[x,0]))
                    arm.putpixel((x,y),(*DARK[shade],255))
    if frame == 5:
        # PixelLab reduced the fingertips to two isolated pixels here.
        # Follow the generated forearm, finishing with frame 2's knuckles.
        hand = np.asarray(donor)
        for y in range(62,71):
            src_y = y+6
            row = hand[src_y]
            xs = np.where((np.arange(128)>68)&(row[:,3]>0)&
                          (row[:,0].astype(int)-row[:,1].astype(int)>14))[0]
            arm.paste((0,0,0,0),(70,y,83,y+1))
            if len(xs):
                centre = 75 + int(y>=66)
                for x in range(xs[0],xs[-1]+1):
                    shade = np.searchsorted([151,179,211],int(row[x,0]))
                    arm.putpixel((centre+x-round(xs.mean()),y),(*DARK[shade],255))
    return Image.alpha_composite(arm,base)


def passing_back(im):
    pen = ImageDraw.Draw(im)
    for y in range(43,70):
        edge = 71 + int(y>=54) + int(y>=63)
        pen.line((edge+1,y,77,y),fill=(0,0,0,0))
        pen.line((edge-1,y,edge,y),fill=(124,139,133,255))


def join_hair_roots(im, phase):
    dx = (0,-2,-1,0,0,0)[phase]
    dy = HEAD_Y[phase]
    tip_y = HEAD_Y[(phase-1)%6]
    drift = int(phase in (2,4))
    # Root the two tracked tips in the same locks at every exposure. Retain
    # the standing reference's outer shape and palette around the join.
    for root, tip in [((73+dx,11+dy),(76+dx+drift,13+tip_y)),
                      ((54+dx,11+dy),(51+dx+drift,13+tip_y))]:
        pen = ImageDraw.Draw(im)
        mid = (round((root[0]+tip[0])/2), round((root[1]+tip[1])/2))
        shade = im.getpixel(tip)
        assert shade[3] == 255
        pen.line([root,mid,tip],fill=shade,width=1)


def main():
    before = [Image.open(BASE/"frames"/f"{n:02}.png").convert("RGBA") for n in range(1,13)]
    after = []
    for n,old in enumerate(before,1):
        im = old.copy()
        if n in (5,6,11,12):
            new = Image.open(OUT/"raw"/f"{n:02}.png").convert("RGBA")
            if n in (5,6):
                im = rear_from_generation(im,new,before[1],n)
            else:
                # Keep the accepted far hand on 12. On 11 replace both
                # shoulder contours so the restored far hand joins the body.
                box = (0 if n==11 else 65,29,98,75)
                im.paste(new.crop(box),box[:2])
        if n in (9,11):
            im = Image.alpha_composite(manual_far_arm(before[1],n),im)
        if n in (4,10):
            passing_back(im)
        join_hair_roots(im,(n-1)%6)
        assert np.array_equal(np.asarray(im)[76:],np.asarray(old)[76:])
        assert im.getbbox()[1] == old.getbbox()[1]
        if n not in (4,5,6,9,10,11,12):
            assert np.array_equal(np.asarray(im)[26:],np.asarray(old)[26:])
        (OUT/"frames").mkdir(exist_ok=True)
        im.save(OUT/"frames"/f"{n:02}.png")
        after.append(im)
    olds,news = [[matte(im) for im in ims] for ims in (before,after)]
    save_gif(news,OUT/"walk_1x.gif",1.08)
    save_gif([im.resize((384,384),ZOOM) for im in news],OUT/"walk_3x.gif",1.08)
    sheet = Image.new("RGB",(3*312,4*279),"#414548")
    pen = ImageDraw.Draw(sheet)
    panels = []
    for n,(a,b) in enumerate(zip(olds,news)):
        x,y=n%3*312,n//3*279
        panel = Image.new("RGB",(512,277),"#414548")
        for k,(im,label) in enumerate([(a,"Before"),(b,"After")]):
            panel.paste(im.resize((256,256),ZOOM),(k*256,21))
            ImageDraw.Draw(panel).text((k*256+12,5),label,fill="white")
            tile=im.crop((22,0,100,128)).resize((156,256),ZOOM)
            sheet.paste(tile,(x+k*156,y+21))
            pen.text((x+k*156+8,y+4),f"{n+1:02}  {label}",fill="white")
        panels.append(panel)
    sheet.save(OUT/"poses_before_after.png")
    save_gif(panels,OUT/"before_after.gif",1.08)


if __name__ == "__main__":
    main()
