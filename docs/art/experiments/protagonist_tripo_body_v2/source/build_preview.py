"""Readable static review of body cleanup and separate provisional pose tests."""
from pathlib import Path
import json,html
EXP=Path(__file__).resolve().parents[1]
build=json.loads((EXP/'source/build_report.json').read_text(encoding='utf-8'))
probe=json.loads((EXP/'source/motion_probe_report.json').read_text(encoding='utf-8'))
qa=json.loads((EXP/'source/independent_validation.json').read_text(encoding='utf-8'))
parts=[]
for name,title in [('front','全身正面'),('side','全身侧面'),('back','全身背面'),('quarter','全身斜视'),('feet','脚部前侧'),('foot_side','脚部侧面')]:
 parts.append(f'<section><h2>{title}</h2><div class="pair"><figure><img src="evidence/{name}_before.png"><figcaption>v1 原始身体</figcaption></figure><figure><img src="evidence/{name}_after.png"><figcaption>v2 脚趾包络修整，其他人体表面保留</figcaption></figure></div></section>')
poses=[]
labels={'rest':'原始A姿势 · Frame 1','raise_arms':'抬臂诊断 · Frame 20','bend_elbows':'弯肘诊断 · Frame 40','step':'迈步关节诊断 · Frame 60'}
for row in probe['poses']:
 name=row['name'];poses.append('<h3>'+labels[name]+'</h3><div class="three">'+''.join(f'<figure><img src="evidence/probe_{name}_{view}.png"><figcaption>{title}</figcaption></figure>' for view,title in [('front','正面'),('side','侧面'),('quarter','斜视')])+'</div>')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>主角身体 v2 · 局部修整与动作探针</title><style>body{max-width:1600px;margin:32px auto;padding:0 24px;background:#142023;color:#e0e6df;font:17px/1.65 system-ui}h1{font-size:29px}h2{font-size:22px}h3{font-size:18px}a{color:#b9d9d7}.pair{display:grid;grid-template-columns:1fr 1fr;gap:14px}.three{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}figure{margin:0}img{width:100%;display:block;background:#293536}figcaption{padding:8px 0;font-size:15px}.note{padding:16px 20px;border:1px solid #859c96;background:#223237}table{border-collapse:collapse;margin:20px 0}td,th{border:1px solid #5e7470;padding:8px 14px;text-align:left}@media(max-width:850px){.pair,.three{grid-template-columns:1fr}}</style>
<h1>主角身体 v2：脚趾局部修整＋临时动作检查</h1><p>2026-11-06 · 本轮未新增Tripo或PixelLab生成。保留身体比例、脸、躯干和四肢姿势；修复脚趾相交并保留独立身体网格。白袍沿用上一轮外形，不在本轮重设计。</p>
<p class="note">静态身体母版与临时骨架工程分开。身体master和GLB重导均通过几何检查；临时19骨骼、4权重归一化的4个姿势已实际渲染。这里没有生产动作、衣物试穿、最终UV、像素贴图或Godot替换。</p>
<p><a href="README.md">说明／已知限制</a> · <a href="model/protagonist_body_v2.blend">干净身体 Blender</a> · <a href="model/protagonist_body_v2.glb">静态身体 GLB</a> · <a href="model/body_v2_motion_probe.blend">临时骨架与姿势 Blender</a> · <a href="source/independent_validation.json">独立检查报告</a></p>
<table><tr><th>项目</th><th>本轮结果</th></tr><tr><td>身体结构</td><td>2950编辑顶点，3271面；导出5896三角面。单一连续身体；无边界、非流形、退化或真自交（GLB属性拆点按精确坐标焊接检查）。</td></tr><tr><td>保护范围</td><td>前脚区域以外2762个表面坐标完全保留；原始corner normals在焊接前保存并恢复。</td></tr><tr><td>临时权重</td><td>19骨；0未绑定顶点，每点最多4项且归一化。手指未分骨。</td></tr><tr><td>动作边界</td><td>4个诊断姿势，不是行走循环。迈步未做落地／重心／根运动；腋下及肘部仍需生产权重精修。</td></tr></table>
'''+''.join(parts)+'''<h2>身体单独的临时骨架探针</h2><p>Blender可跳到1／20／40／60帧。以下各帧检测均无非邻面交叉，但这不能代替动作、皮肤与衣物的最终审查。所有帧有限坐标、无漏绑定；极端局部边长变化仍需后续检查。模型继续使用原始归一化单位，尚未锁最终米制身高。</p>'''+''.join(poses)+'''<h2>范围和下一步</h2><p>先审看身体脚型与体积；接着保持用户接受的白袍外形整理腋下／内外层拓扑，统一休止姿势，再共用骨架试穿。之后加入有限体块头发，复核动作，再固定UV与PixelLab贴图。</p><p><a href="source/build_report.json">几何修整记录</a> · <a href="source/motion_probe_report.json">临时动作参数与诊断</a> · <a href="../protagonist_tripo_body_v1/README.md">原身体来源</a> · <a href="../protagonist_tripo_robe_v2/README.md">保留的白袍外形与拓扑限制</a></p><details><summary>未采用的第一种截断补口：仅留失败证据，不是当前模型</summary><p>技术检查曾无自交，但前脚截断、尖折片损害外形，已否决并重建。下面仅作追溯。</p><div class="pair"><img src="evidence/rejected_flat_cap_feet_after.png"><img src="evidence/rejected_flat_cap_foot_side_after.png"></div></details></html>'''
(EXP/'preview.html').write_text(page,encoding='utf-8')
print('BODY_V2_REVIEW_PAGE_BUILT')
