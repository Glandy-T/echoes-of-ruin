"""PixelLab text generation for the material itself; safe job metadata only."""
from pathlib import Path
import sys,json,base64
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from job import find,credential,request
prompt='''Seamless flat top-down albedo pixel texture for continuous worn matte blue-gray mineral composite flooring inside an abandoned advanced cryogenic facility. The entire square is the material, not a picture of a room. Interlocking cloudy low-contrast worn coating fields, fine coherent pixel clusters and mineral pigment variation distributed throughout, with tiny fragmented edges. Large subtle material patches about 40-90 pixels wide, secondary finer 2-5 pixel clusters. One uniform cold blue-gray floor with modest visible decades of material age. No tile seams, grid, routes, text, furniture, separate objects, big isolated dirt blobs, long scratches, perspective, rendered lights, shadows, glossy reflections or outlines. Seamless continuation on all edges. Use the supplied cool palette, primarily middle tones, with restrained lighter and darker fields. Crisp native pixel art, no blur or smooth airbrushed gradients.'''
(HERE/'prompt_base3.txt').write_text(prompt,encoding='utf-8')
palette=['#4D626B','#526771','#566B74','#5A6C73','#5E727B','#627780','#687D85','#70858D']
payload={'description':prompt,'image_size':{'width':256,'height':256},'seed':2026102991,'no_background':False,'target_palette':{'colors':palette,'max_colors':8}}
(HERE/'request_base3.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
token=credential(True);jobfile=HERE/'job_base3.json'
if sys.argv[1]=='submit':
    assert not jobfile.exists(),'Existing submission; poll it instead.'
    r=request('POST','/generate-image-v2',token,payload)
    safe={k:r.get(k) for k in ['background_job_id','status','usage']};assert safe['background_job_id']
    jobfile.write_text(json.dumps(safe,indent=2),encoding='utf-8');print(json.dumps(safe))
else:
    j=json.loads(jobfile.read_text());r=request('GET','/background-jobs/'+j['background_job_id'],token);print(r.get('status'))
    if r.get('status')=='completed':
        encoded=find(r.get('last_response'));assert encoded
        (HERE.parent/'raw/base3.png').write_bytes(base64.b64decode(encoded.split(',')[-1],validate=True))
        safe={'variant':'base3','endpoint':'/generate-image-v2','background_job_id':j['background_job_id'],'status':'completed','usage':r.get('usage')}
        (HERE.parent/'result_base3.json').write_text(json.dumps(safe,indent=2),encoding='utf-8');print(json.dumps(safe))
