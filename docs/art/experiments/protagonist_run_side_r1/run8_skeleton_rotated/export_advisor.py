"""Export actual source drawings with the accepted run8 exposures."""
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont, ImageSequence

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"run8"))
from review_run import matte,save_gif,NEAREST


def export(folder,source,label,replacements=None):
    period=2*60*1.65/125/2.5
    idle=Image.open(HERE.parents[1]/"protagonist_five_idle_eyes_r3/final_90.png").convert("RGBA")
    group=[]
    for n in range(1,9):
        name=f"{n:02}.png"
        paths=(HERE.parent/"run8/frames"/name,(replacements or {}).get(n,source/name),HERE.parent/"advisor_lean_mock"/name)
        group.append([Image.open(p).convert("RGBA") for p in paths])
    for scale in (1,3):
        singles,pages=[],[]
        font=ImageFont.truetype("msyh.ttc",12 if scale==1 else 18)
        for n,trio in enumerate(group,1):
            side=128*scale
            page=Image.new("RGB",(3*side,side+30),"#414548")
            pen=ImageDraw.Draw(page)
            pen.fontmode="1"
            for k,(im,title) in enumerate(zip(trio,("run8",label,"顾问小样"))):
                tile=matte(im).resize((side,side),NEAREST)
                page.paste(tile,(side*k,29))
                pen.text((side*k+5,4),title,font=font,fill="white")
                if k==1:
                    singles.append(tile)
            pen.text((3*side-32,4),f"{n:02}",font=font,fill="#eddbb0")
            pages.append(page)
        save_gif(pages,folder/f"compare_{scale}x.gif",period)
        save_gif(singles,folder/f"run_{scale}x.gif",period)
    sheet=Image.new("RGB",(3*180,3*220),"#414548")
    for i,im in enumerate([idle]+[trio[1] for trio in group]):
        x,y=i%3*180,i//3*220
        sheet.paste(matte(im).crop((36,0,92,66)).resize((168,198),NEAREST),(x+4,y+21))
        ImageDraw.Draw(sheet).text((x+5,y+1),"90° 定稿" if not i else f"{i:02}",font=ImageFont.truetype("msyh.ttc",14),fill="white")
    sheet.save(folder/"upper_review.png")
    def delays(path):
        with Image.open(path) as f:
            assert f.n_frames==8 and f.info["loop"]==0
            return [frame.info["duration"] for frame in ImageSequence.Iterator(f)]
    reference=delays(HERE.parent/"run8/run_1x.gif")
    for p in folder.glob("*.gif"):
        assert delays(p)==reference


if __name__=="__main__":
    from measure import record
    selected={1:HERE/"retry_01/raw/01.png"}
    export(HERE,HERE/"raw","骨架原件",selected)
    record([selected.get(n,HERE/"raw"/f"{n:02}.png") for n in range(1,9)])


