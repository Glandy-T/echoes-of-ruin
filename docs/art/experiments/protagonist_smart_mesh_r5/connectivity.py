import bpy,bmesh,sys,json
from pathlib import Path
p=Path(sys.argv[-1]).resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p))
obj=next(o for o in bpy.context.scene.objects if o.type=='MESH')
bm=bmesh.new()
bm.from_mesh(obj.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0.000001)
remaining=set(bm.verts)
parts=[]
while remaining:
    stack=[remaining.pop()]
    vertices=[]
    while stack:
        v=stack.pop()
        vertices.append(v)
        for edge in v.link_edges:
            other=edge.other_vert(v)
            if other in remaining:
                remaining.remove(other)
                stack.append(other)
    z=[(obj.matrix_world@v.co).z for v in vertices]
    parts.append(dict(vertices=len(vertices),z_min=min(z),z_max=max(z)))
(p.parent/'connectivity.json').write_text(json.dumps(sorted(parts,key=lambda x:-x['vertices']),indent=2))
