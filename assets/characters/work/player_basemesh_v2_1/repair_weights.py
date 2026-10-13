"""Create v2.1 from v2 by repairing only body vertex weights.

The original blend is opened read-only in practice: it is never saved.  v2.1 keeps
the master scene's mesh, UVs, shape keys and original rig, while removing only the
display-only review scene before writing the new compact deliverable.
"""
import bpy, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'player_basemesh_v2'/'body_165cm_review_v2.blend'
TARGET=ROOT/'body_165cm_validated_v2_1.blend'
BODY='Body_165cm_CC0_pistachio'; RIG='Body_Rig_original'

def evaluated_world_dimensions(body):
    deps=bpy.context.evaluated_depsgraph_get()
    evaluated=body.evaluated_get(deps)
    verts=[evaluated.matrix_world @ vertex.co for vertex in evaluated.data.vertices]
    return [max(vertex[i] for vertex in verts)-min(vertex[i] for vertex in verts) for i in range(3)]

def stats(body, rig):
    bones={b.name for b in rig.data.bones if b.use_deform}
    no_bone=[g.name for g in body.vertex_groups if g.name not in bones]
    count=[]; unweighted=0; under=over=0
    for v in body.data.vertices:
        values=[x.weight for x in v.groups if body.vertex_groups[x.group].name in bones and x.weight>0]
        if not values: unweighted+=1
        count.append(len(values)); s=sum(values)
        if values and s<.999: under+=1
        if values and s>1.001: over+=1
    return {'vertex_groups_without_deform_bone':no_bone,'unweighted_vertices':unweighted,
            'max_influences':max(count),'vertices_over_4':sum(x>4 for x in count),
            'vertices_under_normalized':under,'vertices_over_normalized':over,
            'key_1_value':body.data.shape_keys.key_blocks['Key 1'].value,
            'uv_layer':body.data.uv_layers.active.name if body.data.uv_layers.active else None,
            'evaluated_world_dimensions_m':evaluated_world_dimensions(body)}

bpy.ops.wm.open_mainfile(filepath=str(SOURCE), use_scripts=False)
body=bpy.data.objects[BODY]; rig=bpy.data.objects[RIG]
master=bpy.data.scenes['01_BODY_MASTER_165cm']
bpy.context.window.scene=master
bpy.context.view_layer.update()
before=stats(body,rig)
bones={b.name for b in rig.data.bones if b.use_deform}
heel_to_foot={'heel.L':'foot.L','heel.R':'foot.R'}

for vertex in body.data.vertices:
    weights={}
    for assignment in vertex.groups:
        name=body.vertex_groups[assignment.group].name
        if assignment.weight <= 0: continue
        name=heel_to_foot.get(name,name)
        if name in bones: weights[name]=weights.get(name,0.0)+assignment.weight
    chosen=sorted(weights.items(),key=lambda item:(-item[1],item[0]))[:4]
    total=sum(w for _,w in chosen)
    for group in body.vertex_groups:
        try: group.remove([vertex.index])
        except RuntimeError: pass
    if total:
        for name,weight in chosen: body.vertex_groups[name].add([vertex.index],weight/total,'REPLACE')

for group in list(body.vertex_groups):
    if group.name not in bones: body.vertex_groups.remove(group)

# Save only the real master scene. Review display copies are intentionally excluded.
for scene in list(bpy.data.scenes):
    if scene != master: bpy.data.scenes.remove(scene,do_unlink=True)
after=stats(body,rig)
report={'source':str(SOURCE),'target':str(TARGET),'body':BODY,'rig':RIG,'repair':{
    'heel_groups_merged_into':['foot.L','foot.R'],'removed_non_bone_groups':['heel.L','heel.R'],
    'max_influences_kept':4,'normalization':'per vertex after retaining strongest four valid deform groups'},
    'before':before,'after':after}
(ROOT/'repair_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
print(json.dumps(report,indent=2))
