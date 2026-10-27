"""Authored edge-connected pixel aging, calibrated between r3 and the reference."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib
ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT.parents[3]
for folder in ['source/layers','editable','evidence','survey']:(ROOT/folder).mkdir(parents=True,exist_ok=True)
OUT=PROJECT/'assets/art/room1_wall_age_r4';OUT.mkdir(parents=True,exist_ok=True)
base=Image.open(PROJECT/'assets/art/room1_wall_joints_r3/wall_sample.png').convert('RGBA')
assert base.size==(256,272)

def canvas():return Image.new('RGBA',base.size,(0,0,0,0))
def stepped_band(draw,anchor,profile,color,up=False,scale=1.0):
    points=[(0,anchor),(255,anchor)]
    contour=[]
    # Broad authored masses carry a finer 1-2px boundary rhythm, rather than
    # turning every control point into a huge rectangular staircase.
    rhythm=[0,-1,1,0,2,-1,0,1,-2,0,1,-1,0,2,0,-1,1,0,-2,1,0]
    section=0
    for i,x in enumerate(list(range(0,255,2))+[255]):
        while section+1<len(profile)-1 and profile[section+1][0]<x:section+=1
        x0,h0=profile[section];x1,h1=profile[min(section+1,len(profile)-1)]
        t=(x-x0)/max(1,x1-x0)
        depth=(h0*(1-t)+h1*t)*scale
        y=anchor+(-1 if up else 1)*max(1,round(depth+rhythm[(i+round(scale*7))%len(rhythm)]))
        if contour:contour.append((x,contour[-1][1]))
        contour.append((x,y))
    draw.polygon(points+list(reversed(contour)),fill=color)

# Distinct, hand-set connected contours. No random dots or copied reference pixels.
top_profile=[(0,5),(12,8),(21,6),(30,12),(39,17),(48,11),(55,19),(69,7),
 (80,12),(91,21),(103,16),(114,9),(129,6),(141,12),(150,18),(161,14),
 (173,8),(181,13),(188,22),(199,15),(212,8),(224,12),(239,5),(255,4)]
foot_profile=[(0,12),(10,16),(22,13),(31,23),(43,30),(54,24),(65,19),(77,28),
 (91,18),(106,15),(119,22),(133,19),(146,31),(158,35),(168,29),(179,22),
 (188,27),(199,34),(209,25),(223,18),(236,13),(248,16),(255,11)]
top=canvas();d=ImageDraw.Draw(top)
stepped_band(d,44,top_profile,'#BBC3B5')
stepped_band(d,44,top_profile,'#A7B3A5',scale=.65)
stepped_band(d,44,top_profile,'#929F94',scale=.25)
foot=canvas();d=ImageDraw.Draw(foot)
stepped_band(d,249,foot_profile,'#B4BCAF',up=True)
stepped_band(d,249,foot_profile,'#9EA99C',up=True,scale=.65)
stepped_band(d,249,foot_profile,'#8B988D',up=True,scale=.27)
# Softer, connected relief at the shoulders of accumulation; never isolated stains.
d.polygon([(35,226),(35,220),(42,220),(42,217),(48,217),(48,222),(54,222),(54,226)],fill='#ADB8AA')
d.polygon([(145,227),(145,222),(152,222),(152,218),(160,218),(160,223),(167,223),(167,229)],fill='#ADB8AA')

film=canvas();d=ImageDraw.Draw(film)
for x,shift in [(64,0),(192,13)]:
    # Dust/old seal-film spreads beside the seam; the approved seam itself stays exact.
    d.polygon([(x-5,69+shift),(x-8,69+shift),(x-8,77+shift),(x-11,77+shift),
      (x-11,90+shift),(x-8,90+shift),(x-8,115+shift),(x-5,115+shift)],fill='#BBC3B5')
    d.polygon([(x-5,128+shift),(x-9,128+shift),(x-9,143+shift),(x-12,143+shift),
      (x-12,158+shift),(x-8,158+shift),(x-8,179+shift),(x-5,179+shift)],fill='#B0BBAE')
    d.polygon([(x+4,100-shift),(x+7,100-shift),(x+7,114-shift),(x+10,114-shift),
      (x+10,129-shift),(x+8,129-shift),(x+8,147-shift),(x+4,147-shift)],fill='#B7C0B2')
    d.polygon([(x+4,194-shift),(x+8,194-shift),(x+8,205-shift),(x+11,205-shift),
      (x+11,224-shift),(x+7,224-shift),(x+7,241),(x+4,241)],fill='#A8B4A6')
metal=canvas();d=ImageDraw.Draw(metal)
d.polygon([(31,259),(44,259),(44,258),(65,258),(65,260),(81,260),(81,263),
 (66,263),(66,264),(43,264),(43,262),(31,262)],fill='#617975')
d.polygon([(132,260),(143,260),(143,259),(164,259),(164,261),(182,261),
 (182,264),(159,264),(159,265),(141,265),(141,263),(132,263)],fill='#5A7371')
d.line((47,255,64,255),fill='#B6C1AF');d.line((142,255,160,255),fill='#AFBDAA')

layers=[('upper_recess_deposit',top),('lower_wall_accumulation',foot),
        ('joint_edge_old_film',film),('metal_old_contact',metal)]
protected=np.zeros((272,256),bool);protected[18:36,:]=True
for x in [64,192]:protected[44:249,x-4:x+4]=True
result=base
for name,layer in layers:
    a=np.asarray(layer).copy()
    # Return to the inherited prototype at its ends, without rectangular patch cuts.
    for x in range(256):
        t=min(1,max(0,(min(x,255-x)-6)/22))
        a[:,x,3]=(a[:,x,3].astype(float)*(round(t*8)/8)).astype('uint8')
    a[protected,3]=0
    layer=Image.fromarray(a);layer.save(ROOT/'source/layers'/f'{name}.png')
    result=Image.alpha_composite(result,layer)
result.convert('RGB').save(OUT/'wall_sample.png')
for label,image in [('r3',base),('r4',result)]:
    image.convert('RGB').resize((768,816),Image.Resampling.NEAREST).save(ROOT/'evidence'/f'wall_{label}_native_3x.png')
changed=(np.asarray(base)!=np.asarray(result)).any(2)
(ROOT/'source/design_record.json').write_text(json.dumps({
 'authority':'User accepted r3 joints and explicitly requested a visible middle aging strength, not the former extreme restraint.',
 'reference_observation':'Chrome Viewer Final Render and Base Color revisited: connected gray clusters anchored to trim/joints, stepped contours, quieter central planes. No exact pixel/UV/shader inference.',
 'adaptation':'Smaller/shallower edge coverage than the outdoor reference, clearer gray values than r3. Dry retention and seal/metal old-contact interpretation; no copied water damage.',
 'authorship':'Project-authored deterministic pixel contours, no random distribution or third-party image inputs.',
 'layers':[name for name,_ in layers],'size':[256,272],
 'upper_profile_depth_px_max':22,'lower_profile_depth_px_max':35,'contour_micro_steps_px':2,'density_trial_texels_m':80,
 'changed_pixels':int(changed.sum()),'changed_fraction':float(changed.mean()),
 'joints_and_diffuser_exact':bool(np.array_equal(np.asarray(base)[protected],np.asarray(result)[protected])),
 'floor_geometry_uv_lighting_camera':'Unchanged from r3.',
 'new_generation_usage':0,
 'baseline_sha256':hashlib.sha256((PROJECT/'assets/art/room1_wall_joints_r3/wall_sample.png').read_bytes()).hexdigest()
},indent=2),encoding='utf-8')
print('Middle-strength connected wall aging saved; approved seams and diffuser preserved.')
