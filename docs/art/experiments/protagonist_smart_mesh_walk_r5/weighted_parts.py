"""Read connected pieces and their assigned bones without editing the exported file."""
import bpy,bmesh,sys,json
from pathlib import Path
p=Path(sys.argv[-1]).resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH' and len(o.vertex_groups))
bm=bmesh.new()
bm.from_mesh(o.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0.000001)
remaining=set(bm.verts)
layer=bm.verts.layers.deform.active
parts=[]
while remaining:
    stack=[remaining.pop()]
    vs=[]
    while stack:
        v=stack.pop()
        vs.append(v)
        for edge in v.link_edges:
            other=edge.other_vert(v)
            if other in remaining:
                remaining.remove(other)
                stack.append(other)
    coords=[o.matrix_world@v.co for v in vs]
    weights={}
    for v in vs:
        for idx,w in v[layer].items():
            if w>.05:
                name=o.vertex_groups[idx].name
                weights[name]=weights.get(name,0)+1
    hem=[v for v in vs if (o.matrix_world@v.co).z<0.41] if len(vs)==1610 else []
    hand_count=sum(any(o.vertex_groups[i].name in ('R_Hand','L_Hand') and w>.05 for i,w in v[layer].items()) for v in hem)
    parts.append(dict(hem_hand_vertices=hand_count,vertices=len(vs),bounds=[[fn(pt[i] for pt in coords) for i in range(3)] for fn in (min,max)],bones=weights))
(p.parent/'weighted_parts.json').write_text(json.dumps(sorted(parts,key=lambda x:x['vertices']),indent=2))

