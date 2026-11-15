"""Read actual Godot evidence and assemble a before/after material review."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
E = HERE / 'evidence'
rows = json.loads((E/'capture_record.json').read_text(encoding='utf8'))
assert len(rows) == 32, len(rows)
lookup = {row['file']:row for row in rows}
views = [('grip','栏体握槽'),('wall_grip','墙侧握槽'),('tread_contact','踏步靠墙端'),
         ('platform_contact','平台墙脚转角'),('turn','折返接续'),('all','完整双跑'),
         ('hero','游戏方向与人物尺度'),('upper_end','楼层平台末端'),('side','下跑'),
         ('upper','上跑'),('landing','转向平台'),('wall_back','转台端墙'),
         ('lower_wall','下跑外墙全貌'),('upper_wall','上跑外墙全貌'),
         ('baseline','最低亮度'),('occupied','所在区激活照明')]
for view,_ in views:
    a,b = (lookup[f'{mode}_{view}.png'] for mode in ['a','b'])
    for key in ['resolution','camera','ortho_m','keep_aspect','ambient_energy','sun_energy','point_energies','zone_factors','hidden_meshes']:
        assert a[key] == b[key], (view,key)
    for record in [a,b]:
        with Image.open(E/record['file']) as im:
            assert im.size == (1280,720)
            im.verify()

font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
sheet = Image.new('RGB',(1280,390*6),'#263438')
d = ImageDraw.Draw(sheet)
for i,(view,title) in enumerate(views[:6]):
    d.text((12,i*390+5),title+'　A 原底材 / B 位置旧化',font=font,fill='#e2e7e3')
    for j,mode in enumerate(['a','b']):
        with Image.open(E/f'{mode}_{view}.png') as im:
            sheet.paste(im.convert('RGB').resize((640,360),Image.Resampling.LANCZOS),(640*j,390*i+30))
sheet.save(E/'contact_comparison.jpg',quality=92)

web = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8">',
 '<meta name="viewport" content="width=device-width,initial-scale=1">',
 '<title>C 完整双跑｜按部位旧化</title>',
 '<style>body{max-width:1700px;margin:auto;padding:24px;background:#182226;color:#e2e7e3;font:16px/1.6 system-ui,sans-serif}a{color:#b6dfd5}h1{font-size:clamp(24px,3vw,40px)}h2{margin-top:36px}.row{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}figure{margin:0;padding:8px;background:#263438}img{display:block;width:100%;height:auto}figcaption{padding:4px}p{max-width:1050px}.proof{max-width:960px}@media(max-width:700px){body{padding:12px}.row{grid-template-columns:1fr}}</style>',
 '<h1>C 完整双跑｜按部位旧化</h1>',
 '<p>A 保留原材料底面；B 增加 PixelLab 绘制的接触沉积。形体、布局、创作密度、相机和光照相同。点图看 1280×720 原图。</p>',
 '<p>先看握槽、踏步靠墙端和平台角，再看完整候选。大面颗粒是材料本身；新增旧痕围绕实际凹处和接触位置，不画忙碌客流的磨损。</p>',
 '<p><a href="README.md">制作范围与来源</a> · <a href="model/handrail_age_v2.blend">Blender 工程</a> · <a href="../../../../assets/art/cryo_handrail_age_v2/cryo_handrail_age_v2.glb">GLB</a></p>']
md = ['# C 完整双跑｜按部位旧化','',
 'A 原材料底面，B PixelLab 位置旧化。模型形体、相机、光照与像素密度保持。点图看1280×720原图。','',
 '[说明与来源](README.md) · [Blender 工程](model/handrail_age_v2.blend)','']
differences = {}
for view,title in views:
    web += [f'<h2>{title}</h2>','<div class="row">']
    md += [f'## {title}','','| A 原材料 | B 位置旧化 |','|---|---|',
           f'| [![A](evidence/a_{view}.png)](evidence/a_{view}.png) | [![B](evidence/b_{view}.png)](evidence/b_{view}.png) |','']
    a = Image.open(E/f'a_{view}.png').convert('RGB')
    b = Image.open(E/f'b_{view}.png').convert('RGB')
    differences[view] = sum(pa!=pb for pa,pb in zip(a.getdata(),b.getdata()))
    for mode,title2 in [('a','A · 原材料底面'),('b','B · 按部位旧化')]:
        file = f'evidence/{mode}_{view}.png'
        web.append(f'<figure><figcaption>{title2}</figcaption><a href="{file}"><img src="{file}" width="1280" height="720" loading="lazy" alt="{title2} {title}"></a></figure>')
    web += ['</div>']
web += ['<h2>PixelLab 实际生成</h2>',
 '<a href="evidence/pixellab_floor.jpg"><img class="proof" src="evidence/pixellab_floor.jpg" alt="本轮 PixelLab 官方生成结果"></a>',
 '<p>三张原生256px旧化图，本轮27次额度，剩1,964。程序只作结构位置遮罩、原生像素配准和图集包装；主体痕迹由PixelLab绘制。</p>',
 '<p><a href="source/generation_record.json">生成记录</a> · <a href="source/placement_manifest.json">部位分配</a> · <a href="model_manifest.json">模型与UV记录</a> · <a href="evidence/capture_record.json">实际相机和光照</a></p>',
 '<p>这是独立候选，正式场景未替换；用户视觉审查与技术检查分开记录。</p></html>']
(HERE/'preview.html').write_text('\n'.join(web)+'\n',encoding='utf8')
(HERE/'preview.md').write_text('\n'.join(md).rstrip()+'\n',encoding='utf8')
class Links(HTMLParser):
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in ['src','href']: assert (HERE/value).exists(),value
Links().feed('\n'.join(web))
manifest = {'godot_captures':len(rows),'resolution':[1280,720],
 'same_camera_light_geometry_per_pair':True,'render_pixel_difference_count':differences,
 'difference_note':'Counts show the material comparison changed pixels; they are not aesthetic approval or a replacement for reviewing placement.',
 'glb_sha256':hashlib.sha256((ROOT/'assets/art/cryo_handrail_age_v2/cryo_handrail_age_v2.glb').read_bytes()).hexdigest(),
 'blend_sha256':hashlib.sha256((HERE/'model/handrail_age_v2.blend').read_bytes()).hexdigest(),
 'user_review':'pending'}
(HERE/'review_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(manifest,ensure_ascii=False))
