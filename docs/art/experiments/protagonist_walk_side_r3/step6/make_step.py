"""Build the stepped review and editable Pixelorama timeline from the r3 source art."""
import ast
import csv
import io
import json
from copy import deepcopy
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "walk_r3_pilot.pxo"
SIZE = (128, 128)
DURATION = 1.068 / 12  # Use the accepted r3 preview clock until both painted contacts exist.
BODY_Y = (0, 3, 1, 0, -1, 0)
HEAD_Y = (0, 2, 1, 0, -1, 0)
HEAD_X = (0, -1, 0, 0, 0, 0)
BG = "#424a4b"
ZOOM = Image.Resampling.NEAREST
NAMES = ("Contact", "Down", "Recover", "Passing", "Up", "Reach")


def empty():
    return Image.new("RGBA", SIZE)


def shifted(image, dx, dy):
    out = empty()
    out.paste(image, (int(dx), int(dy)))
    return out


def layer(archive, metadata, frame, number):
    cel = metadata["frames"][frame - 1]["cels"][number - 1]
    size = ast.literal_eval(cel["image_size"].removeprefix("Vector2i"))
    local = Image.frombytes("RGBA", size, archive.read(f"image_data/frames/{frame}/layer_{number}"))
    out = empty()
    out.paste(local, ast.literal_eval(cel["offset"]))
    return out


def point(x, y):
    return np.array([x, y], dtype=float)


def rotation(degrees):
    a = np.deg2rad(degrees)
    return np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])


def orient(src, dst):
    angle = np.arctan2(dst[1], dst[0]) - np.arctan2(src[1], src[0])
    return rotation(np.rad2deg(angle)) * (np.linalg.norm(dst) / np.linalg.norm(src))


def warp_limb(texture, source, target, foot_rotation=None):
    """Skin a strip to the upper and lower bones; sample the native texels once."""
    a, b, c = source
    p, q, r = target
    upper, lower = orient(b-a, q-p), orient(c-b, r-q)
    rows = sorted(set([int(a[1])-8, int(a[1]), int(b[1])-3, int(b[1]), int(b[1])+3,
                       int(c[1])-3, int(c[1]), int(c[1])+2, int(c[1])+10]))
    xmin, _, xmax, _ = texture.getbbox()
    source_rows, dest_rows = [], []
    for y in rows:
        s = np.array([[xmin-1, y], [xmax+1, y]], dtype=float)
        u = np.clip((y-b[1]+3)/6, 0, 1)
        v = (1-u)*((s-a) @ upper.T+p) + u*((s-b) @ lower.T+q)
        if foot_rotation is not None:
            w = np.clip((y-c[1]+3)/5, 0, 1)
            v = (1-w)*v + w*((s-c) @ foot_rotation.T+r)
        source_rows.append(s)
        dest_rows.append(v)
    pixels = np.asarray(texture)
    result = np.zeros((128, 128, 4), dtype=np.uint8)
    for i in range(len(rows)-1):
        src = np.vstack((source_rows[i], source_rows[i+1]))
        dst = np.vstack((dest_rows[i], dest_rows[i+1]))
        for indices in ([0, 1, 2], [1, 3, 2]):
            s, d = src[indices], dst[indices]
            x0, y0 = np.maximum(0, np.floor(d.min(axis=0)).astype(int))
            x1, y1 = np.minimum(127, np.ceil(d.max(axis=0)).astype(int))
            mat = (d[1:] - d[0]).T
            if x0 > x1 or y0 > y1 or abs(np.linalg.det(mat)) < 1e-8:
                continue
            yy, xx = np.mgrid[y0:y1+1, x0:x1+1]
            uv = (np.stack((xx, yy), axis=-1)-d[0]) @ np.linalg.inv(mat).T
            inside = (uv >= -1e-7).all(axis=2) & (uv.sum(axis=2) <= 1+1e-7)
            xy = np.rint(uv[inside] @ (s[1:]-s[0]) + s[0]).astype(int).clip(0, 127)
            result[yy[inside], xx[inside]] = pixels[xy[:, 1], xy[:, 0]]
    return Image.fromarray(result)


def extract_art(idle, contact):
    raw = np.asarray(idle)
    head = empty()
    head.paste(idle.crop((0, 0, 128, 27)))
    dress = empty()
    dress.paste(idle.crop((0, 26, 128, 88)), (0, 26))
    arm_mask = Image.new("1", SIZE)
    outline = [(65,30),(69,31),(72,34),(73,40),(72,44),(70,53),(69,59),(67,66),
               (66,75),(64,76),(60,76),(58,72),(59,68),(61,65),(62,60),(63,55),
               (64,49),(64,45),(61,43),(61,39),(63,34)]
    ImageDraw.Draw(arm_mask).polygon(outline, fill=1)
    arm = Image.composite(idle, empty(), arm_mask)
    # Continue the gown panel under the cut-out sleeve and hand.
    cloth = np.array(dress)
    for y, x in zip(*np.where(np.asarray(arm_mask) & (raw[:, :, 3] != 0))):
        cloth[y, x] = raw[77, int(np.clip(x, 54, 72))]
    dress = Image.fromarray(cloth)
    leg = empty()
    leg.paste(contact.crop((28, 88, 57, 126)), (28, 88))
    # Continue the thigh behind the hem, using the same source strip for both legs.
    for y in range(55, 88):
        strip = contact.crop((44, 90, 54, 91))
        leg.paste(strip, (44+round((90-y)*0.39), y))
    return head, dress, arm, leg


def far_shade(tex):
    a = np.array(tex)
    old = a.copy()
    # The darker values are all sampled from the previous PixelLab artwork.
    pairs = {"e6bd97":"af8e7e","c5a891":"a2857a","be9981":"99807b","af8e7e":"897069",
             "a2857a":"897069","9d8075":"74605d","99807b":"74605d","e4ddcb":"bcb4a3",
             "bcb4a3":"8f9488","8f9488":"7c8b85","7c8b85":"667167"}
    for light, dark in pairs.items():
        mask = (old[:, :, :3] == tuple(bytes.fromhex(light))).all(axis=2) & (old[:, :, 3] != 0)
        a[mask, :3] = tuple(bytes.fromhex(dark))
    return Image.fromarray(a)


def head_and_tips(head, phase):
    dx, dy = HEAD_X[phase], HEAD_Y[phase]
    lag = HEAD_Y[(phase-1) % 6] - dy
    drift = int(phase in (2, 4))
    # Coordinates in the unshifted approved idle. The root texels stay on the skull.
    rear = [(74,11),(74,12),(75,12),(75,13),(76,13)]
    fringe = [(53,11),(52,12),(51,13)]
    face = head.copy()
    tips = empty()
    for strand in (rear, fringe):
        for x, y in strand:
            face.putpixel((x,y), (0,0,0,0))
        for index,(x,y) in enumerate(strand):
            factor = (index+1) / len(strand)
            tx = x+dx+round(drift*factor)
            ty = y+dy+round(lag*factor)
            tips.putpixel((tx,ty),head.getpixel((x,y)))
    return shifted(face, dx, dy), tips


def garment(dress, phase):
    # Widest silhouette one exposure after maximum leg separation at contact.
    spread = (2, 3, 2, 1, 0, 1)[phase]
    trail = (1, 2, 2, 1, 0, 0)[phase]
    dy = BODY_Y[phase]
    result = empty()
    for y in range(26, 88):
        weight = max(0, (y-54)/33)
        extra = round(spread*weight)
        wind = round(trail*weight)
        strip = dress.crop((48,y,79,y+1)).resize((31+2*extra, 1), ZOOM)
        result.paste(strip, (48-extra+wind, y+dy))
    # One neck row covers the 1 px difference in chest and head descent.
    if dy > HEAD_Y[phase]:
        result.paste(dress.crop((0,26,128,27)), (0,26+dy-1))
    return result


LEG_SOURCE = (point(61,60), point(49,90), point(42,119))
ARM_SOURCE = (point(67,33), point(67,53), point(62,72))


def leg_pose(phase, support, near, tex):
    # Foot roll changes the ankle-to-toe offset. Set the stride at the visible forefoot.
    y = BODY_Y[phase]
    hip = point(63 if near else 61, 60+y)
    if support:
        k = point((54,53,57,62,65,66)[phase], (90,92,93,91,90,89)[phase])
        ankle = point((51,56,60,65,70,75)[phase], 116)
        angle = (11, 3, 0, 0, -8, -18)[phase]
        floor = 126
    else:
        k = point((69,67,62,56,53,52)[phase], (89,92,91,88,87,89)[phase])
        ankle = point((80,79,75,67,60,54)[phase], 115)
        angle = (-24, -32, -37, -26, -10, 8)[phase]
        floor = (126, 122, 119, 117, 119, 123)[phase]
    rot = rotation(angle-14)
    # Anchor rasterized support soles to the common floor, including heel roll.
    target_toe = round(38+32*phase/6) if support else (70 if phase==0 else None)
    for _ in range(8):
        im = warp_limb(tex, LEG_SOURCE, (hip,k,ankle), rot)
        correction = floor-(im.getbbox()[3]-1)
        if target_toe is not None:
            band = np.array(im)[116:,:,3]
            x_correction = target_toe-int(np.nonzero(band)[1].min())
        else:
            x_correction = 0
        if not correction and not x_correction:
            break
        ankle[1] += correction
        ankle[0] += x_correction
    if correction:
        assert abs(correction) == 1
        im = shifted(im, 0, correction)
    assert im.getbbox()[3]-1 == floor
    if target_toe is not None:
        residual = target_toe-int(np.nonzero(np.array(im)[116:,:,3])[1].min())
        if residual:
            assert abs(residual) <= 1
            im = shifted(im, residual, 0)
        assert np.nonzero(np.array(im)[116:,:,3])[1].min() == target_toe
    return (hip,k,ankle), im


def arm_pose(phase, near, support, tex):
    dy = BODY_Y[phase]
    angle = (16, 14, 8, 1, -8, -14)[phase] * (1 if support else -1)
    shoulder = point(67 if near else 62, 33+dy)
    elbow = shoulder + np.rint(rotation(-angle) @ point(0,20))
    hand = elbow + np.rint(rotation(-angle) @ point(-5,19))
    joints = (shoulder,elbow,hand)
    return joints, warp_limb(tex, ARM_SOURCE, joints)


def skeleton(raw, phase, arms, legs):
    # PixelLab identifies joints by RGB, with the alpha byte retained from its template.
    template = np.array(raw)
    colors = {tuple(template[y,x,:3]): tuple(template[y,x]) for y,x in
              zip(*np.where((template[:,:,3]>0) & (template[:,:,3]<255)))}
    coords = {}
    def pin(rgb, xy):
        coords[rgb] = tuple(map(int, xy))
    for y,x in zip(*np.where((template[:,:,3]>0) & (template[:,:,3]<255))):
        rgb = tuple(template[y,x,:3])
        if y < 20:
            pin(rgb, (int(x)+HEAD_X[phase], int(y)+HEAD_Y[phase]))
    neck = (255,245,0)
    pin(neck,(63,32+BODY_Y[phase]))
    chains = []
    for side, arm_ids, leg_ids in [
        ("near", [(255,9,0),(255,19,0),(255,30,0)], [(255,99,0),(255,109,0),(255,120,0)]),
        ("far", [(0,0,255),(9,0,255),(19,0,255)], [(109,0,255),(120,0,255),(130,0,255)])]:
        for ids,joints in [(arm_ids,arms[side]),(leg_ids,legs[side])]:
            for color,joint in zip(ids,joints):
                pin(color,joint)
            chains.append([neck]+ids)
    im = empty()
    pen = ImageDraw.Draw(im)
    chains += [[(255,0,180),(255,0,189),(0,130,255),(0,120,255),(255,255,0),neck]]
    for chain in chains:
        for a,b in zip(chain,chain[1:]):
            pen.line([coords[a],coords[b]],fill=(*a,255))
    assert len(set(coords.values())) == len(coords) == len(colors)
    for x,y in coords.values():
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            im.putpixel((x+dx,y+dy),(255,255,255,255))
    for rgb,xy in coords.items():
        im.putpixel(xy,colors[rgb])
    return im


def png_bytes(im):
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


LAYERS = ["Approved reference", "Far leg", "Near leg", "Far arm", "Gown",
          "Near arm", "Fixed head artwork", "Hair tips", "Skeleton"]


def write_project(metadata, reference, ref_skeleton, timeline):
    d = deepcopy(metadata)
    d["layers"] = []
    for name in LAYERS:
        entry = deepcopy(metadata["layers"][0])
        entry.update(name=name, visible=name!="Skeleton")
        d["layers"].append(entry)
    d.update(frames=[], fps=1/DURATION, current_frame=1, current_layer=6, tags=[])
    ref = [reference]+[empty() for _ in LAYERS[1:-1]]+[ref_skeleton]
    with ZipFile(ROOT/"step_skeleton.pxo","w", compression=ZIP_DEFLATED) as out:
        out.writestr("mimetype","application/x-pixelorama")
        out.writestr("preview.png",png_bytes(composite(timeline[0])))
        for frame, stack in enumerate([ref]+timeline, start=1):
            cels = []
            for num,im in enumerate(stack,1):
                box = im.getbbox() or (0,0,1,1)
                small = im.crop(box)
                cel = deepcopy(metadata["frames"][0]["cels"][0])
                cel.update(offset=str((box[0],box[1])), image_size=f"Vector2i{small.size}", metadata={})
                cels.append(cel)
                prefix = f"image_data/frames/{frame}/"
                out.writestr(prefix+f"layer_{num}",small.tobytes())
                out.writestr(prefix+f"indices_layer_{num}",bytes(1))
            d["frames"].append(dict(duration=1.0, metadata={}, cels=cels))
        out.writestr("data.json",json.dumps(d,ensure_ascii=False))


def composite(stack):
    out = empty()
    for part in stack[:-1]:
        out.alpha_composite(part)
    return out


def verify_export(timeline):
    pics, readings = [], []
    with ZipFile(ROOT/"step_skeleton.pxo") as archive:
        d = json.loads(archive.read("data.json"))
        assert len(d["frames"]) == 13
        for i,stack in enumerate(timeline):
            saved = [layer(archive,d,i+2,n) for n in range(1,len(LAYERS)+1)]
            assert all(a.tobytes()==b.tobytes() for a,b in zip(saved,stack))
            art = composite(saved)
            if i>=6:
                assert not art.getbbox()
                continue
            # Read measurements from the written cels, independent of the design arrays.
            top = art.getbbox()[1]
            ty,tx = np.where(np.array(saved[7])[:,:,3]>0)
            tip_x = int(tx.max())
            tip_y = int(ty[tx==tip_x].max())
            rgb = np.array(saved[-1])
            hips = []
            for color in [(255,99,0), (109,0,255)]:
                sy,sx = np.where((rgb[:,:,:3]==color).all(axis=2)&(rgb[:,:,3]<255)&(rgb[:,:,3]>0))
                assert len(sy)==1
                hips.append(int(sy[0]))
            readings.append((top,sum(hips)/2,tip_y,tip_x))
            assert art.getpixel((tip_x,tip_y))[3] == 255 and art.getbbox()[3]==127
            pics.append(art)
    offsets = np.array(readings)[0]-readings
    assert np.array_equal(offsets[:,2],np.roll(offsets[:,0],1))
    assert np.ptp(offsets[:,0])==3 and np.ptp(offsets[:,1])==4
    with (ROOT/"landmarks.csv").open("w",encoding="utf-8",newline="") as file:
        w = csv.writer(file)
        w.writerow(["frame","phase","crown_y","pelvis_y","rear_tip_y","rear_tip_x",
                    "crown_height_delta","pelvis_height_delta","rear_tip_height_delta"])
        for i,row in enumerate(readings):
            w.writerow([i+1,NAMES[i],*row,*offsets[i,:3]])
    return pics,offsets


def previews(pics,offsets):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    panel = Image.new("RGB",(6*192,218),BG)
    draw = ImageDraw.Draw(panel)
    enlarged = []
    for i,im in enumerate(pics):
        flat = Image.new("RGB",SIZE,BG)
        flat.paste(im,mask=im.getchannel("A"))
        enlarged.append(flat.resize((384,384),ZOOM))
        panel.paste(flat.resize((192,192),ZOOM),(192*i,0))
        draw.text((192*i+8,198),f"{i+1:02}  {NAMES[i]}",fill="white")
    panel.save(ROOT/"poses.png")
    holds = [10*(round((i+1)*DURATION*100)-round(i*DURATION*100)) for i in range(6)]
    enlarged[0].save(ROOT/"one_step.gif",save_all=True,append_images=enlarged[1:],
                     duration=holds,loop=0,disposal=2)
    with Image.open(ROOT/"one_step.gif") as gif:
        assert gif.n_frames==6 and gif.info["loop"]==0
        for i,frame in enumerate(enlarged):
            gif.seek(i)
            assert gif.info["duration"]==holds[i] and gif.convert("RGB").tobytes()==frame.tobytes()
    font = FontProperties(fname="C:/Windows/Fonts/msyh.ttc")
    fig,ax = plt.subplots(figsize=(7.8,3.3),layout="constrained")
    for column,label,color,marker,style in [(1,"骨盆","#425978","s","-"),(0,"头顶","#b14f30","o","--"),
                                          (2,"后脑发梢","#008175","D",":")]:
        ax.plot(range(1,7),offsets[:,column],style,marker=marker,ms=7,mfc="white",lw=2,
                color=color,label=label)
    ax.set(ylim=(-3.55,1.65),yticks=range(-3,2),xlim=(.8,6.2))
    ax.set_xticks(range(1,7),["01 触地","02 下沉","03 回升","04 经过","05 上升","06 预备触地"],
                  fontproperties=font)
    ax.set_ylabel("相对触地高度（原生 px，向上为正）",fontproperties=font)
    ax.set_title("90° 走路 · 第一步高度实测",fontproperties=font,loc="left",pad=12)
    ax.legend(prop=font,loc="lower right",ncol=3)
    ax.grid(axis="y",alpha=.2)
    ax.spines[["top","right"]].set_visible(False)
    fig.savefig(ROOT/"heights.png",dpi=155)
    plt.close(fig)


def main():
    with ZipFile(SOURCE) as z:
        meta = json.loads(z.read("data.json"))
        idle = layer(z,meta,1,1)
        ref_skeleton = layer(z,meta,1,3)
        template = layer(z,meta,3,3)
        head,dress,arm,leg = extract_art(idle,layer(z,meta,3,2))
    timeline = []
    for i in range(12):
        phase = i%6
        arms,legs,parts = {},{},{}
        for near,side in [(True,"near"),(False,"far")]:
            support = near==(i<6)
            arms[side],parts[side+"arm"] = arm_pose(phase,near,support,arm if near else far_shade(arm))
            legs[side],parts[side+"leg"] = leg_pose(phase,support,near,leg if near else far_shade(leg))
        bones = skeleton(template,phase,arms,legs)
        if i<6:
            face,tips = head_and_tips(head,phase)
            timeline.append([empty(),parts["farleg"],parts["nearleg"],parts["fararm"],garment(dress,phase),
                             parts["neararm"],face,tips,bones])
        else:
            timeline.append([empty() for _ in LAYERS[:-1]]+[bones])
    write_project(meta,idle,ref_skeleton,timeline)
    pics,offsets = verify_export(timeline)
    previews(pics,offsets)


if __name__ == "__main__":
    main()
