"""Render the FreeCAD-recorded paper primitives for the single-story v2 review.

This exports a parameter snapshot. Copy to a new revision and synchronize the
builder before rebuilding an edited CAD document.
"""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / 'cad_validation.json').read_text(encoding='utf-8'))
pdfmetrics.registerFont(TTFont('CN', r'C:\Windows\Fonts\simsun.ttc', subfontIndex=0))
target = ROOT / 'exports/admin_facility_plans_v2.pdf'
pdf = canvas.Canvas(str(target), pagesize=(594 * mm, 420 * mm), pageCompression=1)
pdf.setTitle('管理设施单层方案 / 空间验证工程图 v2')
pdf.setAuthor('Echoes of Ruin / FreeCAD spatial verification')
issues = []
for page in data['pages']:
    for item in page['items']:
        kind = item['k']
        pdf.setStrokeColorRGB(.07, .07, .07)
        pdf.setFillColorRGB(.07, .07, .07)
        if kind == 'text':
            pdf.setFont('CN', item['size'] * mm)
            anchor = item['anchor']
            width = pdfmetrics.stringWidth(item['s'], 'CN', item['size'] * mm) / mm
            xmin = item['x'] - (width / 2 if anchor == 'middle' else width if anchor == 'end' else 0)
            xmax = xmin + width
            if xmin < 12 or xmax > 582:
                issues.append({'page': page['code'], 'text': item['s'], 'xmin': xmin, 'xmax': xmax})
            draw = {'middle': pdf.drawCentredString, 'end': pdf.drawRightString}.get(anchor, pdf.drawString)
            draw(item['x'] * mm, (420 - item['y']) * mm, item['s'])
        else:
            pdf.setLineWidth(item['lw'] * mm)
            pdf.setDash([2 * mm, 1.2 * mm] if item.get('dash') else [])
            if kind == 'line':
                pdf.line(item['x1'] * mm, (420 - item['y1']) * mm,
                         item['x2'] * mm, (420 - item['y2']) * mm)
            elif kind == 'rect':
                pdf.rect(item['x'] * mm, (420 - item['y'] - item['h']) * mm,
                         item['w'] * mm, item['h'] * mm, fill=0, stroke=1)
    pdf.showPage()
pdf.save()
assert not issues, issues
reader = PdfReader(str(target))
assert len(reader.pages) == 3
for page, expected in zip(reader.pages, ['A201', 'A202', 'A203']):
    content = page.extract_text()
    assert expected in content and 'TBD' in content
    assert abs(float(page.mediabox.width) / mm - 594) < .01
    assert abs(float(page.mediabox.height) / mm - 420) < .01
print(json.dumps({'pdf': str(target), 'pages': len(reader.pages),
                  'page_size_mm': [594, 420], 'text_bounds': 'passed',
                  'page_readback': 'passed'}, ensure_ascii=False))
