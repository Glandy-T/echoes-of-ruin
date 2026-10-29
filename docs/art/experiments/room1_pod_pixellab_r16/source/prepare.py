"""Clean structural inputs + geometric/functional protection masks, no aging paint."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,shutil,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
OLD=ROOT/'docs/art/experiments/room1_pod_volume_v4'
for name in ['raw','editable','evidence','source/layers']:(EXP/name).mkdir(parents=True,exist_ok=True)
for name in ['pixellab_api.py','jobs.py']:
    shutil.copyfile(ROOT/'docs/art/experiments/room1_floor_variants_r15/source'/name,HERE/name)
keys=['lid','shell_side','shell_end','interior','mattress','section'];records=[]
for key in keys:
    layer='section_material_planes' if key=='section' else 'v3_design_pixel_planes'
    path=OLD/'source/texture_layers'/f'{key}__{layer}.png'
    clean=Image.open(path).convert('RGBA')
    if key in ['lid','shell_end']:
        identity=Image.open(OLD/'source/texture_layers'/f'{key}__sample_id_12_or_placeholder_UI.png').convert('RGBA')
        clean=Image.alpha_composite(clean,identity)
        identity.save(HERE/f'identity_{key}.png')
    else:identity=Image.new('RGBA',clean.size)
    clean.save(HERE/f'clean_{key}.png')
    a=np.asarray(clean);dark=np.max(a[:,:,:3],axis=2)<84
    accent=((a[:,:,1].astype(int)-a[:,:,0])>35)&((a[:,:,2].astype(int)-a[:,:,0])>25)
    protected=dark|accent|(np.asarray(identity)[:,:,3]>0)
    protected[:2]=True;protected[-2:]=True;protected[:,:2]=True;protected[:,-2:]=True
    mask=Image.fromarray((~protected).astype('uint8')*255)
    mask.save(HERE/f'mask_{key}.png')
    if key=='shell_side':
        locked=mask.copy();ImageDraw.Draw(locked).rectangle((0,0,255,25),fill=0)
        locked.save(HERE/'final_mask_shell_side.png')
    shutil.copyfile(OLD/'textures'/f'{key}.png',HERE/f'baseline_{key}.png')
    records.append({'key':key,'size':list(clean.size),'clean_source_layer':str(path.relative_to(ROOT)).replace('\\','/'),'clean_source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'removed_layers':['seam_and_recess_aging','coating_contact_chips'] if key!='section' else ['edge_retained_film'],'editable_pixels':int((~protected).sum()),'functional_ID_retained':key in ['lid','shell_end']})
for key in ['glass','display']:
    shutil.copyfile(OLD/'textures'/f'{key}.png',HERE/f'unchanged_{key}.png')
common='''Pixel-art ALBEDO texture edit of an existing low-poly cryogenic pod. Preserve this exact original panel design, proportions, seals, seams, color zones, tiny vents and existing ID. Keep warm gray-white ceramic composite exterior and cool slate-gray structural parts. Add readable medium-strength age from decades in a SEALED indoor facility: coherent small native pixel clusters with fine broken edges, attached residue in recesses, old seal contact film, tiny local coating wear at real edges and corners. Clear material layering, not isolated random spots or smooth shading. No rust orange, yellow stains, moss, blood, horror damage, holes, new parts, extra panels, new vents, new text, glossy reflections, lighting or perspective. Do not redraw structure. '''
surface={
'lid':'''Top cover texture. Preserve the flat broad main panels and existing number. Age sits at panel recess boundaries, corners, close to the gasket and lower cover edge. Use connected 3-10 pixel worn areas with finer 1-3 pixel fragments and sparse shallow variation; main face remains intact. Do not turn the top into a peeling wall.''',
'shell_side':'''Long side casing. Keep the upper inset ledge, narrow service recess and base band exactly. Accumulation belongs at lower undercuts, end corners and existing recessed strip. Moderate layered cool-gray deposits and tiny edge coating loss; broad side panels remain intact. No new lettering or repeated labels.''',
'shell_end':'''Short end casing. Keep exact panel border and ID plate. Small coherent cool-gray contact buildup under the existing rim and near lower foot corners, some finer material variation at upper corner joints. Do not make a thick black border or add a screen.''',
'interior':'''Protected inside liner, cleaner than exterior. Keep current planar gray liner and frame exactly. Fine shallow mineral material variation and restrained contact residue attached to the inner rim and lower recess corners. No random dirty center, big stains, body impressions, fluids or new seams.''',
'mattress':'''Intact sealed gray padded mattress. Preserve existing mattress silhouette and every horizontal cushion channel. Add subtle pixel material grain and shallow uneven compressed coating tone, with fine cool-gray contact aging very close to the outer edge and channel corners. No torn fabric, holes, strong dirt patches, invented buttons or new grooves.''',
'section':'''Structural cut-edge/inner shoulder material strip. Keep the current horizontal bands in exactly their original rows; especially rows 33-42 must stay in place. Fine small cool-gray gasket contact deposits and tiny chips along EXISTING band transitions. Sparse but clearly readable at native pixels. Do not invent vertical stripes, extra layers or large dark blocks.'''
}
variations={'a':'Balanced medium age, uneven small recess deposits and several natural corner clusters.','b':'Different wear distribution: relatively quiet center, denser fine deposits near left ends and lower ledges, broken irregular connected material clusters.','c':'Different wear distribution: finer fragmented accumulation near upper-right joints and lower end corners, some small old contact rubs, no new scratch lines.','d':'Different wear distribution: slightly more visible lower rim contact film and small uneven corner coating wear, same overall material and contrast as variant A.'}
jobs=[]
for variant in ['a','b','c','d']:
    for key in ['lid','shell_side','shell_end']:
        name=f'{variant}_{key}'
        prompt=common+surface[key]+' '+variations[variant]
        (HERE/f'prompt_{name}.txt').write_text(prompt,encoding='utf-8')
        edit_mask='final_mask_shell_side.png' if variant!='a' and key=='shell_side' else f'mask_{key}.png'
        jobs.append({'name':name,'endpoint':'/inpaint-v3','prompt':f'prompt_{name}.txt','seed':2026103100+len(jobs),'guide':f'clean_{key}.png','mask':edit_mask})
for key in ['interior','mattress','section']:
    name='shared_'+key
    (HERE/f'prompt_{name}.txt').write_text(common+surface[key],encoding='utf-8')
    jobs.append({'name':name,'endpoint':'/inpaint-v3','prompt':f'prompt_{name}.txt','seed':2026103100+len(jobs),'guide':f'clean_{key}.png','mask':f'mask_{key}.png'})
(HERE/'requests_all.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
if not (HERE/'requests.json').exists():
    first=[j for j in jobs if j['name'].startswith('a_') or j['name'].startswith('shared_')]
    (HERE/'requests.json').write_text(json.dumps(first,indent=2),encoding='utf-8')
(HERE/'input_provenance.json').write_text(json.dumps({'structural_inputs':records,'legacy_aging_layers_loaded':[],'unchanged':['glass','display','tube geometry and parameters','model/UV/animation/collision'],'final_extra_structural_locks':{'shell_side':'rows 0-25 preserve accepted blue-gray top inset; A raw had white recoloring','shell_end':'rows 55-79 preserve accepted blue-gray support band; B raw had pale invented patch'}},indent=2),encoding='utf-8')
print('Prepared 15 requests; active persistent queue:',len(json.loads((HERE/'requests.json').read_text())),'jobs.')
