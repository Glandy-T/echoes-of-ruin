from pathlib import Path
import argparse,base64,json,sys
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/"docs/art/experiments/pixellab_direct_api_check_v1/source"))
from pixellab_direct import credential,request
def image(p):
    w,h=Image.open(p).size
    return {"image":{"base64":"data:image/png;base64,"+base64.b64encode(p.read_bytes()).decode()},"size":{"width":w,"height":h}}
def find(v):
    if isinstance(v,dict):
        if isinstance(v.get("base64"),str):return v["base64"]
        for c in v.values():
            x=find(c)
            if x:return x
    if isinstance(v,list):
        for c in v:
            x=find(c)
            if x:return x
def main():
    p=argparse.ArgumentParser();p.add_argument("action",choices=("submit","poll"));p.add_argument("variant",choices=("portal","lamp_a","lamp_b"));a=p.parse_args()
    token=credential(True);f=HERE/f"job_{a.variant}.json"
    if a.action=="submit":
        if f.exists():raise RuntimeError("Already submitted; use poll")
        kind="portal" if a.variant=="portal" else "lamp"
        prompt=(HERE/f"prompt_{kind}.txt").read_text(encoding="utf-8")
        r=request("POST","/inpaint-v3",token,{"description":prompt,"inpainting_image":image(HERE/f"guide_{kind}.png"),"mask_image":image(HERE/f"mask_{kind}.png"),"seed":2026102961+["portal","lamp_a","lamp_b"].index(a.variant),"crop_to_mask":False,"no_background":False})
        safe={k:r.get(k) for k in ("background_job_id","status","usage")};assert safe["background_job_id"]
        f.write_text(json.dumps(safe,indent=2),encoding="utf-8");print(a.variant,json.dumps(safe));return
    j=json.loads(f.read_text());r=request("GET","/background-jobs/"+j["background_job_id"],token);print(a.variant,r.get("status"))
    if r.get("status")!="completed":return
    encoded=find(r.get("last_response"));assert encoded
    out=HERE.parent/"raw"/f"{a.variant}.png";out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(base64.b64decode(encoded.split(",")[-1],validate=True))
    safe={"variant":a.variant,"endpoint":"/inpaint-v3","background_job_id":j["background_job_id"],"status":"completed","usage":r.get("usage")}
    (HERE.parent/f"result_{a.variant}.json").write_text(json.dumps(safe,indent=2),encoding="utf-8");print(json.dumps(safe))
if __name__=="__main__":main()
