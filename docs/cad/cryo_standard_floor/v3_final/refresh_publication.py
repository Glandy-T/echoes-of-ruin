from pathlib import Path
import json
from drawings import make_pages,to_svg
ROOT=Path(__file__).resolve().parent
pages=make_pages(json.loads((ROOT/'floor_layout.json').read_text(encoding='utf-8')),json.loads((ROOT/'floor_validation.json').read_text(encoding='utf-8')))
(ROOT/'exports/drawing_data.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
for p in pages:(ROOT/'exports'/(p['code']+'_v3_final.svg')).write_text(to_svg(p),encoding='utf-8')
