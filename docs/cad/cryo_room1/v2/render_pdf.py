"""Publication PDF directly from shared metre-to-paper primitives."""
from pathlib import Path
import json,sys
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parent
pdfmetrics.registerFont(TTFont('CN',r'C:\Windows\Fonts\simsun.ttc',subfontIndex=0))
data=json.loads((ROOT/'cad_validation.json').read_text(encoding='utf-8'))
target=ROOT/'exports/room1_engineering_v2.pdf'
pdf=canvas.Canvas(str(target),pagesize=(594*mm,420*mm),pageCompression=1)
pdf.setTitle('Room 1 单室工程验证 v2');pdf.setAuthor('Echoes of Ruin / FreeCAD 1.1.4')
def color(s):return HexColor(s if len(s)!=4 else '#'+''.join(ch*2 for ch in s[1:]))
issues=[]
for page in data['pages']:
 for a in page['items']:
  k=a['k'];pdf.setStrokeColor(color(a['color']));pdf.setFillColor(color(a['color']))
  if k=='text':
   pdf.setFont('CN',a['size']*mm);w=pdfmetrics.stringWidth(a['s'],'CN',a['size']*mm)/mm
   xmin=a['x']-(w/2 if a['anchor']=='middle' else w if a['anchor']=='end' else 0)
   if xmin<12 or xmin+w>582 or a['y']<12 or a['y']>408:issues.append(dict(page=page['code'],text=a['s'],xmin=xmin,xmax=xmin+w))
   draw={'middle':pdf.drawCentredString,'end':pdf.drawRightString}.get(a['anchor'],pdf.drawString);draw(a['x']*mm,(420-a['y'])*mm,a['s']);continue
  pdf.setLineWidth(a['lw']*mm);pdf.setDash([1.5*mm,mm] if a.get('dash') else [])
  fill=a.get('fill','none');filled=fill!='none'
  if filled:pdf.setFillColor(color(fill))
  if k=='line':pdf.line(a['x1']*mm,(420-a['y1'])*mm,a['x2']*mm,(420-a['y2'])*mm)
  elif k=='rect':pdf.rect(a['x']*mm,(420-a['y']-a['h'])*mm,a['w']*mm,a['h']*mm,stroke=1,fill=int(filled))
  elif k=='circle':pdf.circle(a['x']*mm,(420-a['y'])*mm,a['r']*mm,stroke=1,fill=int(filled))
  elif k=='poly':
   path=pdf.beginPath();path.moveTo(a['pts'][0][0]*mm,(420-a['pts'][0][1])*mm)
   for x,y in a['pts'][1:]:path.lineTo(x*mm,(420-y)*mm)
   path.close();pdf.drawPath(path,stroke=1,fill=int(filled))
 pdf.showPage()
pdf.save();assert not issues,issues
r=PdfReader(str(target));assert len(r.pages)==3
for page,code in zip(r.pages,['A301','A302','A303']):
 assert code in page.extract_text()
 assert abs(float(page.mediabox.width)/mm-594)<.01 and abs(float(page.mediabox.height)/mm-420)<.01
(ROOT/'qa/pdf_validation.json').write_text(json.dumps(dict(pages=3,A2_size_passed=True,text_bounds_passed=True,text_readback_passed=True),indent=2),encoding='utf-8')
print(str(target))
