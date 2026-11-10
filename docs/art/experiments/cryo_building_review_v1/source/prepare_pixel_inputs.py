"""Original flat guides and protection/age masks. No procedural weathering."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageColor
import json, hashlib, re

S=Path(__file__).resolve().parent; E=S.parent; ROOT=S.parents[4]
J=S/'jobs'; J.mkdir(parents=True,exist_ok=True)
BASE=ROOT/'docs/art/cryo_building_production/PIXELLAB_AND_REVIEW.md'
spec=BASE.read_text(encoding='utf-8')
quotes=re.findall(r'^> (.+)$',spec,re.M)
assert len(quotes)==8,len(quotes)
common,steel,coat,ordinary,joint,runoff,zinc,doors,*_=quotes
wall=ROOT/'assets/art/room1_wall_detail_full_r24/wall_rear.png'
style=Image.open(wall).convert('RGB').crop((172,56,236,248))
jobs=[]
region_colors={0:'#59635c',1:'#41525e',2:'#90776b',3:'#7c8f9e',4:'#8d8070'}

def dump(path, data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def save(id, material, shape, palette, prompt, areas=(), features=(), group='J03', mode='Pixen', source=None):
    p=J/id; p.mkdir(exist_ok=True)
    w,h=shape
    body=Image.new('RGB',shape,palette[0]); d=ImageDraw.Draw(body)
    if source is not None:
        # Same-pixel crops only; no source is ever resampled to inflate native density.
        src=Image.open(source).convert('RGB'); body.paste(src.crop((0,0,w,h)))
    mask=Image.new('L',shape,255); protect=ImageDraw.Draw(mask)
    age=Image.new('RGB',shape,region_colors[0]); ad=ImageDraw.Draw(age)
    for zone, rect in areas: ad.rectangle(rect,fill=region_colors[zone])
    for rect, color in features: d.rectangle(rect,fill=color); protect.rectangle(rect,fill=0)
    body.save(p/'guide.png'); mask.save(p/'edit_mask.png'); age.save(p/'age_region_mask.png'); style.save(p/'style_reference.png')
    # Pixen's browser editor accepts only the image. Put a small, original reference
    # to its right, and exclude it from all exported textures. The Pro input can
    # take a separate reference instead. Restore protected geometry from the guide.
    if mode=='Pixen':
        browser=Image.new('RGB',(w+64,h),palette[0]);browser.paste(body,(0,0)); browser.paste(style.crop((0,0,64,min(h,192))),(w,0));browser.save(p/'web_input.png')
        scope=f'Edit only the left {w} by {h} pixels. Right 64 pixels are protected ORIGINAL style reference, not target. Keep the input canvas size.'
    else:
        body.save(p/'web_input.png')
        scope=f'Keep exact canvas {w} by {h}. Preserve the plate splits and the guides marking fixed gaps. Reference is project-owned, only for pixel scale and coating finish.'
    hints=' Real permitted contact regions, coordinates in the left target: '+('; '.join(f'E{z} x{x0}..{x1}, y{y0}..{y1}' for z,(x0,y0,x1,y1) in areas) or 'E0 only')+'.'
    full=f'[CRYO-{id}] {scope}\n{common}\n{prompt}\n{hints}'
    (p/'prompt.txt').write_text(full,encoding='utf-8')
    job={'name':id,'material':material,'group':group,'mode':mode,'observed_ui_unit_cost':1 if mode=='Pixen' else 10,'native_size':[w,h],'input_size':[w+64 if mode=='Pixen' else w,h],'export_crop':[0,0,w,h],'regions':[{ 'id':f'E{z}','bounds':r} for z,r in areas],'region_key':{f'E{z}':c for z,c in region_colors.items()},'style_source':wall.relative_to(ROOT).as_posix(),'style_sha256':hashlib.sha256(wall.read_bytes()).hexdigest(),'style_crop':[172,56,236,248],'workflow':'Official PixelLab Creator; visual guide submitted, mask used at export; editor does not receive a native mask.'}
    dump(p/'request.json',job);jobs.append(job)

if __name__=='__main__':
    save('M04','M04',(256,64),('#737F81',),steel,[(2,(2,19,253,41)),(1,(0,44,24,63)),(1,(230,44,255,63))],group='J01')
    save('M05-L','M05-L',(256,256),('#A7B0AA',),coat.replace('{LIGHT: base #A7B0AA, shadow #858F8A, light #C1C6BD / DARK: base #4D6065, shadow #36494E, light #718185}','LIGHT: base #A7B0AA, shadow #858F8A, light #C1C6BD'),[(2,(8,228,245,253))],group='J02')
    save('M05-D','M05-D',(256,256),('#4D6065',),coat.replace('{LIGHT: base #A7B0AA, shadow #858F8A, light #C1C6BD / DARK: base #4D6065, shadow #36494E, light #718185}','DARK: base #4D6065, shadow #36494E, light #718185'),[(2,(8,228,245,253))],group='J02')
    save('M07','M07',(256,256),('#71858A',),zinc,[(1,(1,1,15,254)),(2,(240,0,255,255))],group='J04')
    for i in range(1,4): save(f'M06-0{i}',f'M06-0{i}',(256,256),('#B9BDB2',),ordinary.replace('{01/02/03}',f'{i:02d}')+' Make this a continuous field with NO seam, border or picture composition.',group='J03')
    save('M06-J','M06-J',(256,256),('#B9BDB2',),joint,[(1,(1,3,30,253)),(4,(0,224,255,255))],[((0,0,0,255),'#687771')],group='J03',mode='Pro')
    save('M06-R','M06-R',(256,256),('#B9BDB2',),runoff,[(3,(110,1,160,137))],[((118,0,150,0),'#687771')],group='J03',mode='Pro')
    manifest=E/'model/interior_manifest.json'
    if manifest.exists():
        for row in json.loads(manifest.read_text(encoding='utf-8'))['doors']:
            id=row['id']; w=round(row['W_m']*80);h=round(row['H_m']*80);p=J/id
            dark=id.startswith('EL') or id=='EN-B';base='#4D6065' if dark else '#A7B0AA';ms='M05-D' if dark else 'M05-L'
            n=0; features=[]
            for span in row['panel_widths_m'][:-1]:
                n+=span;col=round(n*80);features.append(((col,0,col,h-1),'#263B3E'))
            add=' Inactive fixed screen and frame are separate geometry; no marks or glow.' if id.startswith('EL') else ' Release hardware is separate, keep the intact door faces.'
            extra=[(2,(5,h-18,w-6,h-2)),(1,(0,0,5,h-1)),(1,(w-6,0,w-1,h-1))]
            if id.startswith('EN'): add+=' OUTSIDE only: allow restrained rain at real lower seal and top return; no invented streak sources.';extra.append((3,(0,0,12,45)))
            src=ROOT/'assets/art/cryo_building_review_v1/textures'/f'{ms}.png'
            save(id,'FACE_'+id.replace('-','_'),(w,h),(base,),doors.replace('{FD-A/FD-B/EL-A/EL-B/EN-A/EN-B}',id).replace('the supplied approved coating sample',f'the provided {ms} underpainting')+add+f' Keep base {base} and low contrast.',extra,features,group='J05',mode='Pro',source=src if src.exists() else None)
    dump(S/'requests.json',jobs)
    dump(E/'generation_plan.json',{'source':'f7fa9e8342f77106daad9b9199f34333fca53c89','remaining_monthly_units_observed':101,'paid_credit_balance_usd':0,'model_costs':'Creator displayed Pixen edit 1; Pro edit 10 at <=256²; recheck button on every submit','planned_requests':len(jobs),'expected_subscription_units':sum(x['observed_ui_unit_cost'] for x in jobs),'budget_policy':'No purchase or upgrade. One initial result and at most one evidence-based targeted correction within existing balance.','task_order':[x['name'] for x in jobs]})
    print('Prepared',len(jobs),'native artwork guides')
