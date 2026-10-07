"""Explicit deliverables only; verified byte hashes and archive contents."""
from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parent
files=['.gitattributes', 'README.md', 'FREEZE_STATUS.json', 'layout.py', 'build_blockout.py', 'render_blockout.FCMacro', 'validate_blockout.py', 'check_cleanup.py', 'make_gallery.py', 'package_blockout.py', 'cameras.json', 'standard_floor_blockout_v3_frozen.FCStd', 'blockout_validation.json', 'VIEW_GALLERY.html', 'VIEW_CONTACT_SHEET.png', 'sources/accepted_inset_layout.snapshot.json', 'sources/STANDARD_FLOOR_ENGINEERING_BRIEF.snapshot.md', 'qa/render_validation.json', 'qa/image_validation.json', 'qa/cleanup_validation.json', 'sources/before_cleanup_layout.snapshot.json', 'sources/before_cleanup_validation.snapshot.json', 'sources/accepted_frozen_validation.snapshot.json']
revision='standard_floor_blockout_v3_frozen'
manifest_name='manifest.json'
files+=['views/'+v['name']+'.png' for v in json.loads((ROOT/'cameras.json').read_text(encoding='utf-8'))]
freeze=json.loads((ROOT/'FREEZE_STATUS.json').read_text(encoding='utf-8'));assert 'error' not in freeze
assert freeze['stage']=='STANDARD FLOOR SPATIAL BLOCKOUT ACCEPTED / FROZEN FOR NEXT BUILDING STAGE'
entries=[]
for n in files:
 b=(ROOT/n).read_bytes();entries.append(dict(path=n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
m=dict(revision=revision,source_commit='b53aa9b8e38c7c423703dd946c2ba88d44b9ab37',stage=freeze['stage'],files=entries)
(ROOT/manifest_name).write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
with zipfile.ZipFile(ROOT/(revision+'_delivery.zip'),'w',zipfile.ZIP_DEFLATED) as z:
 for n in files+[manifest_name]:z.write(ROOT/n,revision+'/'+n)
print(json.dumps(dict(files=len(files),cad_sha256=next(e['sha256'] for e in entries if e['path'].endswith('FCStd')),zip_bytes=(ROOT/(revision+'_delivery.zip')).stat().st_size)))
