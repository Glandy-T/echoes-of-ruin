from pathlib import Path
import json,re,math
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;E=HERE/'evidence'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
records=read(E/'capture_record.json');motions=read(E/'motion_record.json');metric_records=read(E/'metric_record.json')
auth=read(E/'auth_capture_record.json');auth_by_file={r['file']:r for r in auth}
validation=read(HERE/'functional_validation.json');assert validation['result']=='PASS'
assert auth_by_file['auth_hidden_before.png']['door_alpha']<.001
assert auth_by_file['auth_yellow.png']['state']=='scanning' and auth_by_file['auth_yellow.png']['door_alpha']>.49
assert auth_by_file['auth_red.png']['state']=='denied' and auth_by_file['auth_red.png']['no_modal']
assert auth_by_file['auth_transfer_black.png']['black_alpha']>.999
assert not auth_by_file['auth_returned_room1.png']['outside'] and auth_by_file['auth_returned_room1.png']['corridor']==-1
def rgb(name):return np.asarray(Image.open(E/(name+'.png')).convert('RGB')).astype(np.int16)
metrics=[]
for case in 'ABCDE':
 signals={};counts={};heights={}
 for state in ['hidden','half','solid']:
  prefix=f'metric_{case}_{state}'
  diff=np.max(abs(rgb(prefix+'_hero')-rgb(prefix+'_empty')),axis=2)
  # Character is centred. Restrict to its projected body region, excluding UI.
  diff[:40]=0;diff[:,:300]=0;diff[:,980:]=0
  mask=diff>3;ys,xs=np.nonzero(mask)
  signals[state]=int(diff.sum());counts[state]=int(mask.sum());heights[state]=int(ys.max()-ys.min()+1) if len(ys) else 0
 hidden=next(r for r in records if r['file']==f'camera_{case}_hidden.png')
 metrics.append({'case':case,'hero_actual_height_px':heights['hidden'],'foreground_empty_percent':round(hidden['foreground_empty_fraction']*100,2),'wall_clearance_m':round(hidden['camera_wall_gap'],3),'half_contrast_retention':round(signals['half']/max(signals['hidden'],1),4),'solid_contrast_retention':round(signals['solid']/max(signals['hidden'],1),4),'signal':signals,'visible_pixels':counts})
 assert signals['hidden']>0 and signals['solid']/signals['hidden']<.02
 assert signals['half']/signals['hidden']>.35
for name,samples in motions.items():
 assert all(b['time']>a['time'] for a,b in zip(samples,samples[1:]))
 if name.endswith('approach'):assert samples[0]['alpha']<.001 and samples[-1]['alpha']<.001 and max(s['alpha'] for s in samples)>.49
 if name=='distance_lateral':assert min(s['alpha'] for s in samples)>.49
 if name=='region_lateral':assert samples[0]['alpha']>.49 and samples[-1]['alpha']<.001
 # Shared palette avoids artificial palette flicker in the comparison animation.
 frames=[Image.open(E/s['file']).convert('RGB').resize((640,360),Image.Resampling.NEAREST) for s in samples]
 palette_sample=Image.new('RGB',(640*4,360*math.ceil(len(frames)/4)))
 for i,im in enumerate(frames):palette_sample.paste(im,((i%4)*640,(i//4)*360))
 palette=palette_sample.quantize(colors=256)
 decorated=[]
 for im,s in zip(frames,samples):
  draw=ImageDraw.Draw(im);draw.rectangle((0,0,640,19),fill=(14,23,26));draw.text((8,4),f'B / {name} / t={s["time"]:.2f}s / alpha={s["alpha"]:.2f}',fill=(219,238,238))
  decorated.append(im.quantize(palette=palette,dither=Image.Dither.NONE))
 durations=[max(20,round((b['time']-a['time'])*1000)) for a,b in zip(samples,samples[1:])]+[550];durations[0]+=450
 decorated[0].save(E/(name+'.gif'),save_all=True,append_images=decorated[1:],duration=durations,loop=0,disposal=2,optimize=False)
(HERE/'comparison_analysis.json').write_text(json.dumps({'metrics':metrics,'functional_result':validation['result'],'motion_sequences':{n:len(s) for n,s in motions.items()}},indent=2),encoding='utf-8')
def sheet(state):
 out=Image.new('RGB',(1280,3*382),(15,24,27));draw=ImageDraw.Draw(out)
 for i,case in enumerate('ABCDE'):
  im=Image.open(E/f'camera_{case}_{state}.png').convert('RGB').resize((640,360),Image.Resampling.NEAREST);x=(i%2)*640;y=(i//2)*382
  out.paste(im,(x,y));draw.text((x+8,y+363),case+' / '+state,fill='#bfdddd')
 out.save(E/(state+'_contact.jpg'),quality=94)
for state in ['hidden','half','solid']:sheet(state)
def fig(n,t,ext='png'):return f'<figure><a href="evidence/{n}.{ext}"><img loading="lazy" src="evidence/{n}.{ext}"></a><figcaption>{t}</figcaption></figure>'
configs=[('A','原构图',8,50),('B','前移',6,50),('C','缩小视角',8,38.5),('D','适度组合',7,44),('E','更近构图',4,50)]
rows=''.join(f'<tr><td>{c}</td><td>{name}</td><td>{distance}m</td><td>{fov}°</td><td>{m["foreground_empty_percent"]:.1f}%</td><td>{m["hero_actual_height_px"]}px</td><td>{m["wall_clearance_m"]:.1f}m</td></tr>' for (c,name,distance,fov),m in zip(configs,metrics))
page=['''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>4F 镜头与墙门显现对比 v6</title><style>body{max-width:1440px;margin:auto;padding:28px;background:#111b20;color:#dae8eb;font:16px/1.7 system-ui}h1{font-size:29px}h2{margin-top:42px}p{max-width:1150px}.note{padding:16px;background:#203034;border-left:3px solid #88c9b9}a{color:#a5dcd2}img{width:100%;display:block;image-rendering:pixelated}figure{margin:0}figcaption{padding:10px;color:#adc7cf}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:16px}table{border-collapse:collapse;width:100%;font-size:15px}td,th{padding:9px;border-bottom:1px solid #35484c;text-align:left}select{background:#243a40;color:#e1f0ef;font:inherit;padding:8px;margin:8px}details{margin:20px 0}summary{cursor:pointer}</style><h1>4F 镜头与墙门显现对比 v6</h1><p class="note">独立F6：scenes/dev/cryo_4f_camera_compare_v6.tscn。1–5切换镜头A–E；T切换沿墙距离／门前区域；R切换50%半显／100%实体对照；F7切换自动／强制隐藏／强制显现；F8到门外，Home回室内。E沿用认证、开门与黑门洞穿越。入口从Room1开始，按F8可直接比较。A与距离规则只是首个测试状态，尚未选定最终方案。</p><p>按用户澄清：相机始终留在前侧墙外；前侧门墙平时隐藏，靠近后整段渐显，离开渐隐。没有人物周围挖洞。墙门按房间的21m左右边界分段，共32个前侧门墙段；单一可见表面复用原像素颜色、UV与光图，背景房壳仅在当前走廊视图隐藏，物理碰撞保持。</p><p><a href="README.md">实现、取舍及复建</a> · <a href="functional_validation.json">功能验证</a> · <a href="comparison_analysis.json">图像测量</a> · <a href="evidence/capture_record.json">逐图相机记录</a></p><h2>镜头对比</h2><p>统一高度2.2m、1280×720。同一状态下五种镜头使用相同人物位置。B/C/D的角色大小接近，用于比较前移、镜头缩角及组合的透视差异；E保留更紧的构图作比较。下方空白比例是走廊中线、前墙隐藏时，下边地坪边界之外的屏幕占比；不代表所有姿态的空白比例。</p><table><thead><tr><th>方案</th><th>方式</th><th>距离</th><th>水平FOV</th><th>前景空白</th><th>实测角色高</th><th>相机墙外余量</th></tr></thead><tbody>''',rows,'''</tbody></table><select id="camera"><option>A</option><option>B</option><option>C</option><option>D</option><option>E</option></select><select id="state"><option value="hidden">平时隐藏</option><option value="half">靠近50%半显</option><option value="solid">靠近100%实体</option></select><figure><img id="chosen"><figcaption>点击下方联系表可对比，所有原图保留1280×720。</figcaption></figure><script>let c=document.getElementById('camera'),s=document.getElementById('state');function update(){document.getElementById('chosen').src='evidence/camera_'+c.value+'_'+s.value+'.png'}c.onchange=update;s.onchange=update;update()</script><details open><summary>五种镜头并列：前侧墙隐藏</summary>''',fig('hidden_contact','原尺寸PNG通过上方切换查看。','jpg'),'</details><details><summary>靠近后50%半显</summary>',fig('half_contact','相同近门位置。','jpg'),'</details><details><summary>100%实体遮挡对照</summary>',fig('solid_contact','实体门墙会挡住人物，保留此状态用于比较。','jpg'),'</details><h2>触发方式：同位置对照</h2><p>距离规则：靠近这段墙的任何位置都会显现。区域规则：还要位于门中心左右1.2m内；离开到1.5m外才释放。两种规则进入墙面距离1.15m，退出1.35m，离开保持0.20s后渐隐，显隐渐变0.28s。门认证期间在原交互范围内额外保持其显示面可读。</p><div class="grid">']
for mode in range(2):
 for state,label in [('far','远离前侧墙'),('near_wall','贴近墙但偏离门'),('near_door','靠近门前')]:page.append(fig(f'trigger_{mode}_{state}',('距离规则' if mode==0 else '门前区域')+'：'+label))
page.append('</div><h2>运动过程：接近、离开与横移</h2><p>使用真实CharacterBody移动和原碰撞，B镜头、50%显现。GIF以640×360精确缩半、共享调色板输出，首尾增加停顿方便观察；1280×720逐帧PNG与原始状态时间保留。</p><div class="grid">')
for n,t in [('distance_approach','距离：走近→停留→退开'),('region_approach','区域：走近→停留→退开'),('distance_lateral','距离：贴墙横向离开门中心'),('region_lateral','区域：贴墙横向离开门前区域')]:page.append(fig(n,t,'gif'))
page.append('</div><h2>显现是否挡人物</h2><p>固定位置、固定角色帧，分别拍“有人物／隐藏人物”图对，测量人物对画面的差异信号；再与前侧墙完全隐藏时比较。50%状态保留约一半的人物对比度，100%实体时信号接近0，角色被挡住。这是实测遮挡影响，不是最终强度选择。</p><table><tr><th>镜头</th><th>50%半显：对比度保留</th><th>100%实体：对比度保留</th></tr>')
for m in metrics:page.append(f'<tr><td>{m["case"]}</td><td>{m["half_contrast_retention"]*100:.1f}%</td><td>{m["solid_contrast_retention"]*100:.1f}%</td></tr>')
page.append('</table><h2>认证与黑门洞往返实机</h2><div class="grid">')
for n,t in [('auth_hidden_before','原交互范围内，按E前门墙仍隐藏'),('auth_yellow','E后整段显现，小窗黄闪'),('auth_red','小窗红灯拒绝，保持原碰撞，无权限弹窗已取消'),('auth_main_open_inside','原主门认证开门，室内镜头保持'),('auth_transfer_black','第二次E，全黑下换镜'),('auth_outside_B','出门后启用B镜头'),('auth_returned_room1','E返回室内，恢复原8m／50°镜头')]:page.append(fig(n,t))
page.append('</div><p>120组相机位置检查通过；原Room1镜头恢复、隐藏墙碰撞、门禁拒绝、黑屏下换镜与返回通过。阈值附近往复没有重复显隐。其他连接区／楼梯仍沿用旧镜头与既有灰盒。F5与v5入口保持，本页不选定最终组合；仍需用户决定镜头、触发方式和显现强度。</p></html>')
html=''.join(page)
for link in re.findall(r'(?:href|src)="([^"]+)"',html):assert (HERE/link).exists(),link
(HERE/'preview.html').write_text(html,encoding='utf-8')
print(json.dumps({'metrics':metrics,'result':'CAMERA_V6_PREVIEW_PASS'},ensure_ascii=True))
