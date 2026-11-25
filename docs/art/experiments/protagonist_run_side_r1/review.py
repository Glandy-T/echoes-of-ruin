"""Export the four unretouched PixelLab poses on the target two-step clock."""
from pilot import FRAMES, HERE
import numpy as np
from PIL import Image, ImageDraw
from finish import matte, save_gif

poses = [Image.open(HERE/"raw"/f"{n:02}.png").convert("RGBA") for n in FRAMES]
period = 2*1.1/3.5
sheet = Image.new("RGB",(1024,280),"#414548")
for i,(frame,pose) in enumerate(zip(FRAMES,poses)):
    sheet.paste(matte(pose).resize((256,256),Image.Resampling.NEAREST),(i*256,0))
    ImageDraw.Draw(sheet).text((i*256+10,258),f"{frame:02}  /  {('CONTACT','FLIGHT')[i%2]}",fill="white")
    if i%2 == 0:
        a = np.array(pose)[:,:,3] >127
        assert not a[116:,75:].any()
        tips = []
        for lo,hi in [(0,56),(75,128)]:
            yy,xx = np.where(a[86:,lo:hi])
            bottom = yy.max()
            tips.append(int(xx[yy>=bottom-6].min())+lo)
        print(frame,tips,"fore-aft span",tips[1]-tips[0])
sheet.save(HERE/"poses.png")
for scale in (1,3):
    images = [matte(pose).resize((128*scale,128*scale),Image.Resampling.NEAREST) for pose in poses]
    save_gif(images,HERE/f"pilot_{scale}x.gif",period)
