from pathlib import Path
from PIL import Image,ImageDraw
import json,numpy as np,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
ASSET=ROOT/'assets/art/room1_floor_pixellab_r14'
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
report['rejected_outputs']={'contact_b':'long scratch marks; not used','leak_b':'closed outlined puddles; replaced by leak_d','leak_c':'nearly no visible material; replaced by leak_d','base':'single solid color; replaced by text generation base3','base2':'single solid color; replaced by text generation base3'}
report['rejected_outputs'].update({'leak_b':'closed outlined puddles; not used','leak_c':'nearly no visible material; not used','leak_d':'long crack-like outline; not used'})
usage=[json.loads(p.read_text()) for p in EXP.glob('result_*.json')]
report['generations']=sum(p['usage']['generations'] for p in usage)
report['job_count']=len(usage)
bindings=json.loads((EXP/'evidence/floor_bindings.json').read_text())
assert all('room1_floor_pixellab_r14' in b['map'] for b in bindings)
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
old=Image.open(ROOT/'assets/art/room1_floor_palette_r9/floor_with_leaks.png')
new=Image.open(ASSET/'floor_with_leaks.png')
old.save(EXP/'evidence/floor_map_before.png');new.save(EXP/'evidence/floor_map_after.png')
for name in ['before','after']:
    im=old if name=='before' else new
    im.crop((320,450,500,708)).resize((540,774),Image.Resampling.NEAREST).save(EXP/f'evidence/native_contact_{name}.png')
gallery=Image.new('RGB',(768,576),(25,34,38));d=ImageDraw.Draw(gallery)
for i,n in enumerate(['base3','edge','contact_a','contact_c','leak_a']):
    im=Image.open(EXP/'raw'/f'{n}.png').convert('RGB')
    x=(i%3)*256;y=(i//3)*288
    gallery.paste(im,(x,y));d.text((x+6,y+260),n,fill=(210,224,222))
gallery.save(EXP/'evidence/ai_sources.png')
groups=[('同灯光游戏对照：旧地坪 → PixelLab r14',['game_left_before','game_left_after','game_center_before','game_center_after','game_right_before','game_right_after']),('全室地坪与二十舱',['overhead_before','overhead_after']),('材质原色对照',['overhead_color_before','overhead_color_after']),('原生地图',['floor_map_before','floor_map_after']),('舱底原生细节放大',['native_contact_before','native_contact_after']),('实际舱位近景',['pod_contact_before','pod_contact_after']),('四角与门口',['corner_front_left','corner_rear_left','corner_front_right','corner_rear_right','contact_door']),('四处旧漏液与新版P12接触',['contact_P03','contact_P06','contact_P13','contact_P18','contact_P12_standard']),('无遮挡地坪颜色诊断',['floor_color_unoccluded']),('实际PixelLab原图（深色多边形仅为导图占位，不导入场景）',['ai_sources'])]
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Room 1 PixelLab地坪 r14</title><style>body{margin:28px;background:#141b1d;color:#d4dfd7;font:15px/1.6 system-ui}main{max-width:1500px;margin:auto}section{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;padding:10px;background:#202b2c}img{width:100%;display:block;image-rendering:pixelated}h2{margin-top:32px}a{color:#bcd0c4}</style><main><h1>Room 1：PixelLab地坪 r14</h1><p>从干净蓝灰底图重做；四周墙脚、20舱底接触、4处固定旧漏液。没有砖缝或十字通道，不混入旧人工做旧层。墙面与灯带保持r13，灯光与UV不变。<a href="README.md">制作记录</a> · <a href="editable/room1_floor_r14.aseprite">Aseprite分层母版</a></p><p>这是材质候选，尚未获得用户最终审图；当前保留既有烘焙，新固有色的反弹光未重烘。</p>'''
for title,names in groups:
    html+='<h2>'+title+'</h2><section>'
    for n in names:html+='<figure><img loading="lazy" src="evidence/'+n+'.png"><figcaption>'+n+'</figcaption></figure>'
    html+='</section>'
(EXP/'preview.html').write_text(html+'</main></html>',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
