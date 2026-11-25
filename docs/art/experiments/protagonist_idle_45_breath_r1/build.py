"""Six native-pixel idle exposures from the selected D, with a planted foot pivot."""
from pathlib import Path
from shutil import copyfile
from tempfile import gettempdir

import numpy as np
from PIL import Image, ImageDraw, ImageSequence

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "protagonist_idle_pose_45_r1/D/raw/01.png"
OUT = HERE / "45"
DURATION = [600, 500, 500, 300, 500, 400]
# Shoulder, head/hands, fringe, free knee, free heel (native px).
POSES = [(0,0,0,0,0), (1,0,0,0,0), (1,1,0,1,0),
         (1,1,1,1,1), (0,1,1,1,1), (0,0,1,0,0)]
Y, X = np.indices((128,128))


def exposure(src, pose):
    shoulder, head, tips, knee, heel = pose
    sy, sx = Y.copy(), X.copy()
    sy[Y < 27] += head
    # Repeat the waist row during inhalation to lengthen the torso.
    sy[(Y >= 27) & (Y < 54)] += shoulder
    # Separate sleeves, forearms and hands at the outer garment fold.
    arm = ((X <= np.interp(Y, [45,52,59,66,75], [54,53,51,50,49])) |
           (X >= np.interp(Y, [45,52,59,66,75], [72,74,74,74,73])))
    sy[arm & (Y >= 46) & (Y < 64)] = Y[arm & (Y >= 46) & (Y < 64)] + shoulder
    hand = arm & (Y >= 64) & (Y <= 75)
    sy[hand] = Y[hand] + head
    hair = (((X >= 50) & (X <= 54) & (Y >= 13) & (Y < 18)) |
            ((X >= 53) & (X <= 56) & (Y >= 21) & (Y <= 25)) |
            ((X >= 69) & (X <= 74) & (Y >= 21) & (Y <= 25)))
    sy[hair] = Y[hair] + tips
    # Shift the relaxed knee inward with the thigh and calf tethered at both ends.
    leg = (X < 63) & (Y >= 87) & (Y < 116)
    bend = np.interp(Y, [87,96,103,115], [0,1,1,0])
    sx[leg] -= np.rint(bend[leg] * knee).astype(int)
    # Foot pitches around the ball. Screen-left toe and the supporting sole stay registered.
    rear_foot = (X < 63) & (Y >= 108) & (Y <= 123)
    lift = np.clip((X-52)/7,0,1) * np.clip((Y-108)/9,0,1)
    sy[rear_foot] += np.rint(lift[rear_foot] * heel).astype(int)
    out = src[sy,sx]
    face = (Y < 26) & ~hair
    assert np.array_equal(out[face], src[Y[face]+head, X[face]])
    fy,fx = np.where((Y<26) & (src[:,:,3]>0) &
                     (src[:,:,0].astype(int)-src[:,:,1].astype(int)>=14))
    assert np.array_equal(out[fy-head,fx],src[fy,fx])
    fixed = ((Y >= 76) & (Y < 87)) | ((Y >= 87) & (X >= 63)) | ((Y >= 119) & (X <= 53))
    assert np.array_equal(out[fixed], src[fixed])
    return out


def loop(images, path):
    images[0].save(path,save_all=True,append_images=images[1:],loop=0,duration=DURATION,
                   disposal=2,optimize=False)
    with Image.open(path) as gif:
        assert gif.n_frames == 6 and gif.info["loop"] == 0
        assert [f.info["duration"] for f in ImageSequence.Iterator(gif)] == DURATION


def build():
    OUT.mkdir(exist_ok=True)
    src = np.array(Image.open(SOURCE).convert("RGBA"))
    tiles = []
    for n,pose in enumerate(POSES,1):
        a = exposure(src,pose)
        path = OUT / f"{n:02}.png"
        if n==1:
            assert np.array_equal(a,src)
            copyfile(SOURCE,path)
        else:
            Image.fromarray(a).save(path)
        im = Image.open(path).convert("RGBA")
        tile = Image.new("RGB",im.size,"#555b5e")
        tile.paste(im, mask=im.getchannel("A"))
        tiles.append(tile)
    for scale in (1,3):
        loop([f.resize((128*scale,128*scale),Image.Resampling.NEAREST) for f in tiles],
             OUT/f"breath_{scale}x.gif")
    sheet = Image.new("RGB",(6*132,282),"#404547")
    pen = ImageDraw.Draw(sheet)
    for i, tile in enumerate(tiles):
        x=132*i
        sheet.paste(tile.crop((31,0,96,128)).resize((130,256),Image.Resampling.NEAREST),(x,24))
        pen.text((x+5,5),f"{i+1:02}    {DURATION[i]} ms",fill="#f0ebe0")
    sheet.save(OUT/"six_frames.png")


def room_preview():
    shots = Path(gettempdir()) / "eor_idle45_breath_review"
    crops = [Image.open(shots / f"45_{i:02}.png").convert("RGB").crop((535,244,745,510)) for i in range(1,7)]
    atlas = Image.new("RGB",(210,266*6))
    for i, tile in enumerate(crops):
        atlas.paste(tile,(0,i*266))
    palette = atlas.quantize(colors=256)
    loop([im.quantize(palette=palette,dither=Image.Dither.NONE) for im in crops], OUT/"room_native.gif")


if __name__ == "__main__":
    import sys
    room_preview() if "--room" in sys.argv else build()
