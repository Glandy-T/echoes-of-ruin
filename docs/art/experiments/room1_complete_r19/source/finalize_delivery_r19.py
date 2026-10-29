"""Record strict upload-checkout acceptance and final, unmodified capture hashes."""
from pathlib import Path
import hashlib
import json
import re

here=Path(__file__).resolve().parent
base=here.parent
repo=here.parents[4]
steps={}
for name in ['import','runtime','formal_title','existing_title','formal_capture']:
    text=(here/f'upload_{name}.log').read_text(encoding='utf-8',errors='replace')
    errors=re.findall(r'(?:SCRIPT ERROR:|ERROR:)[^\n]*',text)
    assert not errors,(name,errors[:5])
    steps[name]={'result':'PASS','error_count':0,
                 'evidence_lines':[line.strip() for line in text.splitlines()
                                   if any(token in line for token in ['PASS','R19_COMPLETE_RUNTIME','R19_FORMAL_'])]}
runtime=json.loads((here/'runtime_validation.json').read_text(encoding='utf-8'))
assert runtime['result']=='PASS' and not runtime['errors']
portable=json.loads((here/'upload_portability.json').read_text(encoding='utf-8'))
assert not portable['missing'] and not portable['absolute']
numbered=json.loads((here/'numbering_validation.json').read_text(encoding='utf-8'))
audit=json.loads((here/'independent_bake_audit.json').read_text(encoding='utf-8'))
assert not audit['failures']
shots={str(p.relative_to(base)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
       for p in sorted((base/'evidence').rglob('*.png'))
       if not p.name.startswith('quality_')}
for name in ['从这里开始.md','docs/art/素材目录.md','docs/art/ROOM1_NEXT_SCHOOL_HANDOFF.md']:
    p=repo/name
    p.write_text(p.read_text(encoding='utf-8').rstrip()+'\n',encoding='utf-8',newline='\n')
title=json.loads((here/'title_flow.json').read_text(encoding='utf-8'))
title.pop('validation_logs',None)
title['validation_status']='PASS: final assets in independent upload checkout'
title['validation_evidence']='validation_results.json; temporary console logs deliberately excluded'
(here/'title_flow.json').write_text(json.dumps(title,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
result={'result':'PASS','date':'2026-10-30','scope':'final r19 in managed upload checkout; not school-machine acceptance',
        'steps':steps,'runtime_checks':len(runtime['checks']),'physical_walks':len(runtime['physical_walks']),
        'blend_portability':portable,'independent_asset_failures':audit['failures'],
        'capture_sha256':shots,'pixel_art_generation':'none: approved PixelLab images reused; functional labels only'}
(here/'validation_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'R19_FINAL_DELIVERY_PASS checks={len(runtime["checks"])} walks={len(runtime["physical_walks"])} captures={len(shots)}')
