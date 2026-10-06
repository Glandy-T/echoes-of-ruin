"""Render measured A201–A203 snapshots using the builder's paper primitives."""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'cad_validation.json').read_text(encoding='utf-8'))
pdfmetrics.registerFont(TTFont('CN',r'C:\Windows\Fonts\simsun.ttc',subfontIndex=0))
target=ROOT/'exports/admin_facility_plans_v2.pdf'
def color(value):
    if len(value)==4 and value.startswith('#'):value='#'+''.join(ch*2 for ch in value[1:])
    return HexColor(value)
pdf=canvas.Canvas(str(target),pagesize=(594*mm,420*mm),pageCompression=1)
pdf.setTitle('管理设施单层建筑方案平面图 v2-R2');pdf.setAuthor('Echoes of Ruin / FreeCAD');issues=[]
for page in data['pages']:
    for a in page['items']:
        k=a['k'];pdf.setStrokeColor(color(a.get('color','#111')));pdf.setFillColor(color(a.get('color','#111')))
        if k=='text':
            pdf.setFont('CN',a['size']*mm);w=pdfmetrics.stringWidth(a['s'],'CN',a['size']*mm)/mm
            xmin=a['x']-(w/2 if a['anchor']=='middle' else w if a['anchor']=='end' else 0)
            if xmin<12 or xmin+w>582:issues.append(dict(page=page['code'],text=a['s'],xmin=xmin,xmax=xmin+w))
            draw={'middle':pdf.drawCentredString,'end':pdf.drawRightString}.get(a['anchor'],pdf.drawString);draw(a['x']*mm,(420-a['y'])*mm,a['s']);continue
        pdf.setLineWidth(a['lw']*mm);pdf.setDash([1.5*mm,mm] if a.get('dash') else [])
        fill=a.get('fill','none');filled=fill!='none'
        if filled:pdf.setFillColor(color(fill))
        if k=='line':pdf.line(a['x1']*mm,(420-a['y1'])*mm,a['x2']*mm,(420-a['y2'])*mm)
        elif k=='rect':pdf.rect(a['x']*mm,(420-a['y']-a['h'])*mm,a['w']*mm,a['h']*mm,stroke=1,fill=int(filled))
        elif k=='circle':pdf.circle(a['x']*mm,(420-a['y'])*mm,a['r']*mm,stroke=1,fill=int(filled))
        elif k=='arc':
            x,y,r=a['x']*mm,(420-a['y'])*mm,a['r']*mm;pdf.arc(x-r,y-r,x+r,y+r,startAng=a['angle'],extent=90)
    pdf.showPage()
pdf.save();assert not issues,issues
r=PdfReader(str(target));assert len(r.pages)==3
for p,code in zip(r.pages,['A201','A202','A203']):
    content=p.extract_text();assert code in content and ('P' in content or 'TBD' in content)
    assert abs(float(p.mediabox.width)/mm-594)<.01 and abs(float(p.mediabox.height)/mm-420)<.01
print(json.dumps(dict(pdf=str(target),revision='v2-R2',pages=3,page_size_mm=[594,420],text_bounds='passed',page_readback='passed'),ensure_ascii=False))
