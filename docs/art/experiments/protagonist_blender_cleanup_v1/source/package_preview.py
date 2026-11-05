"""Arrange actual Blender renders; no AI image generation or painted textures."""
from pathlib import Path
from PIL import Image,ImageDraw
import json

EXP=Path(__file__).resolve().parents[1]
views=['front','side','back','quarter','back_quarter']
for name in views:
 sheet=Image.new('RGB',(960,746),(35,44,46));draw=ImageDraw.Draw(sheet)
 for i,version in enumerate(['before','after']):
  im=Image.open(EXP/'evidence'/f'{version}_{name}.png');assert im.size==(1280,720)
  sheet.paste(im.crop((400,0,880,720)),(i*480,26));draw.text((i*480+14,7),version.upper(),fill=(220,230,225))
 sheet.save(EXP/'evidence'/f'comparison_{name}.jpg',quality=95)
sheet=Image.new('RGB',(1280,386),(35,44,46));draw=ImageDraw.Draw(sheet)
for i,name in enumerate(['front','side','back','quarter']):
 im=Image.open(EXP/'evidence'/f'part_ids_{name}.png').crop((360,0,920,720));im.thumbnail((280,360))
 sheet.paste(im,(i*320+(320-im.width)//2,25));draw.text((i*320+16,6),name.upper(),fill=(220,230,225))
sheet.save(EXP/'evidence/part_ids_views.jpg',quality=95)
v=json.loads((EXP/'source/validation.json').read_text('utf8'))
total=sum(p['triangles'] for p in v['saved_blend_meshes'])
page=f'''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>主角本地修模试作 v1</title><style>body{{max-width:1250px;margin:30px auto;padding:0 20px;background:#182225;color:#e3e9e4;font:16px/1.75 system-ui}}a{{color:#a1d7d5}}img{{display:block;max-width:100%;height:auto}}h1{{font-size:27px}}.pairs{{display:grid;grid-template-columns:repeat(auto-fit,minmax(440px,1fr));gap:25px}}figure{{margin:0}}figcaption{{margin:8px 0}}.warning{{border-left:4px solid #c6af82;padding:5px 16px;background:#242d2e}}</style><h1>主角本地修模试作 v1</h1><p>从已下载H2.5灰模继续，在Blender本地整理头部／头发及可编辑部件。原始GLB保留；云端调用0次、Tripo额度消耗0。</p><p><a href="model/protagonist_cleanup_v1.blend">Blender工程</a> · <a href="model/protagonist_cleanup_v1.glb">独立GLB候选</a> · <a href="README.md">修改与限制</a> · <a href="source/validation.json">保存／导出回读</a></p><div class="warning">未完成角色验收：手指和脚仍为原有粗模；肩背补面、领口、发型厚度与形体贴合仍需审查。没有UV、像素贴图、绑定或Godot角色替换。全候选{total}三角面，包含局部修复支撑面，仍待正式拓扑整理。</div><h2>当前部件识别图</h2><p>深发、浅袍只是纯色材质ID，便于识别网格；没有制作最终颜色图或其他贴图。头发、刘海、头、颈、袍体／袖子、手、脚共7个可编辑对象。</p><img src="evidence/part_ids_views.jpg"><h2>同机位灰模：左原始，右本地修模</h2><p>1280×720实际Blender Workbench渲染，使用同一组相机、背景及光照显示。头部／头发已重新建形，不称为原形完全不动。房间场景未改变。</p><div class="pairs">'''
for name,label in [('back','背面：原碎发与新发块'),('front','正面：侧分与弱五官'),('side','侧面：头发厚度与人体轮廓'),('quarter','前斜侧'),('back_quarter','后斜侧：肩背也要看')]:
 page+=f'<figure><figcaption>{label}</figcaption><a href="evidence/comparison_{name}.jpg"><img src="evidence/comparison_{name}.jpg"></a></figure>'
page+='</div><h2>制作参考</h2><p>沿用项目自身三视图v2，侧分长发、弱五官、简单统一休眠袍。下图仅作设计参考，不是已经完成的角色贴图。</p><img width="192" height="256" src="../protagonist_turnaround_v2/views/front.png"></html>'
(EXP/'preview.html').write_text(page,encoding='utf8')
print('PACKAGED_LOCAL_CLEANUP_REVIEW')
