"""Build the approved-phase review from native animation cels and measured contacts."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent
old = root.parent / "protagonist_walk_side_r1"
gait = json.loads((root/"gait.json").read_text(encoding="utf-8-sig"))
frames = [Image.open(root/gait["source"]/f"{i:02}.png").convert("RGBA") for i in gait["samples"]]
font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 14)
bg = "#343939"
zoom = Image.Resampling.NEAREST
reference = np.array(Image.open(root.parent/"protagonist_front_c_raw_v2/B_original.png").convert("RGBA"))
palette = np.unique(reference[reference[:,:,3]==255,:3],axis=0).astype(int)
def patch(im):
    top=im.getbbox()[1]
    return np.array(im.crop((0,top,128,top+22)))
def mapped(a):
    delta = a[:,:,:3].astype("int32")[:,:,None,:]-palette
    return np.where(a[:,:,3]>127,(delta**2).sum(axis=3).argmin(axis=2),-1)
def compare(ref, im):
    a,b=patch(ref),patch(im)
    ma=a[:,:,3]>127
    dx=min(range(-12,13),key=lambda k: (np.count_nonzero(ma^(np.roll(b[:,:,3],k,axis=1)>127)),abs(k)))
    b=np.roll(b,dx,axis=1)
    mb=b[:,:,3]>127
    stats=dict(dx=dx, diff_rgba=int(np.count_nonzero(np.any(a!=b,axis=2)&(ma|mb))),
               diff17=int(np.count_nonzero(mapped(a)!=mapped(b))), silhouette=int(np.count_nonzero(ma^mb)),
               union=int((ma|mb).sum()))
    onion=np.stack((20+ma*205,22+mb*197,22+mb*202),axis=2).astype("uint8")
    return stats, Image.fromarray(onion).crop((35,0,91,22))
def tile(im,scale):
    sz=(128*scale,128*scale)
    canvas=Image.new("RGB",sz,bg)
    im=im.resize(sz,zoom)
    canvas.paste(im,(0,0),im)
    return canvas
def animate(images,path,cycle_seconds):
    # Cumulative rounding preserves cycle time to the closest GIF centisecond.
    per_frame=cycle_seconds*100/len(images)
    images=images*5
    durations=[10*(round((i+1)*per_frame)-round(i*per_frame)) for i in range(len(images))]
    images[0].save(path,save_all=True,append_images=images[1:],duration=durations,loop=0,disposal=2)
frames_aligned=[]
for i,im in enumerate(frames):
    out=Image.new("RGBA",(128,128))
    out.paste(im,(0,127-im.getbbox()[3]))
    out.save(root/f"cycle_{i+1:02}.png")
    frames_aligned.append(out)
guide=Image.new("RGB",(384*4,416*2),bg)
onions=Image.new("RGB",(224*4,110*2),bg)
sheet=Image.new("RGBA",(128*8,128))
stats=[]
for j,im in enumerate(frames_aligned):
    sheet.paste(im,(j*128,0))
    x,y=j%4*384,j//4*416
    guide.paste(tile(im,3),(x,y+32))
    pen=ImageDraw.Draw(guide)
    pen.text((x+12,y+5),f"{j+1:02}    原格 {gait['samples'][j]:02}",font=font,fill="white")
    for anchor,c in [(frames_aligned[0].getbbox()[1],"#79adbb"),(gait["hem_guide"],"#ad9980"),(126,"#7cad91")]:
        row=y+32+3*anchor
        pen.line((x,row,x+383,row),fill=c)
    s,o=compare(frames_aligned[0],im)
    stats.append(s)
    xx,yy=j%4*224,j//4*110
    onions.paste(o.resize((224,88),zoom),(xx,yy+20))
    ImageDraw.Draw(onions).text((xx+8,yy),f"{j+1:02}",font=font)
sheet.save(root/"sheet.png")
guide.save(root/"poses_3x.png")
onions.save(root/"head_onion.png")
for scale in (1,3):
    animate([tile(f,scale) for f in frames_aligned],root/f"walk_{scale}x.gif",gait["period_s"])
old_images=[Image.open(old/f"raw_side_{n:02}.png").convert("RGBA") for n in (8,1,2,1)]
comparison=[]
for k,j in enumerate((7,0,1,0)):
    canvas=Image.new("RGB",(768,416),bg)
    for col,(name,pic) in enumerate([("r1 逐帧重画",old_images[k]),("r2 动画",frames_aligned[j])]):
        canvas.paste(tile(pic,3),(col*384,32))
        ImageDraw.Draw(canvas).text((col*384+12,6),f"{name}   {j+1:02}",font=font,fill="white")
    comparison.append(canvas)
animate(comparison,root/"r1_r2_seam.gif",gait["period_s"]*.5)
(root/"head_metrics.json").write_text(json.dumps(stats,indent=2),encoding="utf-8")
print(stats)
