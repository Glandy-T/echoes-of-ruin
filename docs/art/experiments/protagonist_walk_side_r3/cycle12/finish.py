"""Finish the actual PixelLab outputs and export the 12-frame review."""
import csv
import sys

import numpy as np
from PIL import Image, ImageDraw
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from api_input import HERE, build_request
from review import contact_toes, matte

sys.path.insert(0, str(HERE.parent / "step6"))
from make_step import HEAD_Y, HEAD_X, NAMES, head_and_tips, shifted

SKIN = np.array([tuple(bytes.fromhex(s)) for s in (
    "54504a", "6f635d", "897069", "99807b", "9d8075", "a2857a",
    "af8e7e", "be9981", "c5a891", "e6bd97")], dtype=np.uint8)
YY, XX = np.mgrid[:128, :128]


def distance(bones):
    distances = []
    for (x, y), (u, v) in zip(bones, bones[1:]):
        dx, dy = u - x, v - y
        t = np.clip(((XX-x)*dx + (YY-y)*dy) / max(1, dx*dx+dy*dy), 0, 1)
        distances.append(np.hypot(XX-x-dx*t, YY-y-dy*t))
    return np.min(distances, axis=0)


def separate_limbs(image, pose):
    a = np.array(image)
    rgb = a[:, :, :3].copy()
    ids = np.full(a.shape[:2], -1)
    for i, color in enumerate(SKIN):
        ids[np.all(rgb == color, axis=2) & (a[:, :, 3] > 0)] = i
    for sections, is_leg in [(("HIP", "KNEE", "LEG"), True),
                             (("SHOULDER", "ELBOW", "ARM"), False)]:
        depths = []
        for side in ("LEFT", "RIGHT"):
            bones = [pose[side+" "+label] for label in sections]
            if is_leg:
                x, y = bones[-1]
                bones.append((x-9, y+5))
            depths.append(distance(bones))
        region = (YY >= 76) if is_leg else ((YY >= 39) & (YY < 76))
        # At crossings the visible near limb occupies its full width.
        near = (depths[0] < 3.6) | (depths[0] <= depths[1])
        for on_near, target in [(True, 9), (False, 4)]:
            mask = region & (ids >= 0) & (near == on_near)
            if not np.any(mask):
                continue
            main_tone = int(np.quantile(ids[mask], .75, method="nearest"))
            new_ids = np.clip(ids[mask]+target-main_tone,
                              3 if on_near else 1, 9 if on_near else 5)
            a[mask, :3] = SKIN[new_ids]
    return Image.fromarray(a)


def lock_head(image, idle, phase):
    dy = HEAD_Y[phase]
    # Register the approved face to the generated pose, with the crown at its
    # measured height. Only the head above the narrow neck seam is replaced.
    dx = (0,-2,-1,0,0,0)[phase]
    head = Image.new("RGBA", idle.size)
    head.paste(idle.crop((0, 0, 128, 27)))
    face, tips = head_and_tips(head, phase)
    extra_x = dx - HEAD_X[phase]
    face = shifted(Image.alpha_composite(face, tips), extra_x, 0)
    result = image.copy()
    result.paste(face.crop((0, 0, 128, 26+dy)), (0, 0))
    tip = (76+dx+int(phase in (2, 4)), 13+HEAD_Y[(phase-1) % 6])
    assert result.getpixel(tip) == idle.getpixel((76,13))
    return result, tip


def settle_hem(image):
    # The far-side contact was wider than its loading frame. Extend the
    # generated lower folds only at loading, tapering into thigh and waist.
    out = image.copy()
    for y in range(73,90):
        pad = min(2,(y-72)//3,(90-y)//2)
        if pad:
            strip = image.crop((42,y,78,y+1)).resize((36+pad*2,1),Image.Resampling.NEAREST)
            out.paste(strip,(42-pad,y))
    return out


def settle_planted_foot(image, shift):
    out = image.copy()
    # At these two poses the forward calf is separated from the swinging leg.
    for y in range(98,128):
        dx = round(shift*min(1,(y-98)/18))
        if dx:
            out.paste(image.crop((22,y,62,y+1)),(22+dx,y))
    return out


def save_gif(images, name, period):
    ticks = [round(i*period*100/len(images)) for i in range(len(images)+1)]
    delays = [10*(b-a) for a,b in zip(ticks, ticks[1:])]
    file = HERE/name
    images[0].save(file, save_all=True, append_images=images[1:], loop=0, duration=delays, disposal=2)
    with Image.open(file) as gif:
        assert gif.n_frames == len(images) and gif.info["loop"] == 0
        for i, image in enumerate(images):
            gif.seek(i)
            assert gif.info["duration"] == delays[i]
            assert gif.convert("RGB").tobytes() == image.convert("RGB").tobytes()


def export():
    raw = [Image.open(HERE/"raw"/f"{i:02}.png").convert("RGBA") for i in range(1,13)]
    idle = Image.open(HERE.parents[1]/"protagonist_five_idle_eyes_r3/final_90.png").convert("RGBA")
    poses = build_request()["keypoints"]
    final, rows = [], []
    for i, original in enumerate(raw):
        pose = {k["label"]: (round(k["x"]*128-.5),round(k["y"]*128-.5)) for k in poses[i]}
        image, tip = lock_head(separate_limbs(original, pose), idle, i%6)
        if i in (1,2):
            image = settle_planted_foot(image, 4 if i == 1 else 2)
        if i == 6:  # The weight-bearing forefoot was two pixels above ground.
            sole = image.crop((24,113,54,125)).resize((30,14),Image.Resampling.NEAREST)
            image.paste(sole,(24,113))
        if i == 7:
            image = settle_hem(image)
        if i == 11:  # Extend the four remaining sole pixels onto the ground line.
            image.paste(image.crop((68,125,72,126)), (68,126))
        final.append(image)
        (HERE/"frames").mkdir(exist_ok=True)
        image.save(HERE/"frames"/f"{i+1:02}.png")
        hip_y = (pose["RIGHT HIP"][1]+pose["LEFT HIP"][1])/2
        rows.append([i+1,NAMES[i%6],image.getbbox()[1],hip_y,*tip,image.getbbox()[3]-1])
    front, opposite = [contact_toes(final[i]) for i in (0,6)]
    steps = [opposite[1]-front[0],front[1]-opposite[0]]
    period = sum(steps)*1.65/125/1.1
    print("contact toes",front,opposite,"steps",steps,"period",period,"fps",12/period)
    with (HERE/"heights.csv").open("w", newline="") as file:
        out = csv.writer(file)
        out.writerow(["frame","pose","crown_y","rig_mid_hip_y","rear_tip_x","rear_tip_y","lowest_foot_y"])
        out.writerows(rows)
    fig, ax = plt.subplots(figsize=(9,3.5),layout="constrained")
    for col, label, marker in [(2,"Crown (pixels)","o"),(3,"Pelvis (rig midpoint)","s"),(5,"Rear hair tip (pixels)","^")]:
        ax.plot(range(1,13),[rows[0][col]-r[col] for r in rows],marker=marker,label=label,alpha=.85)
    ax.axvline(6.5,color="grey",ls=":",lw=1)
    ax.set(xticks=range(1,13),yticks=range(-3,2),xlabel="Frame",ylabel="Height relative to contact (px)")
    ax.grid(alpha=.2)
    ax.legend(ncol=3,loc="lower center",bbox_to_anchor=(.5,1))
    fig.savefig(HERE/"heights.png",dpi=155)
    plt.close(fig)
    native = [matte(im) for im in final]
    save_gif(native,"walk_1x.gif",period)
    save_gif([im.resize((384,384),Image.Resampling.NEAREST) for im in native],"walk_3x.gif",period)
    save_gif([matte(im) for im in raw],"raw.gif",period)
    sheet = Image.new("RGB",(6*192,2*215),"#414548")
    pen = ImageDraw.Draw(sheet)
    for i,im in enumerate(native):
        x,y=i%6*192,i//6*215
        sheet.paste(im.resize((192,192),Image.Resampling.NEAREST),(x,y))
        pen.text((x+48,y+194),f"{i+1:02}  {NAMES[i%6]}",fill="white")
    sheet.save(HERE/"poses.png")
    # Common cycle clock; map the actual r2 contacts (frames 1 and 4) to r3.
    r2 = HERE.parents[1]/"protagonist_walk_side_r2"
    panels = []
    for i,im in enumerate(native):
        old = (1,1,2,2,3,3,4,5,6,6,7,8)[i]
        left = matte(Image.open(r2/f"cycle_{old:02}.png").convert("RGBA"))
        panel = Image.new("RGB",(512,276),"#414548")
        for x, p, label in [(0,left,"r2  /  text"),(256,im,"r3  /  skeleton")]:
            panel.paste(p.resize((256,256),Image.Resampling.NEAREST),(x,20))
            ImageDraw.Draw(panel).text((x+10,4),label,fill="white")
        panels.append(panel)
    save_gif(panels,"r2_r3.gif",period)
    print(rows)


if __name__ == "__main__":
    export()
