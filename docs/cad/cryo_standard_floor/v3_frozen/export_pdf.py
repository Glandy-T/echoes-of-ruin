"""Render the same A2 primitives used by the FreeCAD TechDraw snapshots."""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'exports';QA=ROOT/'qa';K=72/25.4
def color(value):
 if len(value)==4:value='#'+''.join(ch*2 for ch in value[1:])
 return HexColor(value)
pdfmetrics.registerFont(TTFont('SimSun',r'C:\Windows\Fonts\simsun.ttc',subfontIndex=0))
pages=json.loads((OUT/'drawing_data.json').read_text(encoding='utf-8'))
path=OUT/'standard_floor_v3_frozen.pdf';c=canvas.Canvas(str(path),pagesize=(594*K,420*K),pageCompression=1)
c.setTitle('Echoes of Ruin 标准休眠层 v3 / 二维工程方案');c.setAuthor('Echoes of Ruin / Codex')
out_of_bounds=[]
for p in pages:
 c.bookmarkPage(p['code']);c.addOutlineEntry(p['code']+' '+p['title'],p['code'])
 for a in p['items']:
  c.saveState();k=a['k']
  if k=='text':
   size=a['size']*K;c.setFont('SimSun',size);c.setFillColor(color(a['color']));x,y=a['x']*K,(420-a['y'])*K
   width=pdfmetrics.stringWidth(a['s'],'SimSun',size);left=x-width/2 if a['anchor']=='middle' else x-width if a['anchor']=='end' else x
   if left<12*K-1 or left+width>582*K+1 or a['y']<12 or a['y']>408:out_of_bounds.append(dict(page=p['code'],text=a['s'],left_mm=left/K,right_mm=(left+width)/K))
   c.drawString(left,y,a['s'])
  else:
   c.setStrokeColor(color(a['color']));c.setLineWidth(a['lw']*K)
   c.setDash([1.5*K,K] if a.get('dash') else [])
   fill=a.get('fill','none')!='none'
   if fill:c.setFillColor(color(a['fill']))
   if k=='line':c.line(a['x1']*K,(420-a['y1'])*K,a['x2']*K,(420-a['y2'])*K)
   elif k=='rect':c.rect(a['x']*K,(420-a['y']-a['h'])*K,a['w']*K,a['h']*K,stroke=1,fill=int(fill))
   elif k=='circle':c.circle(a['x']*K,(420-a['y'])*K,a['r']*K,stroke=1,fill=int(fill))
  c.restoreState()
 c.showPage()
c.save();assert not out_of_bounds,out_of_bounds
r=PdfReader(path);assert len(r.pages)==4
texts=[p.extract_text() for p in r.pages]
for expected,txt in zip(['A401','A402','A403','A405'],texts):assert expected in txt
assert '66.95' in texts[0] and '77.70' in texts[0] and '960' in texts[0]
report=dict(pages=4,page_size_mm=[594,420],page_codes=['A401','A402','A403','A405'],embedded_font='Windows SimSun TTC subset',text_bounds_failures=out_of_bounds,content_checks=True)
(QA/'pdf_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
