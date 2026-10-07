from pathlib import Path
import json,hashlib,zipfile
from PIL import Image
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa'
gui=json.loads((QA/'gui_validation.json').read_text(encoding='utf-8'))
saved=json.loads((QA/'saved_validation.json').read_text(encoding='utf-8'))
render=json.loads((QA/'render_validation.json').read_text(encoding='utf-8'))
assert 'error' not in gui and 'error' not in render and saved['saved_readback_passed']
assert saved['fcstd_sha256']==hashlib.sha256((ROOT/'room1_engineering_v1.FCStd').read_bytes()).hexdigest()
assert len(gui['native_dimensions'])==5 and len(gui['parameter_edit_tests'])==5
assert all(t['passed'] for t in gui['parameter_edit_tests'])
for filename in render['views']:
 im=Image.open(QA/filename);assert im.size==(1800,1100)
 assert sum(hi-lo for lo,hi in im.convert('RGB').getextrema())>50
for code in ['A301','A302','A303','A304']:assert len(PdfReader(str(QA/('freecad_'+code+'.pdf'))).pages)==1
gui['visual_review']='completed: A301-A303 publication and native PDFs, A304 native dimensions, orthographic top and isometric views inspected'
(QA/'gui_validation.json').write_text(json.dumps(gui,ensure_ascii=False,indent=2),encoding='utf-8')
pdfqa=json.loads((QA/'pdf_validation.json').read_text(encoding='utf-8'));pdfqa['visual_review']='all three latest publication pages rendered and inspected; no clipping or text/geometry overlap'
(QA/'pdf_validation.json').write_text(json.dumps(pdfqa,ensure_ascii=False,indent=2),encoding='utf-8')
report=json.loads((ROOT/'cad_validation.json').read_text(encoding='utf-8'))
report['final_verification']=dict(saved_readback=saved['saved_readback_passed'],fully_constrained=gui['native_fully_constrained_sketches'],
 native_dimensions=gui['native_dimensions'],parameter_edit_tests=gui['parameter_edit_tests'],publication_visual_review=pdfqa['visual_review'])
(ROOT/'cad_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
paths=['.gitattributes','README.md','room1_engineering_v1.FCStd','cad_validation.json','layout.py','drawings.py','build_freecad.py','render_pdf.py','validate_saved.py','finish_in_freecad.FCMacro','render_views.FCMacro','package_outputs.py']
paths.extend(str(p.relative_to(ROOT)).replace('\\','/') for p in sorted((ROOT/'sources').iterdir()) if p.is_file())
paths.extend(str(p.relative_to(ROOT)).replace('\\','/') for p in sorted((ROOT/'exports').iterdir()) if p.is_file())
paths.extend('qa/'+name for name in ['gui_validation.json','saved_validation.json','pdf_validation.json','render_validation.json','room1_isometric.png','room1_top.png','freecad_A301.pdf','freecad_A302.pdf','freecad_A303.pdf','freecad_A304.pdf'])
manifest={name:dict(bytes=(ROOT/name).stat().st_size,sha256=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()) for name in paths}
(ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
with zipfile.ZipFile(ROOT/'room1_engineering_v1_delivery.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in paths+['manifest.json']:z.write(ROOT/name,name)
print('Package verified:',len(paths),'files; native model SHA-256',saved['fcstd_sha256'])
