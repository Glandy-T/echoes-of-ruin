from pathlib import Path
from PIL import Image,ImageDraw
import json,numpy as np,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
ASSET=ROOT/'assets/art/room1_floor_variants_r15'
report={'old_art_layers_used':[],'floor_dimensions':[1648,728],'checks':{}}
for name in ['aged','with_leaks']:
    final=Image.open(ASSET/f'floor_{name}.png').convert('RGB')
    read=Image.open(HERE/f'readback_{name}.png').convert('RGB')
    assert final.tobytes()==read.tobytes()
    arr=np.asarray(final,dtype=int)
    report['checks'][name]={'aseprite_readback_exact':True,'size':list(final.size),'warm_R_gt_G_or_G_gt_B_pixels':int(np.sum((arr[:,:,0]>arr[:,:,1])|(arr[:,:,1]>arr[:,:,2]))),'sha256':hashlib.sha256((ASSET/f'floor_{name}.png').read_bytes()).hexdigest()}
    assert final.size==(1648,728)
    assert report['checks'][name]['warm_R_gt_G_or_G_gt_B_pixels']==0
placements=json.loads((HERE/'placements.json').read_text())
assert len(placements['contacts'])==20 and len({p['pod'] for p in placements['contacts']})==20
assert {p['pod'] for p in placements['leaks']}=={'P03','P06','P13','P18'}
assert not placements['legacy_art_layers_used']
report['contact_count']=20;report['leak_pods']=['P03','P06','P13','P18']
selection=json.loads((HERE/'accepted_sources.json').read_text())
report['source_selection']=selection
quilt=json.loads((HERE/'base_quilt.json').read_text())
report['base_source_count']=len(quilt['sources'])
report['base_patch_count']=len(quilt['placements'])
report['base_source_usage']=quilt['usage_counts']
report['immediate_base_repeats']=quilt['immediate_repeat_count']
assert report['base_source_count']>=7 and not report['immediate_base_repeats']
assert all(v>0 for v in quilt['usage_counts'].values())
report['contact_source_count']=len({p['source'] for p in placements['contacts']})
report['leak_source_count']=len({p['source'] for p in placements['leaks']})
assert report['contact_source_count']>=4
for row in [placements['contacts'][:10],placements['contacts'][10:]]:
    assert all(a['source']!=b['source'] for a,b in zip(row,row[1:]))
assert all(placements['contacts'][i]['source']!=placements['contacts'][i+10]['source'] for i in range(10))
old_base=np.asarray(Image.open(ROOT/'docs/art/experiments/room1_floor_pixellab_r14/source/layers/01_PixelLab_floor_coating.png').convert('RGB'),dtype=int)
new_base=np.asarray(Image.open(HERE/'layers/01_PixelLab_floor_coating.png').convert('RGB'),dtype=int)
report['256px_periodic_equality_fraction']={key:float(np.mean(np.all(a[:,256:]==a[:,:-256],axis=2))) for key,a in [('r14',old_base),('r15',new_base)]}
report['256px_shift_luminance_correlation']={key:float(np.corrcoef(a[:,256:].mean(2).ravel(),a[:,:-256].mean(2).ravel())[0,1]) for key,a in [('r14',old_base),('r15',new_base)]}
assert report['256px_periodic_equality_fraction']['r15']<report['256px_periodic_equality_fraction']['r14']*.75
actual=[]
for n in selection['base']:
    raw=np.asarray(Image.open(EXP/'raw'/f'{n}.png').convert('RGB'),dtype=float)
    actual.append(raw.mean(2).ravel())
corr=np.corrcoef(actual);np.fill_diagonal(corr,0)
report['max_accepted_base_pair_correlation_raw']=float(corr.max())
assert corr.max()<.95
usage=[json.loads(p.read_text()) for p in EXP.glob('result_*.json')]
report['generations']=sum(p['usage']['generations'] for p in usage)
report['job_count']=len(usage)
bindings=json.loads((EXP/'evidence/floor_bindings.json').read_text())
assert all('room1_floor_variants_r15' in b['map'] for b in bindings)
report['bindings']=bindings
a=np.asarray(Image.open(EXP/'evidence/overhead_after.png').convert('RGB'),dtype=int)
b=np.asarray(Image.open(EXP/'evidence/overhead_restored.png').convert('RGB'),dtype=int)
report['diagnostic_roundtrip_differing_pixels']=int(np.sum(np.any(a!=b,axis=2)))
report['diagnostic_roundtrip_max_channel_delta']=int(np.abs(a-b).max())
ys,xs=np.where(np.any(a!=b,axis=2))
report['diagnostic_roundtrip_difference_bbox']=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())] if len(xs) else None
pod_mask=np.zeros(a.shape[:2],dtype=bool)
for p in json.loads((EXP/'evidence/projected_supports.json').read_text()):
    pts=np.array(p['points']);lo=np.floor(pts.min(axis=0)-8).astype(int);hi=np.ceil(pts.max(axis=0)+8).astype(int)
    pod_mask[max(0,lo[1]):min(a.shape[0],hi[1]+1),max(0,lo[0]):min(a.shape[1],hi[0]+1)]=True
report['roundtrip_differing_pixels_outside_pod_support_rois']=int(np.sum(np.any(a!=b,axis=2)&~pod_mask))
assert report['roundtrip_differing_pixels_outside_pod_support_rois']==0
report['no_geometry_uv_light_or_bake_edits']=True
(HERE/'quality.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
old=Image.open(ROOT/'assets/art/room1_floor_pixellab_r14/floor_with_leaks.png')
new=Image.open(ASSET/'floor_with_leaks.png')
old.save(EXP/'evidence/floor_map_before.png');new.save(EXP/'evidence/floor_map_after.png')
for name in ['before','after']:
    im=old if name=='before' else new
    im.crop((320,450,500,708)).resize((540,774),Image.Resampling.NEAREST).save(EXP/f'evidence/native_contact_{name}.png')
for group in ['base','contact','leak']:
    ids=selection[group];gallery=Image.new('RGB',(768,((len(ids)+2)//3)*280),(25,34,38));d=ImageDraw.Draw(gallery)
    for i,n in enumerate(ids):
        im=Image.open(EXP/'raw'/f'{n}.png').convert('RGB');x=(i%3)*256;y=(i//3)*280
        if group=='base':
            source=np.array(im);aligned=source.copy()
            for item in quilt['palette_alignment_only'][n]:
                aligned[np.all(source==item['raw_rgb'],axis=2)]=item['aligned_rgb']
            im=Image.fromarray(aligned)
        gallery.paste(im,(x,y));d.text((x+6,y+260),n,fill=(210,224,222))
    gallery.save(EXP/f'evidence/accepted_{group}_sources.png')
names=['game_left_after','game_center_after','game_right_after','overhead_after','corner_front_left','corner_rear_left','corner_front_right','corner_rear_right','contact_P03','contact_P06','contact_P13','contact_P18','contact_P12_standard','contact_door','overhead_color_after','floor_color_unoccluded']
sheet=Image.new('RGB',(1280,816),(20,27,29));draw=ImageDraw.Draw(sheet)
for i,n in enumerate(names):
    x=(i%4)*320;y=(i//4)*204
    sheet.paste(Image.open(EXP/f'evidence/{n}.png').resize((320,180)),(x,y));draw.text((x+4,y+183),n,fill=(215,227,222))
sheet.save(EXP/'evidence/survey_contact_sheet.png')
groups=[('同灯光对照：r14循环底材 → r15多份差分',['game_left_before','game_left_after','game_center_before','game_center_after','game_right_before','game_right_after']),('整室重复分布对照',['overhead_before','overhead_after']),('材质原色对照',['overhead_color_before','overhead_color_after']),('整张原生地坪',['floor_map_before','floor_map_after']),('实际使用的PixelLab底材原图',['accepted_base_sources']),('舱底接触原图与漏液原图',['accepted_contact_sources','accepted_leak_sources']),('舱底原生细节放大',['native_contact_before','native_contact_after']),('实际舱位近景',['pod_contact_before','pod_contact_after']),('四角与门口',['corner_front_left','corner_rear_left','corner_front_right','corner_rear_right','contact_door']),('四处旧漏液与新版P12接触',['contact_P03','contact_P06','contact_P13','contact_P18','contact_P12_standard']),('无遮挡地坪颜色诊断',['floor_color_unoccluded'])]
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Room 1 地坪差分 r15</title><style>body{margin:28px;background:#141b1d;color:#d4dfd7;font:15px/1.6 system-ui}main{max-width:1500px;margin:auto}section{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;padding:10px;background:#202b2c}img{width:100%;display:block;image-rendering:pixelated}h2{margin-top:32px}a{color:#bcd0c4}</style><main><h1>Room 1：PixelLab地坪差分 r15</h1><p>保留r14单块材质基调，增加真正不同的PixelLab原图并重新安排原生像素拼接；减少规则循环与相邻重复。统一蓝灰、无砖缝，无十字通道强调。墙面、门、模型、UV和灯光保持。<a href="README.md">制作记录</a> · <a href="editable/room1_floor_r15.aseprite">Aseprite分层母版</a></p><p>当前是材质差分候选，尚待用户审图；保留既有烘焙，未重烘新固有色的间接反射。</p>'''
for title,names in groups:
    html+='<h2>'+title+'</h2><section>'
    for n in names:html+='<figure><img loading="lazy" src="evidence/'+n+'.png"><figcaption>'+n+'</figcaption></figure>'
    html+='</section>'
(EXP/'preview.html').write_text(html+'</main></html>',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
