"""Review the two whole-frame replacements in their original eight-frame sequence."""
from pathlib import Path
import shutil
import sys

from PIL import Image,ImageDraw,ImageFont,ImageSequence

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
sys.path.insert(0,str(BASE))
from export_advisor import matte,save_gif,NEAREST


def original(n):
    return BASE/("retry_01/raw/01.png" if n==1 else f"raw/{n:02}.png")


def export(replacements):
    folder=HERE/"frames"
    folder.mkdir(exist_ok=True)
    before,after=[],[]
    for n in range(1,9):
        old=original(n)
        source=replacements.get(n,old)
        target=folder/f"{n:02}.png"
        shutil.copyfile(source,target)
        assert source.read_bytes()==target.read_bytes()
        before.append(Image.open(old).convert("RGBA"))
        after.append(Image.open(target).convert("RGBA"))
    period=2*60*1.65/125/2.5
    panels=[]
    font=ImageFont.truetype("msyh.ttc",15)
    for n,(old,new) in enumerate(zip(before,after),1):
        page=Image.new("RGB",(512,284),"#414548")
        pen=ImageDraw.Draw(page)
        pen.fontmode="1"
        for k,(im,label) in enumerate(((old,"修前"),(new,"修后"))):
            page.paste(matte(im).resize((256,256),NEAREST),(k*256,26))
            pen.text((9+k*256,4),label,font=font,fill="white")
        pen.text((460,4),f"{n:02}",font=font,fill="#eddbb0")
        panels.append(page)
    save_gif(panels,HERE/"comparison.gif",period)
    for scale in (1,3):
        save_gif([matte(im).resize((128*scale,128*scale),NEAREST) for im in after],HERE/f"run_{scale}x.gif",period)
    close=Image.new("RGB",(2*210,2*185),"#414548")
    p=ImageDraw.Draw(close)
    for j,n in enumerate((2,6)):
        for col,(im,label) in enumerate(((before[n-1],"修前"),(after[n-1],"修后"))):
            close.paste(matte(im).crop((33,31,84,69)).resize((204,152),NEAREST),(col*210,185*j+28))
            p.text((col*210+8,185*j+4),f"{n:02}  {label}",font=font,fill="white")
    close.save(HERE/"arms_02_06.png")
    def timing(path):
        with Image.open(path) as gif:
            assert gif.n_frames==8 and gif.info["loop"]==0
            return [frame.info["duration"] for frame in ImageSequence.Iterator(gif)]
    for name in ("comparison.gif","run_1x.gif","run_3x.gif"):
        assert timing(HERE/name)==timing(BASE/"run_1x.gif")


if __name__=="__main__":
    export({2:HERE/"retry_down/raw/01.png",6:HERE/"raw/04.png"})
