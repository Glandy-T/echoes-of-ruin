"""Measure the naked-eye review candidates on the delivered native-resolution drawings."""
import csv
from pathlib import Path
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent


def neck(path):
    a=np.asarray(Image.open(path).convert("RGBA")).astype(int)
    r,g,_,alpha=a.transpose(2,0,1)
    top=int(np.flatnonzero(alpha.any(1))[0])
    def left(y):
        return int(np.flatnonzero(alpha[y])[0])
    chin=max(range(top+16,top+26),key=lambda y:left(y+1)-left(y))
    x=left(chin)
    skin=(r-g>=16)&(alpha>0)
    end=chin
    while skin[end+1,x-2:x+18].any():
        end+=1
    return top,chin,end,end-chin,int(skin[chin+1:end+1,x-2:x+8].sum())


def record(paths):
    with (HERE/"measurements.csv").open("w",newline="") as f:
        w=csv.writer(f)
        w.writerow(("version","frame","crown_y","chin_y","last_neck_skin_y","exposed_height_px","front_throat_pixels"))
        w.writerow(("idle",0,*neck(HERE.parents[1]/"protagonist_five_idle_eyes_r3/final_90.png")))
        for n,p in enumerate(paths,1):
            w.writerow(("skeleton",n,*neck(p)))
        for n,p in enumerate(sorted((HERE/"fallback/frames").glob("*.png")),1):
            w.writerow(("fallback",n,*neck(p)))
