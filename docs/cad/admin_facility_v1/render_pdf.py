"""Render the exact paper primitives recorded by the installed FreeCAD build."""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'cad_validation.json').read_text(encoding='utf-8'))
pdfmetrics.registerFont(TTFont('CN',r'C:\Windows\Fonts\simsun.ttc',subfontIndex=0))
file=ROOT/'exports/admin_facility_plans_v1.pdf'
c=canvas.Canvas(str(file),pagesize=(594*mm,420*mm),pageCompression=1)
c.setTitle('管理设施 1F/2F 空间验证工程图 v1')
c.setAuthor('Echoes of Ruin / FreeCAD spatial validation')
issues=[]
for page in data['pages']:
    for it in page['items']:
        k=it['k']
        c.setStrokeColorRGB(.07,.07,.07)
        c.setFillColorRGB(.07,.07,.07)
        if k=='text':
            c.setFont('CN',it['size']*mm)
            y=(420-it['y'])*mm
            x=it['x']*mm
            width=pdfmetrics.stringWidth(it['s'],'CN',it['size']*mm)/mm
            anchor=it['anchor']
            xmin=it['x']-(width/2 if anchor=='middle' else width if anchor=='end' else 0)
            xmax=xmin+width
            if xmin<12 or xmax>582:issues.append({'page':page['code'],'text':it['s'],'xmin':xmin,'xmax':xmax})
            {'middle':c.drawCentredString,'end':c.drawRightString}.get(anchor,c.drawString)(x,y,it['s'])
        else:
            c.setLineWidth(it['lw']*mm)
            c.setDash([2*mm,1.2*mm] if it.get('dash') else [])
            if k=='line':c.line(it['x1']*mm,(420-it['y1'])*mm,it['x2']*mm,(420-it['y2'])*mm)
            elif k=='rect':c.rect(it['x']*mm,(420-it['y']-it['h'])*mm,it['w']*mm,it['h']*mm,fill=0,stroke=1)
    c.showPage()
c.save()
reader=PdfReader(str(file))
assert len(reader.pages)==4
for page,expected in zip(reader.pages,['A101','A102','A103','A104']):
    txt=page.extract_text()
    assert expected in txt
    assert 'TBD' in txt
assert not issues, issues
print(json.dumps({'pdf':str(file),'pages':len(reader.pages),'page_size_mm':[594,420],'text_bounds':'passed','page_readback':'passed'},ensure_ascii=False))
