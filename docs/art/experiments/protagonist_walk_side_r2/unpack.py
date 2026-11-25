"""Save a numbered proof of a native 128 px PixelLab sheet, without repositioning cels."""
from pathlib import Path
from PIL import Image, ImageDraw
import sys

root = Path(__file__).resolve().parent
source = Path(sys.argv[1])
im = Image.open(source)
if getattr(im, "n_frames", 1) > 1:
    frames = []
    for i in range(im.n_frames):
        im.seek(i)
        frames.append(im.convert("RGBA"))
else:
    im = im.convert("RGBA")
    assert im.width % 128 == 0 and im.height % 128 == 0, im.size
    frames = [im.crop((x, y, x+128, y+128)) for y in range(0, im.height, 128)
              for x in range(0, im.width, 128)]
while frames and frames[-1].getbbox() is None:
    frames.pop()
assert frames and all(f.size == (128,128) and f.getbbox() for f in frames)
dest = root/source.stem
dest.mkdir(exist_ok=True)
sheet = Image.new("RGB",(256*4, 276*((len(frames)+3)//4)), "#343939")
pen = ImageDraw.Draw(sheet)
for i, f in enumerate(frames):
    f.save(dest/f"{i+1:02}.png")
    x,y = (i%4)*256,(i//4)*276
    z = f.resize((256,256),Image.Resampling.NEAREST)
    sheet.paste(z,(x,y+20),z)
    pen.text((x+118,y+2),f"{i+1:02}",fill="white")
sheet.save(dest/"poses.png")
print(len(frames), [f.getbbox() for f in frames])
