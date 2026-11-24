"""Paint broad closed curves clipped to the three approved material masks.
Coordinates are in the 128-unit design canvas, exported at 8x.
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
p = Path(__file__).resolve().parent
materials = {
    'hair': ((69,78,72), (51,63,60)),
    'skin': ((234,193,157), (204,163,139)),
    'gown': ((231,223,207), (196,194,181)),
}
# Start point followed by cubic Bezier segments (control, control, end).
art = {
'front': {
'hair': [
 [(52,22),(55,16,60,14,65,7),(64,13,60,18,58,23),(60,22,61,21,62,20),(62,24,57,26,52,25)],
 [(67,7),(69,12,70,15,68,19),(67,21,65,23,66,26),(72,26,77,23,77,18),(74,14,73,9,67,7)]],
'skin': [
 [(56,21),(60,23,63,25,66,23),(67,22,69,20,70,18),(72,26,68,28,65,28),(62,28,60,27,58,28)],
 [(70,87),(71,94,70,101,69,106),(68,113,70,121,72,124),(74,122,75,120,74,116),(75,104,80,92,77,85)]],
'gown': [
 [(53,36),(54,39,54,42,56,44),(56,48,54,52,54,57),(52,53,51,45,48,43),(49,42,53,44,53,42),(54,40,53,38,53,36)],
 [(71,33),(74,36,72,41,72,43),(71,53,75,61,75,70),(75,77,76,82,74,85),(77,85,80,85,82,82),(80,64,76,53,75,45),(75,43,78,43,80,42),(78,41,76,42,75,41),(76,38,74,34,71,33)],
 [(45,84),(52,86,57,86,61,85),(65,84,69,87,75,85),(78,85,80,84,82,84),(83,90,51,93,45,88)] ]},
'right': {
'hair': [[(50,21),(56,17,62,17,66,11),(65,16,62,20,62,22),(66,20,67,17,69,16),(68,22,65,26,61,28),(56,28,51,25,50,21)]],
'skin': [
 [(59,21),(63,22,66,25,69,25),(70,25,72,24,73,23),(72,26,68,27,67,28),(66,29,67,30,67,31),(62,30,59,28,59,21)],
 [(59,87),(62,88,64,88,65,88),(66,96,61,100,62,106),(63,113,61,119,63,124),(62,125,61,125,59,124),(58,112,54,100,59,87)]],
'gown': [
 [(63,33),(66,34,67,37,66,40),(65,43,66,45,66,48),(66,58,67,63,69,69),(64,66,60,60,58,52),(56,48,56,45,56,43),(60,43,63,43,65,41),(65,38,65,36,63,33)],
 [(55,55),(59,62,58,76,60,82),(61,85,66,86,70,86),(74,86,75,85,76,84),(78,89,62,92,52,88),(51,74,53,60,55,55)] ]},
'back': {
'hair': [[(50,18),(57,18,65,17,69,12),(68,15,66,18,64,19),(70,18,72,16,74,14),(73,19,71,22,74,23),(70,27,55,28,50,23)]],
'skin': [[(57,23),(62,24,68,23,70,22),(69,25,66,26,65,28),(63,28,61,27,59,27)],
 [(54,86),(56,88,58,89,59,89),(57,96,58,101,58,104),(59,112,56,118,57,123),(55,125,53,123,52,121),(52,108,50,96,54,86)]],
'gown': [
 [(57,32),(54,36,56,40,56,44),(55,52,53,60,53,70),(52,78,51,84,54,85),(52,86,48,85,46,84),(46,64,52,53,52,45),(53,43,50,43,48,42),(51,42,53,41,54,40),(53,37,54,34,57,32)],
 [(74,35),(74,39,75,41,79,42),(77,44,75,44,74,48),(73,52,74,55,75,57),(72,51,71,44,73,40),(74,38,74,36,74,35)],
 [(46,84),(53,86,58,85,62,85),(66,86,68,86,72,85),(75,85,79,85,82,83),(84,90,53,92,46,88)] ]}}
views = [('front','正面','protagonist_front_c_raw_v2/B_original.png'),('right','人物右侧','protagonist_side_eye_v4/side.png'),('back','背面','protagonist_back_v1/back.png')]
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
sheet=Image.new('RGB',(1260,464),'#65726e')
draw=ImageDraw.Draw(sheet)
for i,(name,title,source) in enumerate(views):
    flat=Image.open(p.parent/'protagonist_model_flats_v1'/(name+'.png')).convert('RGBA')
    src=np.asarray(flat); out=src.copy()
    for material,shapes in art[name].items():
        mask=Image.new('1',flat.size); brush=ImageDraw.Draw(mask)
        for start,*segments in shapes:
            a=np.array(start); points=[tuple(a*8)]
            for seg in segments:
                b,c,d=np.array(seg).reshape(3,2)
                for t in np.linspace(0,1,32)[1:]:
                    points.append(tuple(8*((1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d)))
                a=d
            brush.polygon(points,fill=1)
        base,dark=materials[material]
        used=np.asarray(mask)&np.all(src[:,:,:3]==base,axis=2)&(src[:,:,3]>0)
        assert used.any()
        out[used,:3]=dark
    assert np.array_equal(out[:,:,3],src[:,:,3])
    im=Image.fromarray(out); im.save(p/(name+'.png'))
    for j,(pic,s,label) in enumerate([(Image.open(p.parent/source).convert('RGBA'),1,'像素定稿'),(flat,8,'三色平涂'),(im,8,'结构暗面')]):
        crop=pic.crop((42*s,0,86*s,128*s)).resize((132,384),Image.Resampling.NEAREST if s==1 else Image.Resampling.LANCZOS)
        x=i*420+j*140+4
        sheet.paste(crop,(x,34),crop)
        draw.text((x+66,430),label,font=font,anchor='mt',fill='white')
    draw.text((i*420+210,5),title,font=font,anchor='mt',fill='white')
sheet.save(p/'comparison.png')
