"""Sample skinned edge stretch across the exported walk animation."""
import bpy, json, sys
import numpy as np
from pathlib import Path
p=Path(sys.argv[-1]).resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p))
scene=bpy.context.scene
out={}
for obj in [o for o in scene.objects if o.type=='MESH' and len(o.vertex_groups)]:
    edges=np.array([e.vertices[:] for e in obj.data.edges])
    def lengths(mesh):
        xyz=np.array([v.co[:] for v in mesh.vertices])
        return np.linalg.norm(xyz[edges[:,0]]-xyz[edges[:,1]],axis=1)
    rest=lengths(obj.data)
    keep=rest>0.002
    start,end=max((a.frame_range for a in bpy.data.actions),key=lambda r:r[1]-r[0])
    samples=[]
    for frame in range(round(start),round(end)+1):
        scene.frame_set(frame)
        mesh=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
        ratios=lengths(mesh)[keep]/rest[keep]
        samples.append(dict(frame=frame,max=float(ratios.max()),p99=float(np.percentile(ratios,99)),edges_over_2=int((ratios>2).sum()),worst_edge=edges[keep][ratios.argmax()].tolist()))
    out[obj.name]=samples
(p.parent/(p.stem+'_stretch.json')).write_text(json.dumps(out,indent=2))
