from pathlib import Path
import json,html
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;views=json.loads((ROOT/'cameras.json').read_text(encoding='utf-8'))
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',23);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19)
sheet=Image.new('RGB',(1600,3510),'white');draw=ImageDraw.Draw(sheet);draw.text((30,24),'标准休眠层 3D Blockout / 0E 三项几何修复 / 冻结',font=font,fill='#222222');draw.text((30,66),'48室 / 960舱；主体186.40×77.80m；墙高3.40m、门高2.40m均为暂定空间尺度',font=small,fill='#555555')
cards=[];image_checks=[]
for i,c in enumerate(views):
 p=ROOT/'views'/(c['name']+'.png');im=Image.open(p).convert('RGB');assert im.size==(1920,1080)
 x=25+(i%2)*790;y=122+(i//2)*480;sheet.paste(im.resize((760,428),Image.Resampling.LANCZOS),(x,y));draw.text((x,y+435),str(i+1).zfill(2)+' '+c['label'],font=small,fill='#222222')
 cards.append(f'<figure><a href="views/{c["name"]}.png"><img loading="lazy" src="views/{c["name"]}.png" alt="{html.escape(c["label"])}"></a><figcaption>{html.escape(c["label"])} <small>{"顶板隐藏" if not c["roof_visible"] else "主区顶板显示，楼梯井向上延续"} / {c["projection"]} / {"轿厢地面参照显示" if c.get("car_floor_visible",True) else "轿厢地面参照隐藏，井道检查"}</small></figcaption></figure>')
 image_checks.append(dict(name=c['name'],width=1920,height=1080))
sheet.save(ROOT/'VIEW_CONTACT_SHEET.png')
s='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>标准层 3D Blockout / 0E</title><style>body{margin:32px;background:#f4f4f1;color:#242424;font-family:system-ui,sans-serif}h1{font-size:26px}p{line-height:1.65;max-width:1000px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:24px}figure{margin:0;background:white;border:1px solid #ddd}img{display:block;width:100%;height:auto}figcaption{padding:14px;font-weight:600}small{display:block;font-weight:400;margin-top:7px;color:#666}@media(max-width:480px){body{margin:14px}main{grid-template-columns:1fr}}</style><h1>标准休眠层整层 3D Blockout</h1><p>依据提交b53aa9b8的0E：人员井道开洞、保护廊楼板补齐、南侧双墙缝闭合。其他接受平面保持。48室/960舱；四个代表室完整闭舱，其余简化真实外包。下列均为实际FreeCAD原生视图，1920×1080，点击打开原图。所有墙体保留；相机仅按标注显示/隐藏主区顶板。楼梯通向+3.80m下一层标高，楼梯井不封顶，上层结构未建。</p><p>墙高3.40m、门高2.40m、层高3.80m、楼板0.10m为暂定空间验证值；柱体仅为1.68m尺度参照。只做灰模空间验证，无材质贴图、场景灯光、最终美术或20层堆叠。</p><main>'''+''.join(cards)+'</main></html>'
(ROOT/'VIEW_GALLERY.html').write_text(s,encoding='utf-8');(ROOT/'qa/image_validation.json').write_text(json.dumps(dict(images=image_checks,contact_sheet_size_px=[1600,3510],native_capture=True,visual_review='pending'),ensure_ascii=False,indent=2),encoding='utf-8')
