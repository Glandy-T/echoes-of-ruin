"""Project-authored pixel elevations; no third-party images or random noise."""
from pathlib import Path
from PIL import Image, ImageDraw
import json

ROOT=Path(__file__).resolve().parents[1]
for name in ['guides','raw','editable','evidence','survey','source/layers']:
    (ROOT/name).mkdir(parents=True,exist_ok=True)

wall=Image.new('RGB',(256,272),'#D3D6C9')
d=ImageDraw.Draw(wall)
# Broad coating variation stays quieter than the structural trim.
d.polygon([(0,43),(75,43),(75,64),(63,64),(63,95),(37,95),(37,124),(0,124)],fill='#CED2C5')
d.polygon([(256,63),(200,63),(200,104),(188,104),(188,146),(209,146),(209,161),(256,161)],fill='#D9DBCE')
d.polygon([(0,182),(30,182),(30,198),(65,198),(65,216),(93,216),(93,243),(0,243)],fill='#CFD3C6')
d.polygon([(104,45),(171,45),(171,69),(159,69),(159,82),(125,82),(125,71),(104,71)],fill='#D7D9CC')
d.polygon([(111,188),(146,188),(146,179),(173,179),(173,194),(184,194),(184,211),(155,211),(155,220),(111,220)],fill='#D6D9CC')
wall.save(ROOT/'source/layers/wall_coating_guide.png')

structure=Image.new('RGBA',wall.size,(0,0,0,0));s=ImageDraw.Draw(structure)
# Existing 22.5cm diffuser: world height 2.95..3.175m, rows18..35 at80tex/m.
# All lines represent existing returns/edges; no extra panel grid or devices.
for a,b,c in [(0,10,'#BCC4B9'),(11,12,'#D3D7CA'),(13,13,'#E7E7D4'),
               (14,15,'#A6B4B0'),(16,17,'#52666B'),(18,35,'#CCDDE4'),
               (36,37,'#62777B'),(38,39,'#9EAFAC'),(40,41,'#E2E4D1'),
               (42,43,'#C1C8BC'),(249,249,'#B7C0B3'),(250,251,'#485E63'),
               (252,253,'#A5B6AE'),(254,255,'#BBC5B7'),(256,260,'#829591'),
               (261,265,'#778C89'),(266,268,'#687F7D'),(269,269,'#A0ADA3'),
               (270,271,'#344D55')]:
    s.rectangle((0,a,255,b),fill=c)
structure.save(ROOT/'source/layers/wall_structure_guide.png')
# Sparse connected edge wear on the existing metal lip, never floating dirt.
edge=Image.new('RGBA',wall.size,(0,0,0,0));e=ImageDraw.Draw(edge)
e.polygon([(19,249),(19,247),(27,247),(27,246),(39,246),(39,247),(52,247),(52,249)],fill='#BBC3B7')
e.polygon([(176,249),(176,248),(183,248),(183,246),(195,246),(195,247),(217,247),(217,249)],fill='#C1C8BC')
e.rectangle((46,255,65,255),fill='#CCD0C0')
e.rectangle((145,255,177,255),fill='#CBD0BF')
e.polygon([(67,264),(78,264),(78,263),(91,263),(91,265),(83,265),(83,266),(67,266)],fill='#6F8582')
edge.save(ROOT/'source/layers/wall_contact_guide.png')
wall=Image.alpha_composite(wall.convert('RGBA'),structure)
wall=Image.alpha_composite(wall,edge).convert('RGB')
wall.save(ROOT/'guides/wall_original.png')

floor=Image.new('RGB',(256,256),'#5A6C73');f=ImageDraw.Draw(floor)
# Connected, open-ended pigment plateaus. No tile borders or artificial paths.
regions=[('#566970',[(0,0),(111,0),(111,13),(95,13),(95,28),(76,28),(76,44),(48,44),(48,54),(22,54),(22,69),(0,69)]),
('#607279',[(159,0),(256,0),(256,79),(231,79),(231,66),(208,66),(208,48),(182,48),(182,27),(159,27)]),
('#5D7077',[(0,109),(25,109),(25,96),(54,96),(54,108),(73,108),(73,129),(90,129),(90,150),(67,150),(67,171),(36,171),(36,182),(0,182)]),
('#556970',[(256,117),(231,117),(231,130),(206,130),(206,153),(185,153),(185,171),(165,171),(165,190),(176,190),(176,214),(207,214),(207,229),(256,229)]),
('#5F7178',[(0,230),(32,230),(32,219),(56,219),(56,206),(88,206),(88,218),(112,218),(112,237),(99,237),(99,256),(0,256)]),
('#5D6F76',[(104,76),(126,76),(126,66),(143,66),(143,84),(164,84),(164,103),(156,103),(156,117),(135,117),(135,106),(114,106),(114,96),(104,96)])]
for c,p in regions:f.polygon(p,fill=c)
floor.save(ROOT/'guides/floor_original.png')

prompts={
'wall':'''Refine this ORIGINAL project-authored flat wall elevation into a complete carefully painted PIXEL ART ALBEDO texture for an enclosed futuristic cryogenic preservation facility. This is surface art, not a scene. Preserve exact construction and horizontal rows: upper continuous light recess and diffuser rows18-35, return lips rows13-17 and36-43, narrow metal protection band rows250-271. Preserve those positions and thicknesses exactly. No vertical seams, no modular panel pattern. Mineral/ceramic composite face centered #D3D6C9, with warm ivory #E7E7D4 highlights and #C1C8BC shade. Main wall remains intact and quiet. Give EXISTING trim readable painted volume: deliberate narrow bright upper-facing edge, dark inner return, a middle material tone, and selected stepped pixel edge accents. Metal protection face must read differently from matte ceramic through organized short horizontal highlight clusters, not reflective gradients. Native hard pixel clusters at several scales; retain broad quiet space but replace bland cloud blobs with carefully connected restrained material color steps. Time marks only gather along the actual lower ledge and worn old-contact portion of metal. Do not create random dirt islands or drips, rust, cracks, peeling, plaster, moss, scratches, rivets, screws, vents, pipes, labels, buttons, devices, grid, tiling, extra lights or furniture. No new objects. Light face is continuous low-saturation gray-blue-white, no dark gaps. No perspective, cast shadows, bloom, photoreal PBR, smooth gradient shading, noise or anti-aliasing. Crisp authored pixel clusters and material-specific edges, clear at normal image size. Full opaque 256x272 image.''',
'floor':'''Refine this ORIGINAL project-authored guide into a detailed but restrained PIXEL ART ALBEDO texture for one continuous sealed matte blue-gray engineering-composite indoor floor, centered #5A6C73. Same material over the ENTIRE canvas. Broad tonal differences must remain low contrast, with several scales of connected angular pixel clusters and carefully composed broken stepped transitions, quiet negative space, and much finer secondary connected shapes nested into larger pigment regions. The shapes describe mineral/pigment and subtle application variation, not dirt, camouflage, stones, separate paving or damage. Preserve low saturation. Make pixel shape organization legible without high-contrast noisy speckles. Native hard 1-3pixel contour steps and smaller connected 3-12pixel clusters linking broad regions. No outline around patches; no scene, perspective, objects, lighting gradients, cast shadow, border frame, tile grid, floor panels, gaps, bricks, checkerboard, road, route, stripe, arrows, lines, text, numbers, scratches, scuffs, cracks, stains, puddles, rust, moss or photorealistic noise. Evenly presented flat surface art for a quiet formal life-preservation facility. Full opaque 256x256 image.'''
}
for key,value in prompts.items():(ROOT/'source'/f'{key}_prompt.txt').write_text(value,encoding='utf-8')
(ROOT/'source/guide_manifest.json').write_text(json.dumps({
 'authorship':'Project-authored pixel guides and exact existing structure rows; no third-party image inputs, no random placement.',
 'wall_size':[256,272],'floor_size':[256,256],'density_texels_m':80,
 'scope':'One3.2m sample. Density is a candidate, not a project standard.',
 'wall_emitter_world_y':[2.95,3.175],'third_party_reference_uploaded':False
},indent=2),encoding='utf-8')
print('Original structured pixel guides and prompts saved.')
