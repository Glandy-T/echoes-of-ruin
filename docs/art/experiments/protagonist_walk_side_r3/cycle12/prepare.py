"""Retarget the existing twelve skeleton exposures; leave the drawing cells empty."""
import io
import json
import sys
from copy import deepcopy
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from review import read_layer

NECK = (255,245,0)
NEAR_ARM = [(255,9,0),(255,19,0),(255,30,0)]
FAR_ARM = [(0,0,255),(9,0,255),(19,0,255)]
NEAR_LEG = [(255,99,0),(255,109,0),(255,120,0)]
FAR_LEG = [(109,0,255),(120,0,255),(130,0,255)]
HEAD = [(255,0,180),(255,0,189),(0,130,255),(0,120,255),(255,255,0)]
CHAINS = [HEAD+[NECK]] + [[NECK]+chain for chain in (FAR_ARM, FAR_LEG, NEAR_LEG, NEAR_ARM)]


def joints(im):
    a = np.asarray(im)
    y,x = np.where((a[:,:,3]>0) & (a[:,:,3]<255))
    colors = [tuple(map(int,a[j,i])) for j,i in zip(y,x)]
    assert len(set(c[:3] for c in colors)) == len(colors) == 18
    return {c[:3]: (int(i),int(j)) for i,j,c in zip(x,y,colors)}, {c[:3]: c for c in colors}


def pose(original, frame):
    xy, colors = joints(original)
    phase = frame % 6
    # Negative x is forward. Lean about the hips on the two loading frames.
    lean = (0,-3,-1,0,0,0)[phase]
    xy[NECK] = (xy[NECK][0]+lean, xy[NECK][1])
    for key in HEAD:
        xy[key] = (xy[key][0]+lean, xy[key][1])
    for near,arm,leg in [(True,NEAR_ARM,NEAR_LEG),(False,FAR_ARM,FAR_LEG)]:
        on_ground = near == (frame<6)
        knee_x = ((50,48,54,62,65,68) if on_ground else (72,68,59,54,49,48))[phase]
        ankle_x = ((42,49,57,64,71,79) if on_ground else (86,85,78,68,54,45))[phase]
        xy[leg[1]] = (knee_x,xy[leg[1]][1])
        xy[leg[2]] = (ankle_x,xy[leg[2]][1])
        shoulder = np.array(xy[arm[0]])+[lean,0]
        angle = (27,23,13,0,-13,-23)[phase]*(1 if on_ground else -1)
        rad = np.deg2rad(angle)
        swing = np.array([[np.cos(rad),np.sin(rad)],[-np.sin(rad),np.cos(rad)]])
        elbow = shoulder+np.rint(swing@[0,18]).astype(int)
        wrist = elbow+np.rint(swing@[-5,17]).astype(int)
        for key,pt in zip(arm,(shoulder,elbow,wrist)):
            xy[key] = tuple(map(int,pt))
    assert len(set(xy.values())) == 18
    result = Image.new("RGBA",original.size)
    pen = ImageDraw.Draw(result)
    for chain in CHAINS:
        for a,b in zip(chain,chain[1:]):
            pen.line([xy[a],xy[b]],fill=(*a,255))
    for x,y in xy.values():
        for dx,dy in [(0,-1),(0,1),(-1,0),(1,0)]:
            result.putpixel((x+dx,y+dy),(255,255,255,255))
    for key,pt in xy.items():
        result.putpixel(pt,colors[key])
    assert joints(result)[0] == xy
    return result


def build():
    with ZipFile(HERE.parent/"step6/step_skeleton.pxo") as src:
        old = json.loads(src.read("data.json"))
        bone_index = [l["name"] for l in old["layers"]].index("Skeleton")+1
        bones = [pose(read_layer(src,old,i+2,bone_index),i) for i in range(12)]
    with ZipFile(HERE.parent/"walk_r3_pilot.pxo") as src:
        project = json.loads(src.read("data.json"))
        ref = read_layer(src,project,1,1)
        ref_pose = read_layer(src,project,1,3)
    project["layers"] = [project["layers"][0],project["layers"][2]]
    cel_model = project["frames"][0]["cels"][0]
    project.update(frames=[],current_frame=0,current_layer=0,fps=12/1.056)
    blank = Image.new("RGBA",ref.size)
    source_frames = [(ref,ref_pose)]+[(blank,b) for b in bones]
    destination = HERE/"walk_44_input.pxo"
    with ZipFile(destination,"w",compression=ZIP_DEFLATED) as z:
        z.writestr("mimetype","application/x-pixelorama")
        buf = io.BytesIO()
        ref.save(buf,format="PNG")
        z.writestr("preview.png",buf.getvalue())
        for i,stack in enumerate(source_frames,1):
            cels = []
            for n,im in enumerate(stack,1):
                box = im.getbbox() or (0,0,1,1)
                tile = im.crop(box)
                cel = deepcopy(cel_model)
                cel.update(image_size=f"Vector2i{tile.size}",offset=str(box[:2]),metadata={})
                cels.append(cel)
                path = f"image_data/frames/{i}/"
                z.writestr(path+f"layer_{n}",tile.tobytes())
                z.writestr(path+f"indices_layer_{n}",bytes(1))
            project["frames"].append(dict(duration=1.0,metadata={},cels=cels))
        z.writestr("data.json",json.dumps(project))
    # Check the file that will actually be opened in Pixelorama.
    with ZipFile(destination) as z:
        data = json.loads(z.read("data.json"))
        assert len(data["frames"])==13
        for i,stack in enumerate(source_frames,1):
            for n,im in enumerate(stack,1):
                assert read_layer(z,data,i,n).tobytes()==im.tobytes()
        keyframes = [joints(read_layer(z,data,i,2))[0] for i in range(2,14)]
        for start,end,leg in [(0,6,NEAR_LEG),(6,0,FAR_LEG)]:
            assert keyframes[end][leg[-1]][0]-keyframes[start][leg[-1]][0]==44
        for frame in (1,7):
            assert keyframes[frame][NECK][0]+3==keyframes[frame-1][NECK][0]
    print(destination.name, destination.stat().st_size, "bytes; reference + 12 verified skeletons")


if __name__ == "__main__":
    build()
