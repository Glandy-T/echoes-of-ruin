"""Bounded exact-self-union trial on a disposable imported garment copy."""
from pathlib import Path
import bpy,json,hashlib
EXP=Path(__file__).resolve().parents[1]
RAW=EXP.parent/'protagonist_tripo_robe_v2/model/protagonist_tripo_robe_v2_raw.glb'
LIB=EXP.parent/'protagonist_tripo_body_v1/source/body_topology_check.py'
ns={'__file__':str(LIB),'__name__':'geometry_library'}
exec(compile(LIB.read_text(encoding='utf-8').split("\nbefore={'glb':")[0],str(LIB),'exec'),ns)
original=hashlib.sha256(RAW.read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(RAW));ob=next(o for o in bpy.context.scene.objects if o.type=='MESH');bpy.context.view_layer.objects.active=ob;ob.select_set(True)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);ob.data.calc_loop_triangles()
before={'topology':ns['topology'](ob.data),'crossings':ns['self_intersections'](ob.data,ob.matrix_world)}
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
result=bpy.ops.mesh.intersect_boolean(operation='UNION',use_self=True,solver='EXACT')
bpy.ops.object.mode_set(mode='OBJECT');ob.data.update();ob.data.calc_loop_triangles()
after={'topology':ns['topology'](ob.data),'crossings':ns['self_intersections'](ob.data,ob.matrix_world)}
scratch=EXP/'scratch';scratch.mkdir(exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(scratch/'self_union_trial.blend'))
assert hashlib.sha256(RAW.read_bytes()).hexdigest()==original
(EXP/'source/self_union_trial.json').write_text(json.dumps({'operator_result':list(result),'before':before,'after':after,'raw_unchanged_sha256':original,'scope':'Disposable trial only; no silhouette, source normals, fit or production acceptance.'},indent=2),encoding='utf-8')
print('EXACT_SELF_UNION_RESULT',after['topology'],'crossings',after['crossings']['true_nonadjacent_intersection_count'])
