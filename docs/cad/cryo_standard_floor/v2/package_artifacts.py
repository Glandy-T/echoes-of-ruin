"""Explicit deliverable list, preserving bytes and excluding logs/configs/backups."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent
files=['.gitattributes','README.md','layout.py','drawings.py','build_freecad.py','export_pdf.py','finish_in_freecad.FCMacro','refresh_native_dimensions.FCMacro','verify_saved.py','package_artifacts.py','standard_floor_v2.FCStd','floor_layout.json','floor_validation.json',
 'sources/STANDARD_FLOOR_ENGINEERING_BRIEF.snapshot.md','sources/room1_v2_parameters.snapshot.json','sources/standard_floor_v1_validation.snapshot.json',
 'exports/A2_blank.svg','exports/A2_live.svg','exports/A401_v2.svg','exports/A402_v2.svg','exports/A403_v2.svg','exports/drawing_data.json','exports/standard_floor_v2.pdf','exports/A404_native_live.pdf',
 'qa/gui_validation.json','qa/reopen_gui_validation.json','qa/pdf_validation.json','qa/final_validation.json','qa/sheet-1.png','qa/sheet-2.png','qa/sheet-3.png','qa/native-A404-1.png']
entries=[]
for n in files:
 p=ROOT/n;assert p.is_file(),n;b=p.read_bytes();entries.append(dict(path=n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
manifest=dict(revision='standard_floor_v2',source_commit='c549e7e3cd1328ea1fee249e5d750827d764d823',stage='2D_TOPOLOGY_VERIFIED / EVACUATION_DESIGN_OPEN',files=entries)
(ROOT/'artifact_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
with zipfile.ZipFile(ROOT/'standard_floor_v2_delivery.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in files+['artifact_manifest.json']:z.write(ROOT/n,'standard_floor_v2/'+n)
print(json.dumps(dict(files=len(files),fcstd_sha256=next(e['sha256'] for e in entries if e['path'].endswith('FCStd')),zip_bytes=(ROOT/'standard_floor_v2_delivery.zip').stat().st_size)))
