from pathlib import Path
import bpy,json
from mathutils import Vector
EXP=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(EXP/'model/protagonist_structure_v3.blend'))
scene=bpy.context.scene;cam=bpy.data.objects['QA_quarter']
after=bpy.data.collections['AFTER_V3'];before=bpy.data.collections['BEFORE_V2']
before.hide_viewport=True
for o in list(before.all_objects):o.hide_set(True)
after.hide_viewport=False
for o in list(after.all_objects):o.hide_set(False)
bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get()
inv=cam.calc_matrix_camera(dep,x=1280,y=720).inverted();out=[]
for x,y in [(650,300),(650,320),(650,340),(651,480),(640,500),(580,350),(590,360)]:
    a=inv@Vector((2*x/1280-1,1-2*y/720,-1,1));b=inv@Vector((2*x/1280-1,1-2*y/720,1,1))
    a=cam.matrix_world@(a.xyz/a.w);b=cam.matrix_world@(b.xyz/b.w)
    hit,p,n,fi,obj,mat=scene.ray_cast(dep,a,(b-a).normalized())
    row={'pixel':[x,y],'hit':hit}
    if hit:
        row.update(object=obj.name,face=fi,world_point=list(p),attrs={name:obj.data.attributes[name].data[fi].value for name in ('raw_obj_face_index','surface_kind') if name in obj.data.attributes})
    out.append(row)
(EXP/'source/visible_surface_audit.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out))
