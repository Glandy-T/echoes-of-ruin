"""Position-led material finish; no random generator, route masks or AI age patches.

Retains the existing PixelLab material's faint microtone and the authored wall
trim/diffuser. Broad tonal fields are authored here, not new AI outputs.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OLD_WALL = ROOT.parent / 'room1_wall_pixel_v2'
OLD_FLOOR = ROOT.parent / 'room1_floor_pixel_compare_v1'
LAY = ROOT / 'source/layers'
TEX = ROOT / 'textures'
LAY.mkdir(exist_ok=True)
TEX.mkdir(exist_ok=True)


def rgb(array):
    return Image.fromarray(np.clip(np.rint(array), 0, 255).astype('uint8'))


def overlay(mask, color, strength):
    # Quantized opacity retains restrained pixel steps, no noise/speckle.
    alpha = np.round(np.clip(mask, 0, 1) * strength / 3) * 3
    result = np.empty((*mask.shape, 4), dtype='uint8')
    result[:, :, :3] = color
    result[:, :, 3] = np.clip(alpha, 0, 255).astype('uint8')
    return Image.fromarray(result)


def finish(key, layers):
    result = layers[0][1].convert('RGBA')
    layers[0][1].save(LAY / (key + '_' + layers[0][0] + '.png'))
    for name, layer in layers[1:]:
        layer.save(LAY / (key + '_' + name + '.png'))
        result = Image.alpha_composite(result, layer.convert('RGBA'))
    result.convert('RGB').save(TEX / (key + '_albedo.png'))


# Floor: a continuous coating field, not a layout/color zoning mask.
W, H, D = 1680, 760, 80
base = np.array([90., 108., 115.])
old_micro = np.asarray(Image.open(OLD_FLOOR / 'source/layers/common_material.png').convert('RGB'), dtype=float)
micro = np.clip(old_micro - base, -1, 1)
X, Y = np.meshgrid((np.arange(W) + .5) / D, (H - np.arange(H) - .5) / D)
large = (4.6 * np.cos((X / 21 * 1.18 + Y / 9.5 * .48) * np.pi + .65)
         + 2.8 * np.sin((X / 21 * .6 - Y / 9.5 * .92) * np.pi - .25))
large = np.round(large / 1.5) * 1.5
floor_base = rgb(np.broadcast_to(base, (H, W, 3)))
floor_field = rgb(base + large[:, :, None] + micro)

# Edge distance follows actual interior wall feet; rear doorway stays open.
rear_distance = 9.3 - Y
rear_distance = np.where((X >= 9.8) & (X <= 11.2), 50, rear_distance)
distance = np.maximum(np.minimum.reduce([X - .2, 20.8 - X, Y - .2, rear_distance]), 0)
floor_edge = overlay(np.exp(-(distance / .30) ** 2), [61, 82, 92], 42)
e = ImageDraw.Draw(floor_edge)
def fp(x, y): return (round(x * D), round(H - y * D))
# Thin actual wall-foot join; restrained, not a decorative frame/grid.
for segment in [(.2,.2,20.8,.2),(.2,.2,.2,9.3),(20.8,.2,20.8,9.3),
                (.2,9.3,9.8,9.3),(11.2,9.3,20.8,9.3)]:
    e.line((*fp(*segment[:2]), *fp(*segment[2:])), fill=(65,87,99,65), width=1)

# Two faint installation/contact illustrations adjacent to existing pod envelopes.
contact = np.zeros((H,W))
for px, py in [(5.82,1.35),(6.46,7.45)]:
    contact = np.maximum(contact, np.exp(-((X-px)/.045)**2 - ((Y-py)/.32)**4))
floor_contact = overlay(contact, [65,87,99], 24)
finish('floor', [('base',floor_base),('broad_material',floor_field),
                 ('edge_finish',floor_edge),('contact_finish',floor_contact)])
rgb(np.asarray(Image.open(TEX/'floor_albedo.png'))).resize((840,380),Image.Resampling.NEAREST).save(ROOT/'evidence/floor_flat.png')

# Wall coordinates match existing planar UVs. The rejected patch layer is never
# loaded, composited, or copied. Only authored trims/diffuser and weak native field.
wall_base = np.array([211.,214.,201.])
maps = {
    'rear': {'width':1680,'length':21.,'corners':[16,1663],'phase':.25,'contacts':[142,1162],'door':[784,896]},
    'front': {'width':1680,'length':21.,'corners':[16,1663],'phase':1.15,'contacts':[282,1402],'door':[]},
    'left': {'width':728,'length':9.1,'corners':[0,727],'phase':.7,'contacts':[190],'door':[]},
    'right': {'width':728,'length':9.1,'corners':[0,727],'phase':1.65,'contacts':[600],'door':[]},
}
records = {}
for key, spec in maps.items():
    width = spec['width']
    xx, yy = np.meshgrid(np.arange(width,dtype=float), np.arange(272,dtype=float))
    original = np.asarray(Image.open(OLD_WALL/'source/layers'/f'{key}_body.png').convert('RGB'),dtype=float)
    native = np.clip(original-wall_base,-1,1)
    broad = (3.5*np.cos((xx/width*1.28 + yy/272*.25)*np.pi+spec['phase'])
             + 1.7*np.sin(yy/272*np.pi*.8+spec['phase']))
    broad = np.round(broad/1.5)*1.5
    body = rgb(np.broadcast_to(wall_base,(272,width,3)))
    coating = rgb(wall_base + broad[:,:,None] + native)
    trim = Image.open(OLD_WALL/'source/layers'/f'{key}_trims.png').convert('RGBA')
    diffuser = Image.open(OLD_WALL/'source/layers'/f'{key}_diffuser.png').convert('RGBA')

    # Low-intensity deposits confined to protected lower edges and corners.
    mask = .58*np.exp(-((yy-247)/8)**2)
    body_region = (yy>=45)&(yy<249)
    corner = np.zeros((272,width))
    for cx in spec['corners']:
        corner = np.maximum(corner, np.exp(-((xx-cx)/9)**2) * (.28+.40*(yy/272)**2))
    mask = np.maximum(mask, corner)*body_region
    for dx in spec['door']:
        door = .45*np.exp(-((xx-dx)/5)**2)*(yy>=80)*(yy<249)
        mask = np.maximum(mask,door)
    if key=='rear':
        mask = np.maximum(mask,.30*np.exp(-((yy-79)/3)**2)*(xx>=784)*(xx<=896))
    deposit = overlay(mask, [178,186,170], 62)

    # Old touches remain on the metal protection face only; no floating wall marks.
    touch = np.zeros((272,width))
    for cx in spec['contacts']:
        touch = np.maximum(touch,np.exp(-((xx-cx)/39)**4-((yy-259)/3.8)**2))
    touch *= (yy>=253)&(yy<=266)
    band_contact = overlay(touch,[128,148,139],50)

    # Door return and lower lip offer one-pixel material structure, not broad seams.
    structure = Image.new('RGBA',(width,272),(0,0,0,0));s=ImageDraw.Draw(structure)
    for dx in spec['door']:
        outside = -1 if dx < width/2 else 1
        s.line((dx+outside,80,dx+outside,248),fill=(158,172,157,100))
        s.line((dx+outside*2,80,dx+outside*2,247),fill=(231,231,212,100))
    if key=='rear':
        s.line((784,79,896,79),fill=(158,172,157,100))
        s.line((784,78,896,78),fill=(231,231,212,100))
    # Keep the approved-width light assembly identical; no altered light masks.
    mask_image=Image.open(OLD_WALL/'textures'/f'{key}_emission.png').convert('L')
    mask_image.save(TEX/f'{key}_emission.png')
    rgb(np.asarray(mask_image,dtype=float)[:,:,None]/255*np.array([204,221,228])).save(TEX/f'{key}_emissive_color.png')
    finish(key,[('base',body),('broad_material',coating),('trims',trim),
                ('edge_deposit',deposit),('band_contact',band_contact),
                ('structure',structure),('diffuser',diffuser)])
    records[key] = {k:v for k,v in spec.items() if k!='phase'}
Image.open(TEX/'rear_albedo.png').save(ROOT/'evidence/wall_flat.png')
Image.open(TEX/'right_albedo.png').crop((20,0,420,272)).resize((1200,816),Image.Resampling.NEAREST).save(ROOT/'evidence/wall_detail_pixels.png')
(TEX/'manifest.json').write_text(json.dumps({
    'status':'user selected uniform A direction; new finish awaiting review',
    'floor_dimensions':[W,H],'wall_maps':records,
    'density_texels_m':D,'density_status':'inherited trial only',
    'floor_uniform':True,'route_zoning':False,'random_dirt':False,'visible_scratches':False,
    'wall_rejected_ai_age_patch_layer_used':False,
    'new_paid_generation_requests':0,
    'authorship':'existing PixelLab faint native material; manually authored deterministic tonal/edge layers',
    'floor_broad_tone_nominal_channel_delta':[-7.5,7.5],
    'wall_broad_tone_nominal_channel_delta':[-6,6],
    'contact_history':'illustrative placement, not confirmed historical events',
    'light_diffuser_width_m':.225,'light_tint':'#CCDDE4','light_mask_unchanged':True,
},indent=2),encoding='utf-8')
print('Unified floor and wall material-time layers ready; rejected patches not used.')
