"""Build a static review page; never alters image or mesh assets."""
from pathlib import Path
import json,struct,hashlib
from html import escape

EXP=Path(__file__).resolve().parents[1]
raw=EXP/'model/protagonist_tripo_robe_h31_v1_raw.glb'
b=raw.read_bytes();length=struct.unpack_from('<I',b,12)[0]
glb=json.loads(b[20:20+length])
inventory={'file':raw.name,'sha256':hashlib.sha256(b).hexdigest(),'method':'Direct raw GLB JSON chunk inventory, no scene defaults or Blender objects.',
 'asset':glb['asset'],'nodes':glb.get('nodes',[]),'meshes':[
 {'name':m.get('name'),'primitives':[{'positions':glb['accessors'][p['attributes']['POSITION']]['count'],'indices':glb['accessors'][p['indices']]['count']} for p in m['primitives']]} for m in glb.get('meshes',[])]}
(EXP/'source/glb_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
record=json.loads((EXP/'source/generation_record.json').read_text(encoding='utf-8'))
record.update(status='FAIL_STATIC_AND_FUNCTIONAL_CANDIDATE',static_qa='raw_audit.json',glb_inventory='glb_inventory.json',binding_ready=False,adopted=False)
(EXP/'source/generation_record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
groups=[('原白袍v2轮廓参考','raw_reference_v2_front.png'),('新生成原始正面：有可见破面／碎片','raw_front.png'),('新生成背面','raw_back.png'),('新生成侧面','raw_side.png'),('新生成斜侧','raw_quarter.png'),('领口：浅凹封面','raw_neck.png'),('下摆仰视：内部仍有封挡','raw_underhem.png'),('袖口局部：不代表可动画','raw_cuff_plus_y.png')]
cards=''.join('<figure><img src="evidence/'+f+'" alt="'+escape(label)+'"><figcaption>'+escape(label)+'</figcaption></figure>' for label,f in groups)
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>白袍重新生成｜Tripo v3.1</title><style>body{margin:24px;background:#202628;color:#e6e8e6;font:16px/1.6 system-ui;max-width:1600px}a{color:#abdedf}.notice{padding:16px;background:#443c31;border-left:4px solid #bc9f71}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(440px,1fr));gap:16px}figure{margin:0;background:#303637}img{width:100%;display:block}figcaption{padding:10px}h1{font-size:26px}</style><h1>白袍重新生成｜Tripo v3.1</h1><p class="notice">未采用／未绑定。外形保留，但有少量脱离碎片；领口和下摆存在内部封挡。重新生成没有直接得到合格衣物。身体v2、Room1与游戏角色保持不变。</p><p><a href="README.md">检查说明</a> · <a href="model/protagonist_robe_h31_inspection.blend">Blender检查工程</a> · <a href="source/raw_audit.json">原始检查记录</a></p><p>下面是实际Blender原始导入审图。旧版与新版独立按各自边界适配画幅，仅作轮廓参考，不是同尺寸误差对照。无修模、贴图、试穿或绑定。</p><div class="grid">'''+cards+'''</div><p>Tripo网页原始结果：</p><img style="max-width:900px" src="evidence/tripo_candidate.png" alt="Tripo生成结果"><p>下载原始文件和新检查工程均保留；不可把零自交或Quad标签当成可变形拓扑批准。</p></html>'''
(EXP/'preview.html').write_text(page,encoding='utf-8')
print('PREVIEW_AND_GLB_INVENTORY_WRITTEN')
