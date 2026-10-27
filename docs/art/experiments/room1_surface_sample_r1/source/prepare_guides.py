"""Original painted pixel guides. No reference screenshots or random noise."""
from pathlib import Path
from PIL import Image, ImageDraw
import json

ROOT=Path(__file__).resolve().parents[1]
GUIDES=ROOT/'guides'
GUIDES.mkdir(exist_ok=True)

floor=Image.new('RGB',(128,128),'#5a6c73');d=ImageDraw.Draw(floor)
# Hand-authored interlocking coating plateaus, not independent dirt spots.
regions=[
('#566870',[(0,0),(74,0),(74,8),(62,8),(62,13),(55,13),(55,19),(39,19),(39,25),(24,25),(24,22),(12,22),(12,29),(0,29)]),
('#5e7077',[(74,0),(128,0),(128,31),(114,31),(114,38),(103,38),(103,32),(91,32),(91,22),(84,22),(84,11),(74,11)]),
('#607279',[(0,37),(13,37),(13,31),(31,31),(31,35),(42,35),(42,43),(51,43),(51,54),(46,54),(46,61),(32,61),(32,67),(22,67),(22,73),(0,73)]),
('#53666e',[(128,43),(115,43),(115,48),(108,48),(108,55),(91,55),(91,63),(84,63),(84,71),(77,71),(77,79),(81,79),(81,93),(95,93),(95,100),(108,100),(108,105),(128,105)]),
('#5e7077',[(0,91),(11,91),(11,85),(25,85),(25,79),(37,79),(37,84),(48,84),(48,92),(59,92),(59,104),(53,104),(53,116),(40,116),(40,128),(0,128)]),
('#61737a',[(59,128),(59,118),(68,118),(68,109),(79,109),(79,112),(91,112),(91,119),(101,119),(101,128)]),
('#586a72',[(49,19),(57,19),(57,26),(69,26),(69,34),(76,34),(76,42),(70,42),(70,49),(61,49),(61,44),(56,44),(56,35),(47,35),(47,28)]),
('#5e7077',[(50,58),(60,58),(60,55),(68,55),(68,61),(75,61),(75,67),(69,67),(69,74),(57,74),(57,70),(50,70)]),
]
for c,p in regions:d.polygon(p,fill=c)
floor.save(GUIDES/'floor_original.png')

wall=Image.new('RGB',(128,136),'#d3d6c9');w=ImageDraw.Draw(wall)
wall_regions=[
('#cdd1c4',[(0,23),(35,23),(35,27),(44,27),(44,33),(55,33),(55,39),(62,39),(62,47),(56,47),(56,53),(42,53),(42,48),(28,48),(28,54),(0,54)]),
('#d9dbcf',[(128,23),(91,23),(91,29),(80,29),(80,34),(76,34),(76,45),(83,45),(83,51),(94,51),(94,56),(108,56),(108,52),(128,52)]),
('#d7d9cc',[(0,70),(12,70),(12,64),(30,64),(30,69),(39,69),(39,78),(46,78),(46,86),(35,86),(35,94),(20,94),(20,100),(0,100)]),
('#cfd3c5',[(128,78),(113,78),(113,73),(104,73),(104,67),(94,67),(94,73),(85,73),(85,83),(78,83),(78,92),(86,92),(86,99),(95,99),(95,109),(112,109),(112,114),(128,114)]),
('#d6d9cc',[(38,124),(38,113),(45,113),(45,106),(59,106),(59,99),(66,99),(66,106),(74,106),(74,116),(82,116),(82,124)]),
]
for c,p in wall_regions:w.polygon(p,fill=c)
# Position-defined lower-edge retention, within the coating's actual foot.
w.polygon([(0,121),(12,121),(12,119),(20,119),(20,122),(36,122),(36,124),(0,124)],fill='#c1c8bc')
w.polygon([(128,122),(112,122),(112,120),(103,120),(103,123),(86,123),(86,124),(128,124)],fill='#c5ccbe')
# Integrated structures preserve inherited height/width. No added seams/devices.
old=ROOT.parent/'room1_material_revision_v1/source/layers'
trim=Image.open(old/'left_trims.png').crop((256,0,512,272)).resize((128,136),Image.Resampling.NEAREST)
diffuser=Image.open(old/'left_diffuser.png').crop((256,0,512,272)).resize((128,136),Image.Resampling.NEAREST)
wall=Image.alpha_composite(wall.convert('RGBA'),trim)
wall=Image.alpha_composite(wall,diffuser).convert('RGB')
wall.save(GUIDES/'wall_original.png')

prompts={
'floor':'''Refine the supplied original flat pixel guide into a production albedo texture for a continuous sealed matte engineering-composite indoor floor. Keep the cool desaturated blue-gray hue centered on #5A6C73. Use coherent connected irregular pixel clusters and interlocking tonal plateaus, with deliberate rhythm at several sizes (roughly 3-16 pixels), stepped 1-2 pixel edges and quiet negative space. Color changes describe coating pigment/application and matte surface variation, NOT dirt or damage. Keep low contrast but make individual connected pixel shapes legible: deepest body tone around #52656D and lightest around #657981. No soft gradient-only field, no isolated speckles or random dots. A closed high-tech preservation facility maintained for long service, still structurally intact. Entire canvas is the same continuous floor, evenly lit top-down orthographic albedo; no baked shadows or perspective. Do not draw roads, stripes, arrows, traffic zones, tiles, grid, panel seams, pavement, asphalt, stones, concrete cracks, scratches, rust, puddles, stains, border frame, text, furniture or objects. Do not change the composition into a scene. Refine pixel shape design, not just sprinkle detail. Flat solid opaque full image, hard native pixel edges, limited harmonious palette.''',
'wall':'''Refine the supplied original flat elevation pixel guide into an albedo texture for a sealed high-tech cryogenic facility wall. Fine matte mineral/engineering-composite face, warm gray ivory centered on #D3D6C9, highlights near #E7E7D4, shade near #C1C8BC. Main wall face has quiet connected irregular pixel clusters of subtle coating color, different cluster sizes around 4-20 pixels, stepped crisp pixel boundaries, plenty of restful space; not smooth gradient-only. Main face intact, no floating dirt islands. Greater but restrained pixel information density ONLY at the true top light recess, actual foot of coating and lower narrow metal protection band. Deposits can gather along the lower ledge; very faint old contact finish belongs on the protection band only. Preserve guide construction: continuous pale gray-blue diffuser in upper rows9-17, integrated dark narrow returns, metal protection only in bottom rows125-135. No extra panels, tiled grids, decorative seams, devices, vents, pipes, text or numbers. No streaky water stains, random dark aging patches, peeling plaster, cracks, rust, moss, obvious scratches or outdoor wall damage. This is a flat front-facing evenly lit albedo elevation, no perspective, objects, cast shadows, photorealistic lighting, blur, anti-aliasing or texture noise. Keep all original structural locations and width. Refine coherent pixel shapes while preserving restrained material identity.'''
}
for key,prompt in prompts.items():(ROOT/'source'/f'{key}_prompt.txt').write_text(prompt,encoding='utf-8')
(ROOT/'source/guide_manifest.json').write_text(json.dumps({
 'authorship':'original manually specified pixel polygons; no random generator and no third-party image input',
 'floor_size':[128,128],'wall_size':[128,136],
 'physical_sample_m':{'wall':[3.2,3.4],'floor':[3.2,3.2]},
 'native_density_texels_m':40,'status':'local trial only; not project standard',
 'wall_structure':'crop of existing project-authored trim/diffuser at inherited positions',
 'source_reference_images_submitted':False
},indent=2),encoding='utf-8')
print('Original floor/wall guides and prompts saved.')
