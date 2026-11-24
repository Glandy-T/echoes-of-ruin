from pathlib import Path
import bpy,sys,numpy as np,json
p=Path(sys.argv[-1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p))
s=bpy.context.scene
out={}
for o in [o for o in s.objects if o.type=='MESH' and o.vertex_groups]:
    edges=np.array([list(e.vertices) for e in o.data.edges])
    def lengths(mesh):
        v=np.array([list(v.co) for v in mesh.vertices]);return np.linalg.norm(v[edges[:,1]]-v[edges[:,0]],axis=1)
    rest=lengths(o.data);keep=rest>0.002
    worst=(0,0)
    for f in range(0,57):
        s.frame_set(f);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
        ratio=lengths(ev.data)[keep]/rest[keep]
        worst=max(worst,(float(max(ratio)),f))
    out[o.name]=worst
print(sorted(out.items(),key=lambda kv:-kv[1][0])[:5])
(p.parent/(p.stem+'_stretch.json')).write_text(json.dumps(out,indent=2))
