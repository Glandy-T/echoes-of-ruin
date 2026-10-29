from pathlib import Path
import argparse,base64,json,sys
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/"docs/art/experiments/pixellab_direct_api_check_v1/source"))
from pixellab_direct import credential,request
def encoded(path):
    w,h=Image.open(path).size
    return {"image":{"base64":"data:image/png;base64,"+base64.b64encode(path.read_bytes()).decode()},"size":{"width":w,"height":h}}
def find(v):
    if isinstance(v,dict):
        if isinstance(v.get("base64"),str):return v["base64"]
        for child in v.values():
            x=find(child)
            if x:return x
    if isinstance(v,list):
        for child in v:
            x=find(child)
            if x:return x
def main():
    p=argparse.ArgumentParser();p.add_argument("action",choices=("submit","poll"));p.add_argument("variant",choices=("e","f","g","h","e2"));a=p.parse_args()
    f=HERE/f"job_{a.variant}.json";token=credential(True)
    if a.action=="submit":
        if f.exists():raise RuntimeError("Already submitted; no duplicate POST")
        prompt=(HERE/"prompt.txt").read_text(encoding="utf-8")
        additions={"e":" Vary left and right panel edge dust silhouettes; slightly calmer upper edge and uneven lower accumulation, keeping medium overall density.","f":" Make the two panel edge patterns asymmetric, with local clusters concentrated at different heights on the two seam shoulders. Keep centers quiet.","g":" Use a balanced but irregular top and bottom accumulation, with different fine stepped silhouettes on the two panels. No bilateral symmetry.","h":" Let some edge sections remain cleaner and other short sections gather medium fine dust clusters; varied lower contact, no repeated identical motifs."}
        if a.variant=="e2":
            prompt+=" Keep ALL material intact: no peeling, no coating loss, no large chips or polygon-shaped damage. Only fine dust and seal-contact pixels. Vary local accumulation heights while keeping moderate density and smooth ceramic centers."
        else:prompt+=additions[a.variant]
        payload={"description":prompt,"inpainting_image":encoded(HERE/"guide.png"),"mask_image":encoded(HERE/"mask.png"),"seed":2026102941+["e","f","g","h","e2"].index(a.variant),"no_background":False,"crop_to_mask":False}
        r=request("POST","/inpaint-v3",token,payload);safe={k:r.get(k) for k in ("background_job_id","status","usage")}
        assert safe["background_job_id"];f.write_text(json.dumps(safe,indent=2),encoding="utf-8");print(a.variant,json.dumps(safe));return
    job=json.loads(f.read_text());r=request("GET","/background-jobs/"+job["background_job_id"],token)
    print(a.variant,r.get("status"))
    if r.get("status")!="completed":return
    raw=find(r.get("last_response"));assert raw
    out=HERE.parent/"raw"/f"wall_{a.variant}.png";out.parent.mkdir(parents=True,exist_ok=True)
    out.write_bytes(base64.b64decode(raw.split(",")[-1],validate=True))
    safe={"variant":a.variant,"endpoint":"/inpaint-v3","background_job_id":job["background_job_id"],"status":"completed","usage":r.get("usage")}
    (HERE.parent/f"result_{a.variant}.json").write_text(json.dumps(safe,indent=2),encoding="utf-8");print(json.dumps(safe))
if __name__=="__main__":main()
