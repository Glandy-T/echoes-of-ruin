"""Verify outputs and assemble an offline evidence gallery and byte manifest."""
from pathlib import Path
import json,hashlib,zipfile,html
from PIL import Image
ROOT=Path(__file__).resolve().parent
report=json.loads((ROOT/'visual_blockout_validation.json').read_text(encoding='utf-8'))
saved=json.loads((ROOT/'qa/saved_validation.json').read_text(encoding='utf-8'))
assert report['render_status']=='passed' and saved['saved_readback_passed']
assert saved['fcstd_sha256']==hashlib.sha256((ROOT/'room1_3d_blockout_v2.FCStd').read_bytes()).hexdigest()
assert saved['unchanged_pod_layers']==80 and not saved['positive_volume_collisions']
assert len(saved['parameter_edit_tests'])==5 and all(t['passed'] for t in saved['parameter_edit_tests'])
assert len(report['views'])==8 and report['roof_default_hidden']
stats=[]
for view in report['views']:
 path=ROOT/'evidence/visual_blockout'/(view['name']+'.png')
 im=Image.open(path);im.load();assert im.size==(1920,1080)
 lo,hi=im.convert('L').getextrema();assert hi-lo>50,(view['name'],lo,hi)
 assert len(im.getcolors(1920*1080))>8,(view['name'],'Blank or corrupt image')
 stats.append(dict(name=view['name'],size_px=list(im.size),brightness_range=[lo,hi]))
# Verify every baseline delivery file, in addition to the FCStd hash.
baseline_root=ROOT.parent/'v2';baseline_manifest=json.loads((baseline_root/'manifest.json').read_text(encoding='utf-8'))
for path,meta in baseline_manifest.items():assert hashlib.sha256((baseline_root/path).read_bytes()).hexdigest()==meta['sha256'],path
observations=[
 ('room_proportion','21×9.5m比例','四区与十字通道清楚，横向延展但未见明显失衡。','passed'),
 ('door_to_entry_axis','1.4m门到2.4m入口轴线','两侧各展开0.50m，门口呈明确展开，单人进入未被舱体夹住。','passed'),
 ('pods_near_door','门后左右舱','视觉上近，后墙端余量0.50m；内侧底座距中心线各1.20m，中央轴线保持连续。','passed'),
 ('cross_aisle','3.5m横向通道','较宽敞，仍有主通道层级；未见明显过窄或宽度失衡。','passed'),
 ('pod_spacing','0.7m舱间操作位','单人静态接近可容纳，但偏紧；直径0.45m柱两侧仅各余0.125m。上下舱、转身与辅助操作仍待动作验证。','static_fit_passed_dynamic_use_pending'),
 ('ceiling_height','3.4m暂定净高','比1m舱体高，但与1.68m尺度柱比较未见明显压低或夸张大厅化；保持P测试值。','passed_provisional'),
 ('room_identity','标准化生命保存室身份','低矮单层及统一分层支持标准设备感；中性灰模的重复闭舱排列仍可能带来临床或停尸间联想，最终美术辨识待后续验证。','spatial_organization_passed_art_identity_pending'),
 ('collisions','新增实体碰撞','90个原生实体正体积碰撞0，门洞真实留空；80个原舱分层形状与坐标不变。','passed')]
report.update(visual_review='completed: all eight latest native PNGs inspected; full overview fits frame; all human views use 1.60m eye height and visible 3.40m ceiling',
 acceptance_status='ROOM 1 SPATIAL BLOCKOUT ACCEPTED',
 acceptance_scope='static closed-pod spatial blockout only; not final dimensions, ergonomics, opening sweep, mechanical design or art identity approval',
 visual_judgments=[dict(id=k,question=q,observation=s,status=state,basis='native view inspection and recorded geometry; qualitative spatial judgment') for k,q,s,state in observations],
 image_validation=stats,baseline_manifest_files_unchanged=len(baseline_manifest),
 not_started=['standard floor','12 rooms per zone / 48 rooms per floor','whole building'],
 next_validation=['人体上下舱/转身/辅助操作','开盖机构与扫掠','背部服务系统的设备更换路径','生命保存设备的美术身份'],
 geometry_verification=saved)
(ROOT/'visual_blockout_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
titles={'01_doorway_human_view':'01 门口进入：1.40m门 → 2.40m通道','02_entry_axis_human_view':'02 纵向入口轴线','03_cross_aisle_left_right':'03 横向主通道 · 向左','03b_cross_aisle_right':'03b 横向主通道 · 向右','04_pod_spacing_human_view':'04 舱间0.70m操作位 · 向前','04b_pod_spacing_look_down':'04b 舱间操作位 · 向下','05_room_isometric_open_top':'05 整体斜俯视 · 隐藏顶板','06_room_top':'06 正交俯视 · 平面对照'}
figures=[]
for v in report['views']:
 filename='evidence/visual_blockout/'+v['name']+'.png'
 meta=('眼高1.60m · 竖直视场 '+str(v['vertical_fov_deg'])+'° · 顶板显示') if v['projection']=='perspective' else '正交投影 · 顶板隐藏 · 全部墙体保留'
 figures.append(f'<figure><a href="{filename}"><img src="{filename}" alt="{html.escape(titles[v["name"]])}" loading="lazy"></a><figcaption><strong>{html.escape(titles[v["name"]])}</strong><span>{html.escape(meta)}</span></figcaption></figure>')
rows=''.join(f'<tr><th>{html.escape(q)}</th><td>{html.escape(s)}</td></tr>' for _,q,s,_ in observations)
gallery='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Room 1 v2 · 3D空间验证</title><style>
*{box-sizing:border-box}body{margin:0;background:#f2f2f0;color:#252525;font:16px/1.65 "Microsoft YaHei",sans-serif}main{max-width:1500px;margin:auto;padding:36px 24px}h1{font-size:30px;margin:0 0 8px}p{max-width:1000px}a{color:#303030}nav{display:flex;gap:22px;flex-wrap:wrap;margin:22px 0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}figure{margin:0;background:#fff;border:1px solid #ddd}img{display:block;width:100%;height:auto}figcaption{padding:14px 18px}figcaption span{display:block;color:#666;font-size:14px}.status{padding:14px 18px;border-left:4px solid #444;background:#fff;margin:20px 0}table{border-collapse:collapse;width:100%;background:white}th,td{padding:12px 16px;border-bottom:1px solid #ddd;text-align:left;vertical-align:top}th{width:230px}footer{color:#666;font-size:14px;margin-top:28px}@media(max-width:900px){.grid{grid-template-columns:1fr}main{padding:24px 14px}th{width:150px}}</style><main>
<h1>Room 1 v2 · 3D空间验证</h1><p>21.00×9.50m · 20舱四区 · 墙高3.40m P · 门洞1.40×2.40m P · 闭舱状态。点击任一图片查看1920×1080原图。</p>
<div class="status"><strong>ROOM 1 SPATIAL BLOCKOUT ACCEPTED</strong><br>本阶段静态空间比例通过。0.70m舱间位动作、开盖扫掠、维修更换及最终美术身份仍待验证。未开始标准层。</div>
<nav><a href="room1_3d_blockout_v2.FCStd">可编辑FreeCAD</a><a href="README.md">完整说明</a><a href="visual_blockout_validation.json">验证数据</a><a href="room1_3d_blockout_v2_delivery.zip">交付包</a></nav><section class="grid">'''+''.join(figures)+'''</section><h2>本轮判断</h2><table>'''+rows+'''</table><footer>来源任务501140a / 工程基准b819189 · 2026-10-07 · 原v2文件未修改 · 纯尺度柱高1.68m。</footer></main></html>'''
(ROOT/'VIEW_GALLERY.html').write_text(gallery,encoding='utf-8')
paths=['.gitattributes','README.md','VIEW_GALLERY.html','room1_3d_blockout_v2.FCStd','cameras.json','build_blockout.py','render_blockout.FCMacro','validate_blockout.py','package_blockout.py','visual_blockout_validation.json','qa/saved_validation.json']
paths+=['evidence/visual_blockout/'+v['name']+'.png' for v in report['views']]
paths+=[str(p.relative_to(ROOT)).replace('\\','/') for p in sorted((ROOT/'sources').iterdir()) if p.is_file()]
manifest={p:dict(bytes=(ROOT/p).stat().st_size,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths}
(ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
with zipfile.ZipFile(ROOT/'room1_3d_blockout_v2_delivery.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in paths+['manifest.json']:z.write(ROOT/p,p)
print(f'Packaged {len(paths)} files / 8 native PNGs / {len(baseline_manifest)} unchanged v2 baseline files')
