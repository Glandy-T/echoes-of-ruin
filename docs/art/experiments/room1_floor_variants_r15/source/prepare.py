"""Prepare original guides and PixelLab requests; never paint aging details."""
from pathlib import Path
import shutil,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
OLD=ROOT/'docs/art/experiments/room1_floor_pixellab_r14'
for name in ['raw','editable','evidence']:(HERE.parent/name).mkdir(parents=True,exist_ok=True)
for name in ['pixellab_api.py','pod_footprints.json','canonical_footprint.png']:
    shutil.copyfile(OLD/'source'/name,HERE/name)
for name,old in [('base_00','base3'),('contact_00','contact_a'),('contact_01','contact_c'),('leak_00','leak_a'),('edge_00','edge')]:
    shutil.copyfile(OLD/'raw'/f'{old}.png',HERE.parent/'raw'/f'{name}.png')
shutil.copyfile(OLD/'raw/base3.png',HERE/'accepted_floor_style.png')
palette=json.loads((OLD/'source/request_base3.json').read_text())['target_palette']
common='''Seamless flat top-down albedo pixel texture for continuous worn matte blue-gray mineral composite flooring inside an abandoned advanced cryogenic facility. Match the supplied OWN PROJECT texture's material, native pixel cluster scale, blue-gray palette and moderate contrast, but draw a NEW arrangement of coating wear. The entire square is material, not a room picture. Interlocking cloudy worn coating fields with finer coherent pixel clusters and tiny fragmented edges. One continuous cold blue-gray floor. No tiles, joints, grid, paths, text, objects, long scratches, perspective, shadows, lights, gloss or cartoon outlines. Crisp native pixels, no blur. Seamless continuation on all edges. '''
themes=[
 'New variation: broad diagonal soft-edged coating swaths broken by small darker islands, fine uneven pigment at boundaries. Do not copy the reference silhouette.',
 'New variation: several smaller asymmetrical mineral-coating fields connected in loose irregular chains, with a quiet darker region and intermediate fine clusters.',
 'New variation: elongated gently curved material wear fields, partially fragmented into finer pigment clusters; no long thin line or scratch.',
 'New variation: dispersed overlapping medium-sized irregular cloudy fields with narrow darker gaps and finer mottled pigment. No regular spots.',
 'New variation: broad quiet intermediate blue-gray coating interrupted by a few fragmented worn fields, less evenly distributed, same overall wear strength.',
 'New variation: a broken broad branching swath of lighter old coating surrounded by denser dark mineral pigment; no closed obvious isolated blob.',
 'New variation: several differently sized soft jagged-edged coating regions, restrained larger center field and fine transition clusters near edges.',
 'New variation: irregular broad material scumbling with a darker meandering area and scattered small transitional clusters, same palette and pixel detail.'
]
jobs=[]
for i,theme in enumerate(themes,1):
    n=f'base_{i:02d}'
    prompt=common+theme
    (HERE/f'prompt_{n}.txt').write_text(prompt,encoding='utf-8')
    jobs.append({'name':n,'endpoint':'/generate-image-v2','prompt':f'prompt_{n}.txt','seed':2026103010+i,'style':'accepted_floor_style.png','palette':palette})
contact_prompts=[
 'Make a new fine granular contact-dust variation outside the preserved pod footprint. Slightly denser at the LOWER TWO corners, discontinuous narrow grain clusters along the long sides, lighter dust at the head. Contact halo mostly 3-12 pixels wide. No long scratches, lines or puddles.',
 'Make a new fine granular contact-dust variation outside the preserved pod footprint. Uneven fine buildup at all four corners, some small breaks along the long sides, denser at the UPPER RIGHT. Dust connected closely to base, not a separate rectangle. No scratches or long lines.',
 'Make a new fine granular contact-dust variation outside the preserved pod footprint. Mostly a fine broken left-side contact trace and small corner deposits, right side quieter with isolated attached clusters. No continuous hard border, long scrape, crack or pool.',
 'Make a new fine granular contact-dust variation outside the preserved pod footprint. Asymmetric small material clusters near each foot corner and delicate alternating density along both long sides. 1-3 pixel coherent fragments. No scratches, hatching, extra objects or hard rectangle.'
]
for i,prompt in enumerate(contact_prompts,2):
    n=f'contact_{i:02d}'
    for kind in ['guide','mask']:shutil.copyfile(OLD/'source'/f'{kind}_contact_a.png',HERE/f'{kind}_{n}.png')
    full='Flat top-down pixel-art floor texture edit. Cool blue-gray #5A6C73 floor; dark central polygon is the occupied pod footprint and must be preserved. All new details are on the floor OUTSIDE it. Match fine small native pixel clusters of old mineral dust. No warm colors, yellow, brown, rust, glow, lighting or perspective. '+prompt+' Outer background stays the original flat floor color. Do not add standalone speckles across the full patch.'
    (HERE/f'prompt_{n}.txt').write_text(full,encoding='utf-8')
    jobs.append({'name':n,'endpoint':'/inpaint-v3','prompt':f'prompt_{n}.txt','seed':2026103040+i,'guide':f'guide_{n}.png','mask':f'mask_{n}.png'})
leak_prompts=[
 'A different short broad dried seep spreading beside the LOWER RIGHT corner, connected to the base, fine jagged fragmented residue rather than a rounded pool. 15-30 pixels across. Similar amount and cool desaturated contrast to original, but a different outline.',
 'A different narrow irregular dried seep trailing just beyond the LOWER RIGHT end corner, a few small connected material tongues and finer disintegrating edges. 18-34 pixels across, not a long line or crack.',
 'A different small asymmetric dried coolant residue at the LOWER RIGHT base corner: low flat spreading discoloration, fine fragmented dry tide edge with a few attached pixels. Compact 15-30 pixel extent, no closed black outline or pools.'
]
for i,prompt in enumerate(leak_prompts,1):
    n=f'leak_{i:02d}'
    shutil.copyfile(OLD/'raw/leak_a.png',HERE/f'guide_{n}.png')
    shutil.copyfile(OLD/'source/mask_leak_a.png',HERE/f'mask_{n}.png')
    full='Flat top-down pixel-art albedo material edit. Preserve the existing central dark occupied pod footprint and flat blue-gray floor. Replace the existing small dried coolant mark with a NEW variation in the SAME restrained style and palette. '+prompt+' No yellow, brown, green, glow, highlights, deep hole, long scratches, new equipment or changes to the pod footprint. Only one localized residue; keep all other contact edges quiet.'
    (HERE/f'prompt_{n}.txt').write_text(full,encoding='utf-8')
    jobs.append({'name':n,'endpoint':'/inpaint-v3','prompt':f'prompt_{n}.txt','seed':2026103060+i,'guide':f'guide_{n}.png','mask':f'mask_{n}.png'})
if not (HERE/'requests_initial.json').exists():
    (HERE/'requests_initial.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
# Early style-reference jobs mostly copied the reference pattern. Preserve them
# as evidence and make genuine new compositions using text + the same palette.
for j in jobs:
    if j['name'] in ['base_07','base_08']:j.pop('style',None)
replacements=[]
for i in range(2,7):
    n=f'base_{i:02d}_new'
    old=next(j for j in jobs if j['name']==f'base_{i:02d}')
    prompt=(HERE/old['prompt']).read_text(encoding='utf-8').replace('Match the supplied OWN PROJECT texture\'s material, native pixel cluster scale, blue-gray palette and moderate contrast, but draw a NEW arrangement of coating wear.','Use coherent small pixel clusters, blue-gray mineral coating and restrained contrast, with a new irregular distribution of wear.')
    (HERE/f'prompt_{n}.txt').write_text(prompt,encoding='utf-8')
    replacements.append({'name':n,'endpoint':'/generate-image-v2','prompt':f'prompt_{n}.txt','seed':2026103080+i,'palette':palette})
jobs=jobs[:8]+replacements+jobs[8:]
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
print('Prepared',len(jobs),'persistent requests, including near-copy replacements without style-image composition guidance.')
