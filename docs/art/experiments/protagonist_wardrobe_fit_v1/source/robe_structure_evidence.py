"""Read-only fit evidence for the raw robe v2 and body v2 assets.

Run with Blender 5 in background mode.  This script never saves a .blend or
modifies source meshes; it writes only the sibling JSON evidence file.
"""
from pathlib import Path
from collections import Counter
import hashlib, json
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]  # docs/art/experiments
ROBE = ROOT / "protagonist_tripo_robe_v2/model/protagonist_tripo_robe_v2_raw.glb"
BODY = ROOT / "protagonist_tripo_body_v2/model/protagonist_body_v2.blend"
PROBE = ROOT / "protagonist_tripo_body_v2/model/body_v2_motion_probe.blend"
QA = ROOT / "protagonist_tripo_robe_v2/source/robe_topology_check.json"
OUT = Path(__file__).with_suffix(".json")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def v3(v): return [round(float(x), 7) for x in v]

def bounds(points):
    return {"min": v3([min(p[i] for p in points) for i in range(3)]),
            "max": v3([max(p[i] for p in points) for i in range(3)])}

def all_mesh_world():
    result=[]
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH": continue
        pts=[ob.matrix_world @ x.co for x in ob.data.vertices]
        if pts:
            result.append((ob, pts))
    return result

def mesh_summary(label):
    rows=[]
    for ob, pts in all_mesh_world():
        rows.append({"object":ob.name, "vertices":len(pts), "polygons":len(ob.data.polygons),
                     "bounds":bounds(pts), "location":v3(ob.matrix_world.translation)})
    return {"label":label, "meshes":rows}

def z_band(pts, lo, hi):
    q=[p for p in pts if lo <= p.z <= hi]
    return {"z_range":[lo,hi], "vertices":len(q), "bounds":bounds(q) if q else None}

def robe_landmarks(ob, pts):
    # Axis convention is project-established: upright +Z, forward +X.
    bb=bounds(pts); z0,z1=bb["min"][2],bb["max"][2]
    # Bands capture measurable placement, not semantic topology selection.
    levels={
        "neck_top":(z1-.025,z1), "shoulder":(.775,.835),
        "elbow":(.635,.725), "cuff":(.44,.58), "hem":(z0,z0+.04),
    }
    out={k:z_band(pts,*r) for k,r in levels.items()}
    for side, sign in (("negative_y",-1),("positive_y",1)):
        q=[p for p in pts if (p.y*sign) > .24]
        out["sleeve_"+side]={"vertices":len(q), "bounds":bounds(q) if q else None}
    return out

def crossings_by_region(qa):
    rows=qa["self_intersection_audit"]["true_nonadjacent_intersections_sample"]
    bins=Counter()
    for r in rows:
        x,y,z=r["position_world"]
        if z >= .76: key="shoulder_neck"
        elif abs(y) >= .11 and z >= .55: key="sleeve_armpit"
        elif z <= .20: key="lower_hem"
        else: key="torso_inner"
        bins[key]+=1
    return {"sampled_crossings":len(rows), "sample_region_counts":dict(bins),
            "note":"Counts describe the stored first-100 QA sample, not all 272 crossings."}

def bones():
    arm=[o for o in bpy.context.scene.objects if o.type=="ARMATURE"]
    return [{"object":o.name,"bones":[{"name":b.name,"head":v3(b.head_local),"tail":v3(b.tail_local)} for b in o.data.bones]} for o in arm]

before={str(p):sha(p) for p in (ROBE,BODY,PROBE,QA)}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROBE))
robe_meshes=all_mesh_world()
if len(robe_meshes)!=1: raise RuntimeError(f"expected one robe mesh, found {len(robe_meshes)}")
robe_ob, robe_pts=robe_meshes[0]
robe={"mesh":mesh_summary("raw_robe_glb"),"landmarks":robe_landmarks(robe_ob,robe_pts)}

bpy.ops.wm.open_mainfile(filepath=str(BODY))
body={"master":mesh_summary("body_v2_master"),"master_armatures":bones()}

bpy.ops.wm.open_mainfile(filepath=str(PROBE))
probe={"motion_probe":mesh_summary("body_v2_motion_probe_rest_file"),"armatures":bones()}
qa=json.loads(QA.read_text(encoding="utf-8"))
after={str(p):sha(p) for p in (ROBE,BODY,PROBE,QA)}

result={
 "status":"READ_ONLY_EVIDENCE", "source_hashes_before":before,"source_hashes_after":after,
 "source_files_unchanged":before==after,
 "coordinate_convention":"Observed dimensions are raw normalized units; project convention is upright +Z, face +X.",
 "robe":robe,"body":body,"probe":probe,
 "existing_robe_QA":{
   "topology":qa["topology"],"nonmanifold_edges":qa["nonmanifold_edges"],
   "crossings":{"total":qa["self_intersection_audit"]["true_nonadjacent_intersection_count"], **crossings_by_region(qa)},
   "openings":{k:{"uncapped_centerline_rays":v["uncapped_centerline_rays"],"immediate_cap_hits_under_002":v["immediate_cap_hits_under_002"]} for k,v in qa["opening_ray_probes"].items()}
 },
 "interpretation_limits":[
   "This records source geometry and the existing exact robe QA; it does not prove body-to-robe clearance or animation deformation.",
   "A raw single connected component cannot by itself identify a detachable inner shell. Any inner-layer deletion requires face-region selection in a working copy and same-camera silhouette comparison."
 ]
}
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(OUT)
