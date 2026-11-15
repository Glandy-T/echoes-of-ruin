"""Package actual 1280x720 Godot captures; never draw the scene in Python."""
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
E = HERE / 'evidence'
records = json.loads((E/'capture_record.json').read_text(encoding='utf8'))
assert len(records) == 138, len(records)
lookup = {r['file']:r for r in records}
views = [('all','完整双跑与上下平台'),('hero','沿用游戏方向与人物尺度'),
         ('grip','栏体内凹握持边'),('turn','转台内侧接续'),('wall_grip','墙侧握槽'),
         ('side','下跑视线'),('upper','上跑视线'),('landing','转向平台'),
         ('upper_end','楼层平台栏体末端'),('wall_back','转台端墙'),
         ('lower_wall','下跑外墙巡检'),('upper_wall','上跑外墙巡检')]
for view,_ in views:
    a,b = (lookup[f'{mode}_{view}.png'] for mode in ['gray','pixel'])
    for key in ['camera','resolution','ortho_m','keep_aspect','ambient_energy','sun_energy','point_energies','zone_factors','hidden_meshes']:
        assert a[key] == b[key], (view,key)
for row in records:
    assert not row['missing'], row
    with Image.open(E/row['file']) as im:
        assert im.size == (1280,720)
        im.verify()
assert Image.open(HERE/'source/pixellab_C_BODY_raw.png').convert('RGBA').tobytes() == Image.open(HERE/'source/aseprite_readback.png').convert('RGBA').tobytes()
runtime = json.loads((E/'runtime_clearance.json').read_text(encoding='utf8'))
assert min(r['width_m'] for r in runtime['flight_ray_widths']) >= 1.799
assert runtime['turn_apex_width_m'] >= 1.799
assert all(p['overlap_count']==0 for p in runtime['tread_center_static_poses'])

frames = []
for index in range(112):
    with Image.open(E/f'motion_{index:03d}.png') as im:
        frames.append(im.convert('RGB').resize((960,540),Image.Resampling.LANCZOS))
frames[0].save(E/'stair_motion_28s.gif', save_all=True, append_images=frames[1:], duration=250, loop=0, optimize=False)

font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
sheet = Image.new('RGB',(1280,6*390),'#263438')
draw = ImageDraw.Draw(sheet)
for i,(view,title) in enumerate(views[:6]):
    draw.text((12,i*390+5),title,fill='#e2e7e3',font=font)
    for j,mode in enumerate(['gray','pixel']):
        with Image.open(E/f'{mode}_{view}.png') as im:
            sheet.paste(im.convert('RGB').resize((640,360),Image.Resampling.LANCZOS),(j*640,i*390+30))
sheet.save(E/'review_contact_sheet.jpg',quality=92)

web = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8">',
 '<meta name="viewport" content="width=device-width,initial-scale=1">',
 '<title>C 一体化护栏｜完整双跑</title>',
 '<style>body{max-width:1700px;margin:auto;padding:24px;background:#182226;color:#e2e7e3;font:16px/1.6 system-ui,sans-serif}a{color:#b6dfd5}h1{font-size:clamp(24px,3vw,40px)}h2{margin-top:36px}.row{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;padding:8px;background:#263438}img{display:block;width:100%;height:auto}figcaption{padding:4px}p{max-width:1050px}.proof{max-width:960px}@media(max-width:700px){body{padding:12px}.row{grid-template-columns:1fr}}</style>',
 '<h1>C 一体化护栏｜完整双跑</h1>',
 '<p>沿已认可的 C 轮廓补齐两跑、转台、楼层平台及墙侧内凹握槽。两列为本轮同几何、同机位、同光照的灰模与像素表面。点图查看 1280×720 原图。</p>',
 '<p><a href="model/handrail_full_v1.blend">Blender 工程</a> · <a href="README.md">范围与检查说明</a> · <a href="../../../../assets/art/cryo_handrail_full_v1/textures/C_BODY.aseprite">分层 Aseprite</a></p>',
 '<p>造型基线：80 mm 栏体、0.90 m 握持边、1.10 m 栏顶。墙侧槽向墙内凹 67 mm。净宽目标 1.80 m；以导入碰撞实测及源网格检查分别核对。局部巡检采用临时剖切，逐图记录隐藏对象，未改正式场景。</p>']
md = ['# C 一体化护栏｜完整双跑','',
 '完整双跑候选。每组同几何、机位、光照；点图看 1280×720 原图。', '',
 '[Blender 工程](model/handrail_full_v1.blend) · [范围与检查](README.md)', '']
for view,title in views:
    web += [f'<h2>{title}</h2>','<div class="row">']
    md += [f'## {title}','','| 本轮灰模 | PixelLab 像素表面 |','|---|---|',
           f'| [![灰模](evidence/gray_{view}.png)](evidence/gray_{view}.png) | [![像素](evidence/pixel_{view}.png)](evidence/pixel_{view}.png) |','']
    for mode,title2 in [('gray','本轮灰模'),('pixel','PixelLab 像素表面')]:
        file = f'evidence/{mode}_{view}.png'
        web += [f'<figure><figcaption>{title2}</figcaption><a href="{file}"><img src="{file}" width="1280" height="720" loading="lazy" alt="{title2} {title}"></a></figure>']
    web += ['</div>']
web += ['<h2>实际实时灯光</h2><div class="row">']
for name,title in [('baseline','应急最低亮度'),('occupied','人物所在区激活')]:
    file=f'evidence/pixel_{name}.png'
    web += [f'<figure><figcaption>{title}</figcaption><a href="{file}"><img src="{file}" width="1280" height="720" alt="{title}"></a></figure>']
web += ['</div><p>灯条沿用既有位置，点光源减少到原审图 0.18 倍以适配浅色完整栏体；基准亮度与激活亮度保持 1:5。该亮度为本轮审图配置，未冻结为全楼最终照明。</p>',
 '<a href="evidence/stair_motion_28s.gif"><img class="proof" src="evidence/stair_motion_28s.gif" width="960" height="540" alt="28秒人物与灯光演示"></a>',
 '<p>演示包含停留、退回、转台和上跑。纸片人物沿预定路径播放；不能据此宣称移动控制器、碰撞爬楼或寻路已完成。</p>',
 '<h2>PixelLab 实际出图</h2><a href="evidence/pixellab_result.jpg"><img class="proof" src="evidence/pixellab_result.jpg" alt="PixelLab 官方Creator实际结果"></a>',
 '<p>本轮 9 次生成额度，月额度余 1,991 次。使用项目自有 M06-01-R1 图库输入，原图没有程序化污斑或改绘。C_SLOT 复用同图并由材质略压暗，未另画主体。</p>',
 '<p><a href="source/generation_record.json">生成记录</a> · <a href="evidence/runtime_clearance.json">Godot 净宽与静态胶囊</a> · <a href="model_manifest.json">源模型记录</a> · <a href="evidence/capture_record.json">逐图相机和剖切</a></p></html>']
md += ['## 实时灯光与来源','',
       '[![28秒演示](evidence/stair_motion_28s.gif)](evidence/stair_motion_28s.gif)','',
       '人物沿预定路径播放；运动控制器与正式安装尚未验证。', '',
       '[PixelLab 出图证据](evidence/pixellab_result.jpg) · [额度与来源](source/generation_record.json) · [Godot 碰撞实测](evidence/runtime_clearance.json)']
(HERE/'preview.html').write_text('\n'.join(web)+'\n',encoding='utf8')
(HERE/'preview.md').write_text('\n'.join(md)+'\n',encoding='utf8')
class Links(HTMLParser):
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in ['src','href']: assert (HERE/value).exists(),value
Links().feed('\n'.join(web))
manifest={'godot_captures':len(records),'comparison_pairs':len(views),
          'resolution':[1280,720],'same_camera_and_lighting_per_pair':True,
          'missing_maps':0,'aseprite_rgba_matches_raw':True,
          'runtime_width_min_m':min(r['width_m'] for r in runtime['flight_ray_widths']),
          'turn_width_m':runtime['turn_apex_width_m'],
          'raw_pixel_png_sha256':hashlib.sha256((HERE/'source/pixellab_C_BODY_raw.png').read_bytes()).hexdigest(),
          'glb_sha256':hashlib.sha256((ROOT/'assets/art/cryo_handrail_full_v1/cryo_handrail_full_v1.glb').read_bytes()).hexdigest(),
          'blend_sha256':hashlib.sha256((HERE/'model/handrail_full_v1.blend').read_bytes()).hexdigest()}
(HERE/'review_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(manifest,ensure_ascii=False))
