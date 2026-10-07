from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parent
files=['.gitattributes','README.md','build_blockout.py','render_blockout.FCMacro','validate_blockout.py','make_gallery.py','package_blockout.py','cameras.json','standard_floor_blockout_v3.FCStd','blockout_validation.json','VIEW_GALLERY.html','VIEW_CONTACT_SHEET.png','sources/accepted_inset_layout.snapshot.json','sources/STANDARD_FLOOR_ENGINEERING_BRIEF.snapshot.md','qa/render_validation.json','qa/image_validation.json']
files+=['views/'+v['name']+'.png' for v in json.loads((ROOT/'cameras.json').read_text(encoding='utf-8'))]
entries=[]
for n in files:
 b=(ROOT/n).read_bytes();entries.append(dict(path=n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
m=dict(revision='standard_floor_blockout_v3',source_commit='16898b0561e0ac3a96697ff501a4ba26380221ec',scope='Single-floor spatial blockout; accepted plan frozen except fully inset N/S stairs',files=entries)
(ROOT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
with zipfile.ZipFile(ROOT/'standard_floor_blockout_v3_delivery.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in files+['manifest.json']:z.write(ROOT/n,'standard_floor_blockout_v3/'+n)
print(json.dumps(dict(files=len(files),cad_sha256=next(e['sha256'] for e in entries if e['path'].endswith('FCStd')),zip_bytes=(ROOT/'standard_floor_blockout_v3_delivery.zip').stat().st_size)))
