"""Run8 torso rotation, PixelLab-free. All rotations sample original palette entries."""
import csv
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageSequence

HERE = Path(__file__).resolve().parent
RUN = HERE.parent / "run8"
HAND_PASS = HERE.parent / "run8_head_shoulders"
sys.path.insert(0, str(HAND_PASS))
from build import HIP, PHASE, NEAREST, matte, save_gif, shift_at, sprite

BODY = 9.0
COUNTER = -4.0
SCALE = 8


def upright_arms(n):
    # Undo the old row offsets on the hand correction only. Thus both hands
    # ride the same new hip rotation as their original run8 shoulder.
    im = sprite(RUN,n)
    if (n-1)%4 == 1:
        # Both arms pass the waist. Transfer the lean drawing between the
        # original sleeve openings and the fixed hip row, matching the wrist.
        near_low=n==2
        donor=sprite(HERE.parent/"run8_lean",n)
        for y in range(49,65):
            t=min(1,(y-48)/7,(65-y)/4 if near_low else 1)
            for x in range(46,75):
                ox=3 if near_low else 2
                sy=min(67,y+1)
                px=donor.getpixel((x-ox,sy))
                old=im.getpixel((x,y))
                skin=lambda c:c[3] and int(c[0])-int(c[1])>=16
                if skin(px) and (t>=0.5 or skin(old)):
                    im.putpixel((x,y),px)
                elif skin(old) and t>=0.5:
                    replacement=donor.getpixel((x-ox,sy))
                    im.putpixel((x,y),replacement)
        return im
    patched = sprite(HAND_PASS,n)
    result = im.copy()
    for y in range(38,62):
        d = shift_at(y,(n-1)%4)
        result.paste(patched.crop((0,y,128-d,y+1)),(d,y))
    return result


def approved_upper(im, idle, hip):
    # Restore a continuous design plate before posing. Its jaw, neck, neckline
    # and both shoulder roots come from one drawing, at one native scale.
    dy=hip-62
    out=im.copy()
    for y in range(24+dy,34+dy):
        out.paste((0,0,0,0),(0,y,128,y+1))
        out.paste(idle.crop((0,y-dy,128,y-dy+1)),(-1,y))
    # Join inside the gown, below the collar, to the moving run8 sleeve.
    for y in range(34+dy,39+dy):
        t=(y-33-dy)/6
        src=im.crop((0,y,128,y+1))
        l,_,r,_=src.getbbox()
        left,_,right,_=out.crop((0,33+dy,128,34+dy)).getbbox()
        el,_,er,_=im.crop((0,39+dy,128,40+dy)).getbbox()
        lo,hi=round(left+(el-left)*t),round(right+(er-right)*t)
        out.paste((0,0,0,0),(0,y,128,y+1))
        out.paste(src.crop((l,0,r,1)).resize((hi-lo,1),NEAREST),(lo,y))
    return out


def scale2x(a):
    p=np.pad(a,1,mode="edge")
    b,d,f,h=p[:-2,1:-1],p[1:-1,:-2],p[1:-1,2:],p[2:,1:-1]
    split=(b!=h)&(d!=f)
    out=np.empty((a.shape[0]*2,a.shape[1]*2),a.dtype)
    for oy,ox,side,other in ((0,0,d,b),(0,1,b,f),(1,0,d,h),(1,1,h,f)):
        out[oy::2,ox::2]=np.where(split & (side==other),side,a)
    return out


def turn(pt, pivot, angle):
    x,y=np.subtract(pt,pivot)
    c,s=math.cos(math.radians(angle)),math.sin(math.radians(angle))
    return pivot[0]+c*x+s*y,pivot[1]-s*x+c*y


def point(x,y,hip):
    return turn(turn((x,y),(62.5,hip-38.5),COUNTER),(64.5,hip+.5),BODY)


def rotated_grid(source,hip):
    a=np.array(source.convert("RGBA")).copy()
    a[a[:,:,3]==0]=0
    packed=a.view(np.uint32)[:,:,0]
    for _ in range(3):
        packed=scale2x(packed)
    high=Image.fromarray(packed.view(np.uint8).reshape(1024,1024,4))
    cut=(hip-62+23)*SCALE
    neck=(62.5*SCALE,(hip-38.5)*SCALE)
    pivot=(64.5*SCALE,(hip+.5)*SCALE)
    # Articulate at the neck joint. Keep the rotated head overlapping its
    # original attachment by one source row so the jaw joins the upper body.
    head=Image.new("RGBA",high.size)
    head.paste(high.crop((0,0,1024,cut+SCALE)))
    head=head.rotate(COUNTER,NEAREST,center=neck)
    high.paste((0,0,0,0),(0,0,1024,cut))
    high=Image.alpha_composite(high,head).rotate(BODY,NEAREST,center=pivot)
    return np.array(high)

def sample(high,source,hip,lag,phase_x=0,phase_y=5):
    raster=Image.fromarray(high[phase_y::8,phase_x::8].copy())
    # Carry the head, neck and shoulders together through the previous phase's
    # height. The small vertical settle tapers through the waist to the fixed hip.
    out=source.copy()
    for y in range(hip):
        sy=y-round(lag*np.clip((hip-y)/15,0,1))
        out.paste(raster.crop((0,sy,128,sy+1)),(0,y))
    return out


def metrics(im):
    a=np.array(im).astype(int)
    r,g,b,t=a.transpose(2,0,1)
    top=im.getbbox()[1]
    left=lambda y:int(np.flatnonzero(t[y])[0])
    candidates=list(range(top+17,top+25))
    chin=max(candidates,key=lambda y:left(y+1)-left(y))
    skin=(r-g>=16)&(t>0)
    hair=(g>=r-5)&(g<133)&(t>0)
    cx=left(chin)
    end=chin
    while skin[end+1,cx-2:cx+18].any():
        end+=1
    # Throat exposure: count bare skin below the front of the jaw, on its
    # anterior half. Also record the total vertical span to the last skin row.
    cx=left(chin)
    count=np.count_nonzero(skin[chin+1:end+1,:cx+8])
    runs=[]
    for x in range(left(chin+1),left(chin+1)+12):
        for y in range(chin-3,chin+5):
            if hair[y,x]:
                j=y+1
                while j<42 and skin[j,x]:
                    j+=1
                if j>y+1 and t[j,x] and not hair[j,x]:
                    runs.append(j-y-1)
    return top,chin,cx,int(end-chin),int(count),max(runs,default=0)


def finish_pixels(im,idle,hip,lag):
    # Native-size eye and fringe registration. Use the original two-pixel
    # eyelid, its lower shadow, and the dark edge of the forelock.
    keys=[(57,13),(58,13),(60,14),(61,14),(57,15),(58,15),(59,15),
          (60,15),(56,16),(57,16),(58,16),(59,16)]
    for x,y in keys:
        tx,ty=point(x-.5,y+.5+hip-62,hip)
        im.putpixel((round(tx-.0625),round(ty-.6875)+lag),idle.getpixel((x,y)))
    # Correct the leading cloth contour by one or two pixels at the ribs,
    # avoiding the skin of either arm and the draped sleeve shading.
    top=im.getbbox()[1]
    for y in range(top+33,top+45):
        for x in (49,50,51):
            r,g,b,a=im.getpixel((x,y))
            if a and abs(r-g)<=15 and r>=124:
                im.putpixel((x,y),(0,0,0,0))
    # Join the last two rotated gown rows to the unrotated waist contour.
    # Keep hands separate from the fabric edge.
    def cloth_span(y):
        row=np.array(im.crop((0,y,128,y+1))).astype(int)[0]
        r,g,b,a=row.T
        solid=np.flatnonzero((a>0)&(abs(r-g)<=15)&(r>=124))
        return int(solid[0]),int(solid[-1])
    upper=cloth_span(hip-3)
    lower=cloth_span(hip)
    for i in (1,2):
        y=hip-3+i
        l,r=cloth_span(y)
        for edge,goal,interior in ((l,round(upper[0]+(lower[0]-upper[0])*i/3),1),
                                   (r,round(upper[1]+(lower[1]-upper[1])*i/3),-1)):
            if (edge-goal)*interior>0 and abs(edge-goal)<=2:
                for x in range(min(edge,goal),max(edge,goal)+1):
                    if not im.getpixel((x,y))[3]:
                        im.putpixel((x,y),im.getpixel((edge,y)))


def main():
    (HERE/"frames").mkdir(exist_ok=True)
    idle=Image.open(HERE.parents[1]/"protagonist_five_idle_eyes_r3/final_90.png").convert("RGBA")
    reference=metrics(idle)
    assert reference[3:]==(6,16,4)
    imgs,pairs,rows=[],[],[]
    neck_sample=None
    font=ImageFont.truetype("msyh.ttc",15)
    small=ImageFont.truetype("msyh.ttc",13)
    necksheet=Image.new("RGB",(3*168,3*175),"#414548")
    def detail(im,index,label):
        top,chin,x,*_=metrics(im)
        crop=matte(im).crop((x-8,chin-23,x+32,chin+13)).resize((160,144),NEAREST)
        pos=(index%3*168,index//3*175)
        necksheet.paste(crop,(pos[0],pos[1]+24))
        ImageDraw.Draw(necksheet).text((pos[0]+6,pos[1]+3),label,font=small,fill="white")
    detail(idle,0,"90° 定稿站姿")
    for n in range(1,9):
        i=(n-1)%4
        hip,lag=HIP[i],HIP[i-1]-HIP[i]
        source=approved_upper(upright_arms(n),idle,hip)
        original=sprite(RUN,n)
        im=sample(rotated_grid(source,hip),source,hip,lag)
        finish_pixels(im,idle,hip,lag)
        path=HERE/"frames"/f"{n:02}.png"
        im.save(path)
        im=Image.open(path).convert("RGBA")
        assert im.crop((0,hip,128,128)).tobytes()==original.crop((0,hip,128,128)).tobytes()
        top,chin,x,length,throat,nape=metrics(im)
        assert length==reference[3] and throat<=reference[4] and nape==reference[5]
        neck=im.crop((x-2,chin,x+14,chin+length+1)).tobytes()
        if neck_sample is None:
            neck_sample=neck
        assert neck==neck_sample
        assert top==(3,4,7,4)[i]
        rows.append((n,hip,top,chin,length,throat,nape))
        imgs.append(im)
        mock=Image.open(HERE.parent/"advisor_lean_mock"/f"{n:02}.png").convert("RGBA")
        panel=Image.new("RGB",(648,284),"#414548")
        pen=ImageDraw.Draw(panel)
        pen.fontmode="1"
        for k,(item,label) in enumerate(zip((original,mock,im),("run8","顾问旋转小样","本次修订"))):
            panel.paste(matte(item).crop((15,0,121,128)).resize((212,256),NEAREST),(k*216+2,26))
            pen.text((k*216+10,4),label,font=font,fill="white")
        pen.text((543,4),f"{n:02}   {PHASE[i]}",font=small,fill="#eadbb8")
        pairs.append(panel)
        detail(im,n,f"{n:02}   {PHASE[i]}")
    necksheet.save(HERE/"neck_detail.png")
    with (HERE/"measurements.csv").open("w",newline="") as f:
        writer=csv.writer(f)
        writer.writerow(("frame","hip_y","crown_y","chin_y","exposed_neck_height_px","front_throat_pixels","nape_run_px"))
        writer.writerows(rows)
    period=2*60*1.65/125/2.5
    for scale in (1,3):
        save_gif([matte(im).resize((128*scale,128*scale),NEAREST) for im in imgs],HERE/f"run_{scale}x.gif",period)
    save_gif(pairs,HERE/"comparison.gif",period)
    def delays(path):
        with Image.open(path) as gif:
            return [frame.info["duration"] for frame in ImageSequence.Iterator(gif)]
    for name in ("run_1x.gif","run_3x.gif","comparison.gif"):
        assert delays(HERE/name)==delays(RUN/"run_1x.gif")


if __name__=="__main__":
    main()
