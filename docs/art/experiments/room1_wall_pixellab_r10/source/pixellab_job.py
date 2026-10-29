"""Official PixelLab edit; no credential persistence and no duplicate POST."""
from pathlib import Path
import argparse, base64, json, sys
from PIL import Image
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "docs/art/experiments/pixellab_direct_api_check_v1/source"))
from pixellab_direct import credential, request

def image(path):
    w,h = Image.open(path).size
    return {"image":{"base64":"data:image/png;base64,"+base64.b64encode(path.read_bytes()).decode()}, "size":{"width":w,"height":h}}

def find(value):
    if isinstance(value,dict):
        if isinstance(value.get("base64"),str): return value["base64"]
        for v in value.values():
            found=find(v)
            if found: return found
    if isinstance(value,list):
        for v in value:
            found=find(v)
            if found: return found

def main():
    p=argparse.ArgumentParser();p.add_argument("action",choices=("submit","poll"));a=p.parse_args()
    token=credential(True)
    jobfile=HERE/"submission.json"
    if a.action=="submit":
        if jobfile.exists(): raise RuntimeError("Job already submitted; use poll")
        payload={"description":(HERE/"prompt.txt").read_text(encoding="utf-8"),"inpainting_image":image(HERE/"guide.png"),"mask_image":image(HERE/"mask.png"),"no_background":False,"crop_to_mask":False}
        r=request("POST","/inpaint-v3",token,payload)
        safe={k:r.get(k) for k in ("background_job_id","status","usage")}
        assert safe["background_job_id"]
        jobfile.write_text(json.dumps(safe,indent=2),encoding="utf-8");print(json.dumps(safe));return
    job=json.loads(jobfile.read_text(encoding="utf-8"))
    r=request("GET","/background-jobs/"+job["background_job_id"],token)
    print("PIXELLAB",r.get("status"))
    if r.get("status")!="completed": return
    encoded=find(r.get("last_response"))
    if not encoded: raise RuntimeError("Completed response has no inline image")
    out=HERE.parent/"raw/pixellab_wall.png";out.parent.mkdir(parents=True,exist_ok=True)
    out.write_bytes(base64.b64decode(encoded.split(",")[-1],validate=True))
    safe={"endpoint":"/inpaint-v3","background_job_id":job["background_job_id"],"status":"completed","usage":r.get("usage"),"image_file":out.name}
    (HERE.parent/"result.json").write_text(json.dumps(safe,indent=2),encoding="utf-8");print(json.dumps(safe))

if __name__=="__main__": main()
