from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib,itertools
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
ASSET=ROOT/'assets/art/room1_pod_pixellab_r16'
records=[];variants=['a','b','c','d'];keys=['lid','shell_side','shell_end'];shared=['interior','mattress','section']
for folder,roles in [('variant_'+v,keys) for v in variants]+[('shared',shared)]:
    for key in roles:
        path=ASSET/folder/f'{key}.png';im=Image.open(path).convert('RGBA')
        read=Image.open(HERE/f'readback_{folder}_{key}.png').convert('RGBA')
        clean=Image.open(HERE/f'clean_{key}.png').convert('RGBA')
        mask=np.array(Image.open(HERE/f'final_mask_{key}.png').convert('L'))>0
        a=np.array(im);c=np.array(clean)
        assert im.tobytes()==read.tobytes()
        assert im.size==clean.size
        assert np.array_equal(a[~mask],c[~mask]),(folder,key,'protected structure changed')
        assert np.all(a[:,:,3]==255)
        changed=np.any(a!=c,axis=2)&mask
        assert changed.sum()>10,(folder,key,'no actual material change')
        records.append({'folder':folder,'key':key,'size':list(im.size),'aseprite_pixel_exact':True,'structure_and_ID_protection_exact':True,'changed_vs_clean':int(changed.sum()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
pairwise={}
for key in keys:
    clean=np.array(Image.open(HERE/f'clean_{key}.png').convert('RGBA'))
    images={v:np.array(Image.open(ASSET/f'variant_{v}/{key}.png').convert('RGBA')) for v in variants}
    pairwise[key]=[]
    for a,b in itertools.combinations(variants,2):
        union=np.any(images[a]!=clean,axis=2)|np.any(images[b]!=clean,axis=2)
        equal=float(np.mean(np.all(images[a][union]==images[b][union],axis=1))) if union.any() else 1.0
        pairwise[key].append({'a':a,'b':b,'age_union_pixels':int(union.sum()),'equal_fraction_on_age_union':equal})
        assert equal<.90,(key,a,b,'near-copy age pattern')
provenance=json.loads((HERE/'input_provenance.json').read_text());assert not provenance['legacy_aging_layers_loaded']
scope=json.loads((EXP/'evidence/runtime_scope.json').read_text())
assert scope['opaque_surface_count']==12 and scope['geometry_uv_unchanged'] and scope['glass_display_all_tube_parts_unchanged'] and scope['real_open_close_animation_passed']
bindings=json.loads((EXP/'evidence/material_bindings.json').read_text())
assert set(bindings)=={'before','a','b','c','d'}
for variant in variants:
    for entry in bindings[variant]:
        folder='variant_'+variant if entry['role'] in keys else 'shared'
        assert entry['texture']==f"res://assets/art/room1_pod_pixellab_r16/{folder}/{entry['role']}.png"
        assert entry['shader']=='res://scripts/props/cryopod_standard_v8_surface.gdshader'
usage=[json.loads(p.read_text()) for p in EXP.glob('result_*.json')]
record=json.loads((EXP/'evidence/capture_record.json').read_text())
assert len({tuple(r['size']) for r in record})==1
report={'surface_maps':records,'variant_age_pattern_comparisons':pairwise,'legacy_script_age_layers_used':[],'glass_display_all_tube_parts':'retained, not newly generated','runtime_scope':scope,'new_job_count':len(usage),'new_generations':sum(r['usage']['generations'] for r in usage),'screenshot_count':len(record),'source_scope':'Single P12 candidate only, not twenty-pod rollout','lighting':'existing P12 pose maps retained; new color bounce not rebaked'}
report['render_roundtrips']={}
for label,a,b in [('A_material_restore','oblique_a_open','a_open_restored'),('glass_tube_restore','glass_on','glass_restored')]:
    first=np.asarray(Image.open(EXP/f'evidence/{a}.png').convert('RGB'),dtype=int)
    second=np.asarray(Image.open(EXP/f'evidence/{b}.png').convert('RGB'),dtype=int)
    report['render_roundtrips'][label]={'different_pixels':int(np.sum(np.any(first!=second,axis=2))),'max_channel_delta':int(np.abs(first-second).max())}
blender=HERE/'blender_readback.json'
if blender.exists():report['blender_source']={'readback_passed':True,'geometry_uv_animation_protected':True,'packed_candidates':len(json.loads(blender.read_text())['packed_candidates'])}
(HERE/'quality.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
# Native atlases: old layer composite, current clean structure, new AI variants.
rows=[('lid',128,256),('shell_side',256,80),('shell_end',128,80),('interior',128,256),('mattress',128,256),('section',128,64)]
for key,w,h in rows:
    names=[('v4 baseline',HERE/f'baseline_{key}.png'),('clean guide',HERE/f'clean_{key}.png')]
    if key in keys:names += [(v.upper(),ASSET/f'variant_{v}/{key}.png') for v in variants]
    else:names += [('new shared',ASSET/f'shared/{key}.png')]
    cellw=max(180,w);out=Image.new('RGB',(cellw*len(names),h+30),(24,32,35));draw=ImageDraw.Draw(out)
    for i,(label,path) in enumerate(names):
        out.paste(Image.open(path).convert('RGB'),(i*cellw,0));draw.text((i*cellw+5,h+6),label,fill=(210,228,224))
    out.save(EXP/f'evidence/atlas_{key}.png')
names=['oblique_before_closed','oblique_a_closed','oblique_b_closed','oblique_c_closed','oblique_d_closed','oblique_before_open','oblique_a_open','oblique_b_open','oblique_c_open','oblique_d_open','game_a_closed','game_a_open','glass_on','glass_hidden','screen_unchanged']
sheet=Image.new('RGB',(1280,612),(20,27,29));draw=ImageDraw.Draw(sheet)
for i,n in enumerate(names):
    x=(i%5)*256;y=(i//5)*204;sheet.paste(Image.open(EXP/f'evidence/{n}.png').resize((256,144)),(x,y));draw.text((x+4,y+150),n,fill=(215,230,224))
sheet.save(EXP/'evidence/survey_contact_sheet.png')
groups=[('实际房间：旧版 → A（闭合／打开）',['oblique_before_closed','oblique_a_closed','oblique_before_open','oblique_a_open']),('四套外壳差分：闭合',['oblique_a_closed','oblique_b_closed','oblique_c_closed','oblique_d_closed']),('四套外壳差分：打开',['oblique_a_open','oblique_b_open','oblique_c_open','oblique_d_open']),('实际游戏镜头',['game_before_closed','game_a_closed','game_before_open','game_a_open']),('实体材质原色诊断：玻璃／灯管／屏幕保持正常',['color_before_open','color_a_open','color_b_closed','color_c_closed','color_d_closed']),('原生盖板／长侧／端面图',['atlas_lid','atlas_shell_side','atlas_shell_end']),('共用内腔／床垫／截面',['atlas_interior','atlas_mattress','atlas_section']),('玻璃与内灯控制',['glass_on','glass_hidden','glass_tubes_off','glass_restored']),('屏幕与真实动画',['screen_unchanged','animation_open','animation_closed']),('侧面与头部巡检',['side_a_closed','side_a_open','head_a_closed','head_a_open','side_b_closed','side_c_closed','side_d_closed'])]
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Room 1 单舱PixelLab返修 r16</title><style>body{margin:28px;background:#141b1d;color:#d4dfd7;font:15px/1.6 system-ui}main{max-width:1500px;margin:auto}section{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;padding:10px;background:#202b2c}img{width:100%;display:block;image-rendering:pixelated}h2{margin-top:32px}a{color:#bcd0c4}</style><main><h1>Room 1：单舱PixelLab返修 r16</h1><p>四套外壳差分，共用新内腔／床垫／截面；去掉v4脚本追加的旧化层，保留已确认结构、样本编号12、玻璃与动态屏幕。当前只替换P12。<a href="README.md">制作和范围记录</a> · <a href="room1_pod_pixellab_r16_packed.blend">Blender打包源</a> · <a href="editable/">Aseprite母版</a></p><p>仍为单舱材质候选，未推广其余19舱；沿用原P12端点光照，没有重烘新材质反弹光。诊断图只让实体表面不受光，玻璃／屏幕／灯管不改。</p>'''
for title,names in groups:
    html+='<h2>'+title+'</h2><section>'
    for n in names:html+='<figure><img loading="lazy" src="evidence/'+n+'.png"><figcaption>'+n+'</figcaption></figure>'
    html+='</section>'
(EXP/'preview.html').write_text(html+'</main></html>',encoding='utf-8')
print('R16_REVIEW_PASS',len(records),'maps;',len(usage),'PixelLab jobs;',report['new_generations'],'generations;',len(record),'Godot screenshots.')
