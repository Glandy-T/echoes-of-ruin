"""Static review of independent unmodified Tripo candidates; no asset editing."""
from pathlib import Path
import html,json
EXP=Path(__file__).resolve().parents[1]
qa=EXP/'source/robe_topology_check.json'
report=json.loads(qa.read_text(encoding='utf-8')) if qa.exists() else {'status':'PENDING_STATIC_QA'}
rows=[]
for name,label in [('front','正面'),('side','侧面'),('back','背面'),('quarter','斜视')]:
 rows.append(f'<section><h2>{label}</h2><div class="pair"><figure><img src="../protagonist_tripo_body_v1/evidence/blender_{name}.png"><figcaption>身体 v1 · 原始导入</figcaption></figure><figure><img src="evidence/blender_{name}.png"><figcaption>白袍 v2 · 外形参考，结构未通过</figcaption></figure></div></section>')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>主角分件候选 · 身体与白袍</title>
<style>body{max-width:1600px;margin:32px auto;padding:0 24px;background:#142023;color:#e0e6df;font:17px/1.65 system-ui}h1{font-size:29px}h2{font-size:21px}a{color:#b9d9d7}p{max-width:1150px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0}img{width:100%;display:block;background:#293536}figcaption{padding:8px 0}.notice{padding:16px 20px;border:1px solid #859c96;background:#223237}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:14px}@media(max-width:800px){.pair{grid-template-columns:1fr}}</style>
<h1>主角分件候选：身体 v1＋白袍 v2</h1>
<p>2026-11-06 · Tripo 国内版 P2.0 · 独立网格，为换装与共享骨架准备。四组图均为 Blender 原始导入，1280×720。每件各自居中构图，<strong>不代表两者已对齐、试穿或同尺度</strong>。</p>
<p class="notice">当前门槛：审看外形→处理静态问题→统一身高与休止姿势→试穿→共享骨架与抬臂／弯肘／行走测试→最终UV和PixelLab贴图。当前没有骨架、权重、最终UV、贴图或游戏替换。身体脚趾局部28对相交必须先简化；白袍272对相交、2条非流形边，须重新整理腋下与内外层拓扑，不能直接绑骨。</p>
<p><a href="README.md">当前说明</a> · <a href="model/protagonist_robe_v2_inspection.blend">白袍 Blender</a> · <a href="../protagonist_tripo_body_v1/model/protagonist_body_v1_inspection.blend">身体 Blender</a> · <a href="source/generation_record.json">生成记录</a> · <a href="source/mesh_audit.json">导入统计</a></p>
'''+''.join(rows)+'''<h2>白袍生成结果实拍</h2><p>用项目自有仅衣服灰模正反面引导；未上传Pixel Canals内容。文字第一稿附带手脚已拒绝，本稿无附带人形。画面上的网格不是变形或动画验收。</p><figure style="max-width:650px"><img src="evidence/tripo_robe_front.png"><figcaption>Tripo网页生成结果</figcaption></figure><h2>白袍独立静态检查：未通过</h2><figure><img src="evidence/independent_underhem_opening.png"><figcaption>下摆开口技术图；开口成立不等于整件拓扑通过。</figcaption></figure><p><a href="source/robe_topology_check.json">完整QA记录</a> · <a href="../protagonist_tripo_body_v1/source/body_topology_check.json">身体QA</a></p><pre>'''+html.escape(json.dumps(report,ensure_ascii=False,indent=2)[:10000])+'''</pre><h2>原始来源与旧版</h2><p><a href="source/guide_front.png">原创正面输入</a> · <a href="source/guide_back.png">原创背面输入</a> · <a href="source/guide_provenance.json">输入来源</a> · <a href="model/protagonist_tripo_robe_v2_raw.glb">原始GLB</a> · <a href="model/protagonist_tripo_robe_v2_raw.obj">原始四边面OBJ</a> · <a href="../protagonist_tripo_robe_v1/README.md">失败文字稿</a> · <a href="../protagonist_structure_v3/README.md">停止修补的结构v3</a> · <a href="../protagonist_tripo_cn_cleanup_v2/preview.html">保留的头发v2来源</a></p></html>'''
(EXP/'preview.html').write_text(page,encoding='utf-8')
print('PREVIEW_BUILT',report.get('status'))
