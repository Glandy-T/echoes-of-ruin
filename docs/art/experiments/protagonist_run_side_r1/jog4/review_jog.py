"""Register four generated poses and measure the delivered pixels."""
import json
from PIL import Image, ImageDraw
import numpy as np
from skeleton import HERE, FRAMES, jog
from finish import separate_limbs, matte, save_gif
from review import contact_toes

NEAREST = Image.Resampling.NEAREST
GROUND = 125


def head(image, idle, high, dx=-4, dy=None, lag=None):
    if dy is None:
        dy = 0 if high else 3
    if lag is None:
        lag = 2 if high else -2
    layer = idle.crop((0,0,128,27))
    # Keep two rooted locks attached, carrying the ends only.
    for strand,root in [([(74,11),(74,12),(75,12),(75,13),(76,13)],(73,11)),
                        ([(53,11),(52,12),(51,13)],(54,11))]:
        for pt in strand:
            layer.putpixel(pt,(0,0,0,0))
        previous = root
        for index,(x,y) in enumerate(strand,1):
            ratio = index/len(strand)
            target=(x+round(int(high)*ratio),y+round(lag*ratio))
            ImageDraw.Draw(layer).line([previous,target],fill=idle.getpixel((x,y)))
            previous=target
    image.paste((0,0,0,0),(0,0,128,26+dy))
    image.paste(layer.crop((0,0,128,26)),(dx,dy))
    return 13+dy+lag


def finish(raw,points,high,frame):
    im = separate_limbs(raw,points)
    if frame in (1,7):
        far=Image.new("RGBA",im.size)
        pen=ImageDraw.Draw(far)
        y=57 if frame==1 else 54
        pen.line([(47,y+1),(51,y+2),(59,y)],fill=(153,128,123,255),width=3)
        im=Image.alpha_composite(far,im)
    data=np.array(im)
    if not high:
        # Pull the trailing knee slightly under the skirt without moving its foot.
        for y in range(85,107):
            dx=round(3*max(0,1-abs(y-92)/12))
            if dx:
                data[y,63:112-dx]=data[y,63+dx:112].copy()
    # A strip map tapers to zero at waist and calf. In the high pose the
    # bottom of the gown still hangs low; at contact it is still settling.
    hem_delta=1 if high else -2
    shaped=data.copy()
    for y in range(70,100):
        weight=np.interp(y,[70,80,88,99],[0,1,1,0])
        src=y-round(hem_delta*weight)
        data[y]=shaped[src]
    im=Image.fromarray(data)
    old_bottom=im.getbbox()[3]-1
    target=GROUND-2*high
    shin=im.crop((0,99,128,old_bottom+1)).resize((128,target-98),NEAREST)
    im.paste((0,0,0,0),(0,99,128,128))
    im.paste(shin,(0,99))
    return im


def export():
    idle=Image.open(HERE.parents[1]/"protagonist_five_idle_eyes_r3/final_90.png").convert("RGBA")
    frames=[]
    report=[]
    skeletons={}
    for frame,pose in zip(FRAMES,jog()["keypoints"]):
        high=frame in (3,7)
        points={j["label"]:(int(128*j["x"]),int(128*j["y"])) for j in pose}
        skeletons[frame]=points
        raw=Image.open(HERE/"raw"/f"{frame:02}.png").convert("RGBA")
        im=finish(raw,points,high,frame)
        tip=head(im,idle,high)
        assert im.getpixel((72+int(high),tip))==idle.getpixel((76,13))
        foot=im.getbbox()[3]-1
        assert foot == GROUND-2*high
        report.append(dict(frame=frame,ground_clearance_px=GROUND-foot,crown_y=im.getbbox()[1],
                           rig_pelvis_y=points["LEFT HIP"][1],rear_tip_y=tip))
        (HERE/"frames").mkdir(exist_ok=True)
        im.save(HERE/"frames"/f"{frame:02}.png")
        frames.append(im)
    contacts=[contact_toes(frames[i]) for i in (0,2)]
    steps=[contacts[1][1]-contacts[0][0],contacts[0][1]-contacts[1][0]]
    meters=[px*1.65/125 for px in steps]
    period=sum(meters)/2.5
    metrics=dict(contacts_x=contacts,steps_px=steps,steps_m=meters,period_s=period,
                 sample_fps=4/period,eight_frame_fps=8/period,poses=report)
    (HERE/"measurements.json").write_text(json.dumps(metrics,indent=2))
    (HERE/"joints.json").write_text(json.dumps(skeletons,indent=2))
    print(metrics)
    old=[Image.open(HERE.parent/"raw"/f"{n:02}.png").convert("RGBA") for n in FRAMES]
    pairs=[]
    sheet=Image.new("RGB",(4*256,2*280),"#414548")
    for i,(before,after) in enumerate(zip(old,frames)):
        pair=Image.new("RGB",(512,280),"#414548")
        for row,(im,label) in enumerate([(before,"First pilot"),(after,"Tired jog")]):
            pic=matte(im).resize((256,256),NEAREST)
            pair.paste(pic,(256*row,21))
            ImageDraw.Draw(pair).text((256*row+10,4),label,fill="white")
            sheet.paste(pic,(i*256,row*280+21))
            ImageDraw.Draw(sheet).text((i*256+10,row*280+4),f"{label}   {FRAMES[i]:02}   {('CONTACT','FLIGHT')[i%2]}",fill="white")
        pairs.append(pair)
    sheet.save(HERE/"comparison.png")
    save_gif(pairs,HERE/"comparison.gif",period)
    for scale in (1,3):
        save_gif([matte(im).resize((128*scale,128*scale),NEAREST) for im in frames],HERE/f"jog_{scale}x.gif",period)


if __name__=="__main__":
    export()
