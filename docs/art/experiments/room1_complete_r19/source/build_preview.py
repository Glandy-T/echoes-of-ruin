"""Index unmodified Godot captures; no pixel-art generation or retouching."""
from pathlib import Path
from html import escape

base = Path(__file__).resolve().parents[1]
parts = ['''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Room 1 · r19 整室整合</title>
<style>body{background:#121b1d;color:#dae0dc;font:16px/1.6 system-ui;margin:28px auto;max-width:1500px;padding:0 24px}a{color:#abcbd2}h1{font-size:30px}h2{margin-top:42px}p{max-width:1000px}figure{margin:0;background:#1e292b;padding:10px}img{display:block;width:100%;image-rendering:pixelated}figcaption{padding:7px 2px;color:#bbc8c4}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.wide{grid-column:1/-1}@media(max-width:800px){.grid{grid-template-columns:1fr}}details{margin:28px 0}</style>
<h1>Room 1 · r19 整室整合</h1><p>2026-10-30 · 20 新舱、01–20 独立编号、各位置受光。墙／地／主门和薄柔光使用已确认版本。布局、人物比例保持；只有 P12 可开盖。整室待最终审图。</p>
<p><a href="README.md">技术说明与限制</a> · <a href="room1_complete_r19.blend">全室 Blender 烘焙源</a> · <a href="../../ROOM1_NEXT_SCHOOL_HANDOFF.md">学校交接</a></p>
<p>F5 标题→「はじめる」。WASD 移动、E 调查、Enter 翻页、Esc 暂停。下列均为实际 Godot 截图；点击查看原始尺寸。</p>''']

def figure(path, title, wide=False):
    return f'<figure class="{"wide" if wide else ""}"><a href="evidence/{escape(path)}.png"><img loading="lazy" src="evidence/{escape(path)}.png" alt="{escape(title)}"></a><figcaption>{escape(title)}</figcaption></figure>'

parts += ['<h2>正式入口与实际游戏</h2><div class="grid">']
for name,title in [('formal_opening_dialogue','标题进入后的开场对白'),('formal_gameplay_start','走出 P12 后'),('formal_main_aisle','中央活动区域'),('formal_door_open','真实检测后主门开启')]:
    parts.append(figure(name,title))
parts += ['</div><h2>全室与单舱</h2><div class="grid">',figure('complete/whole_room_closed','技术巡检：P12 闭盖'),figure('complete/whole_room_open','技术巡检：P12 开盖'),figure('complete/p12_oblique_closed','实际光照下闭盖／玻璃'),figure('complete/p12_oblique_open','实际光照下开盖／内部两侧灯管'),figure('pods_all_20','01–20 全部舱体；仅排列实际截图',True),'</div>']
parts += ['<h2>与整合前相同机位对比</h2><p>左：r18（仅 P12 新舱）；右：r19（20 新舱与独立位置烘焙）。没有改变布局与材质风格。</p><div class="grid">']
for name in ['game_front_left_open','game_front_middle_open','game_front_right_open']:
    parts += [figure('before/'+name,'整合前 · '+name),figure('complete/'+name,'r19 · '+name)]
parts += ['</div><h2>全室光照与接缝检查</h2>',figure('lighting_checks','四角／前墙／门上方／灯槽／地坪／玻璃与 raw 对照；点击原图',True),'<p>技术巡检显示了平时剖切隐藏的前墙；没有把技术机位保存到游戏。原始光图仍有蒙特卡洛噪声，运行使用 OIDN 图。端点插值不是真动态 GI。</p>']
parts += ['<details><summary>其余游戏机位与原始证据</summary><div class="grid">']
for path in sorted((base/'evidence/complete').glob('game_*.png')):
    parts.append(figure('complete/'+path.stem,path.stem))
parts += ['</div><p><a href="evidence/complete/capture_record.json">机位／分辨率／开闭记录</a> · <a href="source/runtime_validation.json">物理运行结果</a> · <a href="source/bake_manifest.json">逐图烘焙合同</a> · <a href="source/independent_bake_audit.json">独立审计</a></p></details>', '<p>走廊与楼梯仍是既有灰盒；3D 主角未制作，本轮未扩大范围。未新增像素美术，原 PixelLab／Aseprite 来源见素材目录。</p></html>']
(base/'preview.html').write_text('\n'.join(parts),encoding='utf-8')
print('R19_PREVIEW_BUILT')
