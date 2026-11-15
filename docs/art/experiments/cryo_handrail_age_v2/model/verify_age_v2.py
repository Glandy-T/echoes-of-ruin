"""Read-only UV/density validation for the age-v2 editable Blender file."""
from pathlib import Path
import json, math
import bpy

HERE = Path(__file__).resolve().parent
EXPERIMENT = HERE.parent
ROOT = EXPERIMENT.parents[3]
BLEND = HERE / "handrail_age_v2.blend"
MANIFEST = EXPERIMENT / "model_manifest.json"
bpy.ops.wm.open_mainfile(filepath=str(BLEND))

def cross2(a, b, c):
    return (b.x-a.x)*(c.y-a.y) - (b.y-a.y)*(c.x-a.x)

results=[]
for obj in sorted((o for o in bpy.data.objects if o.type == "MESH" and o.data.materials and o.data.materials[0] and o.data.materials[0].name.startswith("AGE_")), key=lambda o:o.name):
    mesh=obj.data; uv=mesh.uv_layers.active; mesh.calc_loop_triangles()
    tex=next(n.image for n in obj.data.materials[0].node_tree.nodes if n.type=="TEX_IMAGE")
    tw,th=tex.size[:]
    world_area=0.; uv_area=0.
    resolution=256; hits=bytearray(resolution*resolution); hits_total=0
    for tri in mesh.loop_triangles:
        ls=tri.loops; a,b,c=[uv.data[l].uv.copy() for l in ls]
        pa,pb,pc=[obj.matrix_world @ mesh.vertices[mesh.loops[l].vertex_index].co for l in ls]
        world_area += (pb-pa).cross(pc-pa).length*.5
        uv_area += abs(cross2(a,b,c))*tw*th*.5
        q=[type(a)((u.x*resolution,u.y*resolution)) for u in (a,b,c)]
        den=cross2(q[0],q[1],q[2])
        if abs(den)<1e-12: continue
        for y in range(max(0,math.floor(min(v.y for v in q))), min(resolution-1,math.ceil(max(v.y for v in q)))+1):
          for x in range(max(0,math.floor(min(v.x for v in q))), min(resolution-1,math.ceil(max(v.x for v in q)))+1):
            p=type(a)((x+.5,y+.5)); aa=cross2(p,q[1],q[2])/den; bb=cross2(q[0],p,q[2])/den; cc=1-aa-bb
            if aa>=-1e-5 and bb>=-1e-5 and cc>=-1e-5:
                i=y*resolution+x; hits[i]=min(255,hits[i]+1); hits_total+=1
    unique=sum(1 for x in hits if x)
    overlap=max(0., (hits_total-unique)/max(1,hits_total))
    results.append({"object":obj.name,"material":obj.data.materials[0].name,"atlas_px":[tw,th],"effective_area_density_px_per_m":math.sqrt(uv_area/world_area),"uv_overlap_raster_ratio":overlap,"pass_density_80pm":abs(math.sqrt(uv_area/world_area)-80)<.2,"pass_no_material_overlap":overlap<.015})
manifest=json.loads(MANIFEST.read_text(encoding="utf8"))
manifest["uv_validation"]={"method":"per-object UV triangle area density; 256px raster union overlap metric (shared edges included)","entries":results,"all_density_pass":all(e["pass_density_80pm"] for e in results),"all_overlap_pass":all(e["pass_no_material_overlap"] for e in results)}
MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(manifest["uv_validation"],ensure_ascii=False))
