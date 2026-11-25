"""One hip rotation of the original run8 PixelLab PNGs; no other painting."""
from pathlib import Path
import numpy as np
from PIL import Image
from export_advisor import HERE,NEAREST,export

OUT=HERE/"fallback"
HIP=(62,65,62,61)


def scale2x(a):
    padded=np.pad(a,1,mode="edge")
    up,down=padded[:-2,1:-1],padded[2:,1:-1]
    left,right=padded[1:-1,:-2],padded[1:-1,2:]
    split=(up!=down)&(left!=right)
    result=np.empty((2*a.shape[0],2*a.shape[1]),a.dtype)
    for row,col,b,c in ((0,0,up,left),(0,1,up,right),(1,0,down,left),(1,1,down,right)):
        result[row::2,col::2]=np.where(split & (b==c),b,a)
    return result


def rotate_original(im,hip):
    colors=np.array(im)
    colors[colors[:,:,3]==0]=0
    pixels=colors.view(np.uint32)[:,:,0]
    for _ in range(3):
        pixels=scale2x(pixels)
    high=Image.fromarray(pixels.view(np.uint8).reshape(1024,1024,4))
    turned=high.rotate(9,NEAREST,center=((64+.5)*8,(hip+.5)*8))
    small=turned.resize((128,128),NEAREST)
    out=im.copy()
    out.paste(small.crop((0,0,128,hip)))
    assert out.crop((0,hip,128,128)).tobytes()==im.crop((0,hip,128,128)).tobytes()
    return out


def main():
    frames=OUT/"frames"
    frames.mkdir(parents=True,exist_ok=True)
    for i in range(8):
        name=f"{i+1:02}.png"
        source=Image.open(HERE.parent/"run8/raw"/name).convert("RGBA")
        rotate_original(source,HIP[i%4]).save(frames/name)
    export(OUT,frames,"原件单次旋转")


if __name__=="__main__":
    main()

