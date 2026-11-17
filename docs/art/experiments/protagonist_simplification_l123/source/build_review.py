"""Read actual masks/captures, measure them, and make labelled review layouts."""
from pathlib import Path
from hashlib import sha256
import json,struct
from PIL import Image,ImageDraw,ImageFont,ImageChops

ROOT=Path(__file__).resolve().parent.parent
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',23)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
tiny=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
geometry=json.loads((ROOT/'source/geometry.json').read_text(encoding='utf8'))
metrics={}

def run(mask,y):
    xs=[x for x in range(128) if mask.getpixel((x,y))]
    assert xs and xs==list(range(xs[0],xs[-1]+1))
    return {'row':y,'x_min':xs[0],'x_max_inclusive':xs[-1],'width_px':xs[-1]-xs[0]+1}

def central_run(mask,y):
    assert mask.getpixel((64,y))
    left=right=64
    while left>0 and mask.getpixel((left-1,y)):left-=1
    while right<127 and mask.getpixel((right+1,y)):right+=1
    return left,right,right-left+1

for level in ['L1','L2','L3']:
    masks={v:Image.open(ROOT/f'source/parts/{level}_{v}_garment_measure_mask.png').getchannel('A') for v in ['front','side']}
    measures={}
    for name,y in [('chest',44),('waist',55),('hem',86)]:
        front=run(masks['front'],y);side=run(masks['side'],y)
        ratio=side['width_px']/front['width_px']
        assert ratio<=.8 if name=='hem' else .55<=ratio<=.65
        for v,m in [('front',front),('side',side)]:
            silhouette=Image.open(ROOT/f'silhouette/{level}_{v}.png').getchannel('A')
            # At chest height short sleeves touch the torso; its separate
            # garment mask intentionally excludes that arm projection.
            if name!='chest':assert central_run(silhouette,y)==(m['x_min'],m['x_max_inclusive'],m['width_px'])
        measures[name]={'front':front,'side':side,'side_to_front':ratio}
    band=[]
    for y in range(40,65):
        ratio=run(masks['side'],y)['width_px']/run(masks['front'],y)['width_px']
        assert .55<=ratio<=.65,(level,y,ratio)
        band.append(ratio)
    head=max(p[1] for p in geometry['views'][f'{level}_front']['geometry']['face'])+1-6
    side_head=max(p[1] for p in geometry['views'][f'{level}_side']['geometry']['face'])+1-6
    assert head==side_head==geometry['views'][f'{level}_front']['head_height_landmark_px']
    metrics[level]={'visible_height_px':117,'crown_y':6,'sole_exclusive_y':123,'head_crown_to_chin_landmark_px':head,'chin_last_row':head+5,
        'measured_heads_high':117/head,'measurements':measures,'torso_rows40_to64_ratio_min':min(band),'torso_rows40_to64_ratio_max':max(band)}

for kind in ['silhouette','two_tone']:
    bg='#e6e5dc' if kind=='silhouette' else '#273236'
    ink='#202a2c' if kind=='silhouette' else '#e4ece7'
    muted='#53615e' if kind=='silhouette' else '#b9cbc2'
    proof=Image.new('RGB',(1260,1030),bg);d=ImageDraw.Draw(proof)
    for i,level in enumerate(['L1','L2','L3']):
        m=metrics[level]
        d.text((i*420+20,12),{'L1':'L1 · 解剖起伏／分指','L2':'L2 · 简单体块／连指手','L3':'L3 · 更硬的轮廓／方体块'}[level],font=font,fill=ink)
        d.text((i*420+20,48),f"实测约{m['measured_heads_high']:.2f}头身 · 同造型／同姿势",font=small,fill=muted)
        for j,view in enumerate(['front','side']):
            y=98+j*400
            im=Image.open(ROOT/f'{kind}/{level}_{view}.png').convert('RGBA')
            rgb={p[:3] for p in im.getdata() if p[3]}
            assert rgb==({(0,0,0)} if kind=='silhouette' else {(218,221,216),(79,94,99)})
            assert im.getbbox()[1]==6 and im.getbbox()[3]==123
            assert set(im.getchannel('A').getdata())=={0,255}
            enlarged=im.resize((384,384),Image.Resampling.NEAREST)
            proof.paste(enlarged,(i*420+18,y),enlarged)
            d.text((i*420+20,y-21),'正面' if view=='front' else '右侧面',font=small,fill=muted)
        w=m['measurements']['waist'];h=m['measurements']['hem'];c=m['measurements']['chest']
        d.text((i*420+20,906),f"腰厚／正宽 {w['side']['width_px']}/{w['front']['width_px']} = {w['side_to_front']:.3f}",font=small,fill=ink)
        d.text((i*420+20,933),f"胸 {c['side']['width_px']}/{c['front']['width_px']} = {c['side_to_front']:.3f}；下摆 {h['side']['width_px']}/{h['front']['width_px']} = {h['side_to_front']:.3f}",font=small,fill=muted)
    d.text((20,990),'128×128原生网格，最近邻整数3倍；两色版仅用于体块判断，档位未选，非成品上色。',font=small,fill=muted)
    proof.save(ROOT/f'evidence/{kind}_comparison.png')

# Evidence calipers are drawn on a separate proof, never on source silhouettes.
caliper=Image.new('RGB',(1260,500),'#e6e5dc');d=ImageDraw.Draw(caliper)
for i,level in enumerate(['L1','L2','L3']):
    d.text((i*420+15,10),level+' · 中央衣身测量，排除手臂',font=small,fill='#202a2c')
    for j,v in enumerate(['front','side']):
        im=Image.open(ROOT/f'silhouette/{level}_{v}.png').convert('RGBA').resize((256,256),Image.Resampling.NEAREST)
        # Show the same native garment crop at integer4x for readable calipers.
        native=Image.open(ROOT/f'silhouette/{level}_{v}.png').convert('RGBA').crop((44,30,84,90)).resize((160,240),Image.Resampling.NEAREST)
        x=i*420+30+j*195;y=75
        caliper.paste(native,(x,y),native)
        d.text((x,45),'正面' if v=='front' else '右侧',font=small,fill='#202a2c')
        for name in ['chest','waist','hem']:
            rec=metrics[level]['measurements'][name][v]
            yy=y+(rec['row']-30)*4+2
            xx=x+(rec['x_min']-44)*4;end=x+(rec['x_max_inclusive']+1-44)*4
            d.line((xx,yy,end,yy),fill='#ae463d',width=2)
            d.line((xx,yy-5,xx,yy+5),fill='#ae463d',width=2);d.line((end,yy-5,end,yy+5),fill='#ae463d',width=2)
            d.text((x,330+['chest','waist','hem'].index(name)*30),f"{ {'chest':'胸44行','waist':'腰55行','hem':'摆86行'}[name]}：{rec['width_px']}px",font=small,fill='#202a2c')
d.text((20,453),'红线只是测量证据；宽度按原生像素含两端计数，未把手臂跨度当成躯干宽度。',font=small,fill='#53615e')
caliper.save(ROOT/'evidence/measurement_calipers.png')

expected=Image.new('RGBA',(256,384))
for i,L in enumerate(['L1','L2','L3']):
    for j,v in enumerate(['front','side']):
        im=Image.open(ROOT/f'two_tone/{L}_{v}.png').convert('RGBA');expected.paste(im,(j*128,i*128),im)
readback=Image.open(ROOT/'evidence/aseprite_readback.png').convert('RGBA')
assert expected.size==readback.size
assert expected.getchannel('A').tobytes()==readback.getchannel('A').tobytes()
assert all(a==b for a,b in zip(expected.getdata(),readback.getdata()) if a[3])
b=(ROOT/'editable/L123_comparison.aseprite').read_bytes();count=struct.unpack_from('<H',b,134)[0];offset=144;layers=[]
for _ in range(count):
    size,kind=struct.unpack_from('<IH',b,offset);data=b[offset+6:offset+size]
    if kind==0x2004:
        flags=struct.unpack_from('<H',data)[0];n=struct.unpack_from('<H',data,16)[0]
        layers.append({'name':data[18:18+n].decode('utf8'),'visible':bool(flags&1)})
    offset+=size
assert len(layers)==24 and all(not l['visible'] for l in layers if l['name'].endswith('_hidden'))

record=json.loads((ROOT/'evidence/game/capture_record.json').read_text(encoding='utf8'))
shots=record['shots'];assert len(shots)==6
first=shots[0];baseline=Image.open(ROOT/'evidence/game'/first['file']).convert('RGB')
gamechecks=[]
actual=Image.new('RGB',(960,700),'#273236');d=ImageDraw.Draw(actual)
contact=Image.new('RGB',(1280,820),'#273236');cd=ImageDraw.Draw(contact)
for index,shot in enumerate(shots):
    assert shot['review_camera_transform']==first['review_camera_transform']
    assert shot['render_camera_transform']==first['render_camera_transform']
    assert shot['render_camera_matches_review'] and shot['fov']==50
    assert shot['output_viewport']==shot['internal_viewport']==[1280,720]
    im=Image.open(ROOT/'evidence/game'/shot['file']).convert('RGB');assert im.size==(1280,720)
    diff=ImageChops.difference(baseline,im);bbox=diff.getbbox()
    outside=diff.copy();outside.paste((0,0,0),(540,240,740,530));assert outside.getbbox() is None
    mode=shot['appearance']['mode'];level,view=mode.split('_');i=int(level[1])-1;j=0 if view=='front' else 1
    # Exact-size crop: no resize; actual screenshot pixels remain1:1.
    x=i*320;y=j*345
    d.text((x+10,y+7),f"{level} {'正面' if view=='front' else '侧面'} · 游戏截图原像素",font=small,fill='#e4ece7')
    actual.paste(im.crop((480,230,800,540)),(x,y+30))
    cd.text((i*426+8,j*402+5),f"{level} {'正面' if view=='front' else '侧面'} · 完整画面缩略",font=small,fill='#e4ece7')
    contact.paste(im.resize((426,240),Image.Resampling.LANCZOS),(i*426,j*402+35))
    gamechecks.append({'file':shot['file'],'sha256':sha256((ROOT/'evidence/game'/shot['file']).read_bytes()).hexdigest(),
        'difference_bounds_vs_L1_front':bbox,'outside_actor_region_identical':True})
actual.save(ROOT/'evidence/game_actual_pixels.png');contact.save(ROOT/'evidence/game_contact_sheet.png')

validation={'brief_scope':'Section3 L1/L2/L3 only','native_canvas':[128,128],'visible_height_all':117,
    'pure_black_silhouettes':True,'two_colour_rgbs':[[218,221,216],[79,94,99]],'alpha_values':[0,255],
    'geometry_metrics':metrics,'measurement_method':'Actual native garment masks and central connected silhouette run. Inclusive x widths at chest44, waist55, hem86. Band40..64 also checked; no arm width included.',
    'aseprite_layers':layers,'aseprite_visible_pixels_and_alpha_exact':True,'aseprite_transparent_rgb_ignored':True,
    'game_screenshot_count':6,'game_output_internal':[1280,720],'same_game_camera_all_six':True,
    'game_world_visible_height_m':record['baseline_visible_height_m'],'game_crop_no_resampling':True,
    'game_crop_source_rect':[480,230,800,540],'game_checks':gamechecks,
    'PixelLab_requests':0,'Tripo_requests':0,'other_generation_requests':0,'selection':'USER_PENDING',
    'not_verified':['Chosen simplification tier','Final costume/colour/face design','3D mesh, UV, rig, animation or lighting']}
(ROOT/'source/measurements.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(ROOT/'source/validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
rows=[]
for L,m in metrics.items():
    w=m['measurements']['waist'];h=m['measurements']['hem'];c=m['measurements']['chest']
    rows.append(f"| {L} | {m['measured_heads_high']:.2f} | {c['side']['width_px']}/{c['front']['width_px']}={c['side_to_front']:.3f} | {w['side']['width_px']}/{w['front']['width_px']}={w['side_to_front']:.3f} | {h['side']['width_px']}/{h['front']['width_px']}={h['side_to_front']:.3f} |")
(ROOT/'source/measurement_table.md').write_text('| 档位 | 实测头身 | 胸厚／正宽 | 腰厚／正宽 | 下摆厚／正宽 |\n|---|---|---|---|---|\n'+'\n'.join(rows)+'\n',encoding='utf8')
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>主角简化程度 L1/L2/L3</title><style>body{max-width:1320px;margin:24px auto;padding:0 20px;background:#1d282c;color:#e1e9e4;font:16px/1.7 system-ui}a{color:#9fdbd2}img{max-width:100%;height:auto}.native{image-rendering:pixelated}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}figure{margin:15px 0}h1{font-size:26px}h2{font-size:22px}table{border-collapse:collapse}td,th{border:1px solid #64766e;padding:8px 12px}@media(max-width:700px){.grid{grid-template-columns:1fr}}</style><h1>阶段一 · 简化程度 L1／L2／L3 · 等待用户选档</h1><p>仅执行新版重设计简报第3节。同一个短发、短袖及膝休眠服、赤脚造型，统一站姿；不使用旧v4/v5导图，不调用PixelLab、Tripo或其他生成服务。</p><p><a href="README.md">说明与实测表</a> · <a href="editable/L123_comparison.aseprite">可编辑Aseprite</a> · <a href="source/measurements.json">原生测量数据</a> · <a href="source/validation.json">交付检查</a></p><h2>1. 纯黑剪影</h2><p>每张原生128×128，头顶y6／脚底exclusive y123，可见117px。上行为正面，下行为右侧面。以下仅整数3倍显示，未等高重采样。</p><img class="native" src="evidence/silhouette_comparison.png" alt="三档正侧面黑剪影"><h2>2. 两色体块</h2><p>三档一律只有两种灰色，没有材质纹理、五官或成品上色。L1多层皮肤过渡在本轮两色限制下不展开，只比较解剖起伏与分指轮廓。</p><img class="native" src="evidence/two_tone_comparison.png" alt="三档两色平涂"><h2>3. 尺寸实测</h2><p>测量衣身本体，排除手臂跨度；胸y44、腰y55、下摆y86，像素含两端计数。胸腰连续40–64行比例也逐行检查。红线只在证据图，不进入剪影素材。</p><img src="evidence/measurement_calipers.png" alt="正侧面厚宽实测"><h2>4. Room 1实际游戏大小</h2><p>独立审图场景继承已冻结Room1：墙r24、地r26、舱r28、门r32、灯B与暗玻璃。沿用实际镜头和纸片受光，六图同机位同身高，内部／输出1280×720；正式角色未改。</p><p>下图直接裁取截图原像素，没有放大或缩小；打开原图可1:1看。每格保留舱体与地面做尺寸背景。网页缩放／窗口不足时仍可能由浏览器整体缩小。</p><a href="evidence/game_actual_pixels.png"><img class="native" src="evidence/game_actual_pixels.png" alt="实际游戏像素1比1裁片"></a><h2>完整1280×720实机截图</h2><div class="grid">'''
for L in ['L1','L2','L3']:
    html+='<section><h3>'+L+'</h3>'
    for v,label in [('front','正面'),('side','侧面')]:
        file=f'evidence/game/game_{L}_{v}.png'
        html+=f'<figure><a href="{file}"><img src="{file}" alt="{L}{label}完整截图"></a><figcaption>{label} · <a href="{file}">1280×720原图</a> · <a href="silhouette/{L}_{v}.png">纯黑原生PNG</a> · <a href="two_tone/{L}_{v}.png">两色原生PNG</a></figcaption></figure>'
    html+='</section>'
html+='''</div><p>只用于选简化档位。未制作背面、最终上色、阶段二服装或新3D，未采用任何档位；正式占位、镜头与布局保持不变。</p></html>'''
(ROOT/'preview.html').write_text(html+'\n',encoding='utf8')
(ROOT/'preview.md').write_text('# 主角简化程度 L1／L2／L3\n\n[说明与测量](README.md) · [可编辑Aseprite](editable/L123_comparison.aseprite)\n\n![纯黑剪影](evidence/silhouette_comparison.png)\n\n![两色平涂](evidence/two_tone_comparison.png)\n\n![实际游戏像素](evidence/game_actual_pixels.png)\n\n仅新版简报第3节，档位待选。PixelLab／Tripo调用均为0。\n',encoding='utf8')
print('\n'.join(rows));print('Six actual Godot captures verified: fixed camera and identical room pixels outside actor area.')
