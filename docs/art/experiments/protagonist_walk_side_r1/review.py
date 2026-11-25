"""Review three consecutive seam samples. All transforms here are for measurement or display."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent
groups = ("B", "side")
frames = (8, 1, 2)
ref = Image.open(root.parent / "protagonist_front_c_raw_v2/B_original.png").convert("RGBA")
arr = np.array(ref)
palette = np.unique(arr[arr[:, :, 3] == 255, :3], axis=0)
small = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 16)
large = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 21)
bg = "#333939"
labels = {"B": "B 正面参照", "side": "90° 侧面参照"}

def load(group, frame):
    return Image.open(root / f"raw_{group}_{frame:02}.png").convert("RGBA")

def head_patch(im):
    top = im.getbbox()[1]
    # Exclude the lower neck, shoulders and background below the chin.
    return im.crop((0, top, 128, top + 22))

def metrics(group):
    ref_head = np.array(head_patch(load(group, 1)))
    result = {}
    overlays = []
    for i in frames:
        sprite = load(group, i)
        patch = head_patch(sprite)
        pixels = np.array(patch)
        # Search integer translation only, optimizing the head silhouette.
        def score(dx):
            a = np.roll(pixels[:, :, 3], dx, axis=1) > 127
            b = ref_head[:, :, 3] > 127
            return np.count_nonzero(a ^ b), abs(dx)
        dx = min(range(-12, 13), key=score)
        registered = np.roll(pixels, dx, axis=1)
        active = (registered[:, :, 3] > 127) | (ref_head[:, :, 3] > 127)
        def quantize(a):
            rgb = a[:, :, :3].astype("int32")
            return np.where(a[:, :, 3] > 127, ((rgb[:, :, None] - palette) ** 2).sum(axis=3).argmin(axis=2), -1)
        q1, qi = quantize(ref_head), quantize(registered)
        result[i] = {
            "shift_x": dx, "shift_y": load(group, 1).getbbox()[1] - sprite.getbbox()[1],
            "changed_rgba": int(np.count_nonzero(np.any(registered != ref_head, axis=2) & active)),
            "changed_B_palette": int(np.count_nonzero(q1 != qi)),
            "silhouette_xor": int(np.count_nonzero((q1 == -1) ^ (qi == -1))),
            "union_pixels": int(active.sum()),
        }
        mask1, maski = ref_head[:, :, 3].astype(float)/255, registered[:, :, 3].astype(float)/255
        onion = np.stack([210 * mask1 + 20, 200 * maski + 22, 207 * maski + 20], axis=2).astype("uint8")
        overlays.append(Image.fromarray(onion).crop((42,0,86,22)))
    return result, overlays

def board(index, zoom):
    w, h = 128*zoom, 128*zoom
    im = Image.new("RGB", (w*2, h+42), bg)
    pen = ImageDraw.Draw(im)
    for col, g in enumerate(groups):
        a = load(g, index).resize((w,h),Image.Resampling.NEAREST)
        im.paste(a,(col*w,39),a)
        pen.text((col*w+w//2,4),labels[g],anchor="mt",font=large if zoom==3 else small,fill="white")
    return im

records = {}
onions = Image.new("RGB",(3*176,2*122),bg)
sheet = Image.new("RGB",(3*384,2*416),bg)
for j,g in enumerate(groups):
    records[g], os = metrics(g)
    for k,i in enumerate(frames):
        pic=load(g,i).resize((384,384),Image.Resampling.NEAREST)
        sheet.paste(pic,(k*384,416*j+32),pic)
        ImageDraw.Draw(sheet).text((k*384+192,416*j+4),f"{labels[g]}   ·   {i:02}",font=large,anchor="mt",fill="white")
        onions.paste(os[k].resize((176,88),Image.Resampling.NEAREST),(176*k,j*122+32))
        ImageDraw.Draw(onions).text((176*k+88,j*122+4),f"{labels[g]}   {i:02}",font=small,anchor="mt",fill="white")
sheet.save(root/"pilot_frames_3x.png")
onions.save(root/"head_onion_4x.png")
# A reverse pass avoids displaying an invented 02→08 jump. APNG timing is in milliseconds.
for zoom in (1,3):
    seq=[board(i,zoom) for i in (8,1,2,1)]
    seq[0].save(root/f"pilot_{zoom}x.png",save_all=True,append_images=seq[1:],duration=[81,81,81,82],loop=0)
    # GIF compatibility for desktop chat previews. Mean 81.25 ms over 16 frames.
    seq=(seq*4)
    ds=[(round((i+1)*8.125)-round(i*8.125))*10 for i in range(16)]
    seq[0].save(root/f"pilot_{zoom}x.gif",save_all=True,append_images=seq[1:],duration=ds,loop=0,disposal=2)
(root/"pilot_metrics.json").write_text(json.dumps(records,indent=2),encoding="utf-8")
print(json.dumps(records))

# Diagnostic for the proposed head lock. Transplant the winning pilot's first
# head at the registered position; quantize the body to B. It is not a final cel.
fixed = []
fixed_head = head_patch(load("side",1))
for frame in (8,1,2,1):
    img = load("side",frame)
    top = img.getbbox()[1]
    img.paste((0,0,0,0), (0,0,128,top+22))
    img.paste(fixed_head, (-records["side"][frame]["shift_x"],top))
    a = np.array(img)
    mask = a[:,:,3] > 127
    delta = a[mask,:3].astype("int32")[:,None,:] - palette
    a[mask,:3] = palette[(delta**2).sum(axis=2).argmin(axis=1)]
    a[~mask] = 0
    tile = Image.fromarray(a).resize((384,384),Image.Resampling.NEAREST)
    diag = Image.new("RGB",(384,416),bg)
    diag.paste(tile,(0,32),tile)
    ImageDraw.Draw(diag).text((192,4),"固定头部＋统一 17 色   ·   诊断",font=large,anchor="mt",fill="white")
    fixed.append(diag)
fixed[0].save(root/"head_lock_diagnostic.gif",save_all=True,append_images=(fixed*4)[1:],duration=ds,loop=0,disposal=2)
strip = Image.new("RGB",(1152,416),bg)
for j,pic in enumerate(fixed[:3]):
    strip.paste(pic,(j*384,0))
strip.save(root/"head_lock_frames.png")
