"""Explicit deliverables only; verified byte hashes and archive contents."""
from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parent
files=['.gitattributes', 'README.md', 'FREEZE_STATUS.json', 'layout.py', 'drawings.py', 'build_freecad.py', 'export_pdf.py', 'finish_in_freecad.FCMacro', 'verify_saved.py', 'package_artifacts.py', 'reopen_in_freecad.FCMacro', 'mark_freeze.FCMacro', 'standard_floor_v3_trim.FCStd', 'floor_layout.json', 'floor_validation.json', 'sources/STANDARD_FLOOR_ENGINEERING_BRIEF.snapshot.md', 'sources/before_cleanup_layout.snapshot.json', 'sources/room1_v2_parameters.snapshot.json', 'sources/standard_floor_v2_validation.snapshot.json', 'exports/A2_blank.svg', 'exports/A2_live.svg', 'exports/A401_v3_trim.svg', 'exports/A402_v3_trim.svg', 'exports/A403_v3_trim.svg', 'exports/A405_v3_trim.svg', 'exports/drawing_data.json', 'exports/standard_floor_v3_trim.pdf', 'exports/A404_native_live.pdf', 'qa/gui_validation.json', 'qa/reopen_gui_validation.json', 'qa/pdf_validation.json', 'qa/final_validation.json', 'qa/cleanup_validation.json', 'qa/sheet-1.png', 'qa/sheet-2.png', 'qa/sheet-3.png', 'qa/sheet-4.png', 'qa/native-A404-1.png']
revision='standard_floor_v3_trim'
manifest_name='artifact_manifest.json'
freeze=json.loads((ROOT/'FREEZE_STATUS.json').read_text(encoding='utf-8'));assert 'error' not in freeze
assert freeze['stage']=='STANDARD FLOOR SPATIAL BLOCKOUT ACCEPTED / FROZEN FOR NEXT BUILDING STAGE'
entries=[]
for n in files:
 b=(ROOT/n).read_bytes();entries.append(dict(path=n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
m=dict(revision=revision,source_commit='8dbcec552f6a058145508c8e0bf701063067449f',stage=freeze['stage'],files=entries)
(ROOT/manifest_name).write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
with zipfile.ZipFile(ROOT/(revision+'_delivery.zip'),'w',zipfile.ZIP_DEFLATED) as z:
 for n in files+[manifest_name]:z.write(ROOT/n,revision+'/'+n)
print(json.dumps(dict(files=len(files),cad_sha256=next(e['sha256'] for e in entries if e['path'].endswith('FCStd')),zip_bytes=(ROOT/(revision+'_delivery.zip')).stat().st_size)))
