import bpy,json
from pathlib import Path
p=Path.cwd()/'docs/art/experiments/protagonist_blender_cleanup_v1/source'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p.parents[1]/'protagonist_tripo_h25_v1/model/protagonist_tripo_h25_v1_raw.glb'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH')
r={'vertices':[list(o.matrix_world@v.co) for v in o.data.vertices],'faces':[list(f.vertices) for f in o.data.polygons]}
(p/'raw_geometry_diagnostic.json').write_text(json.dumps(r))
for z in [.15,.2,.3,.4,.5,.6,.65,.7,.75,.8,.85,.9,.95]:
 a=[v for v in r['vertices'] if abs(v[2]-z)<.015]
 if a:print(z, len(a),'x',round(min(v[0] for v in a),3),round(max(v[0] for v in a),3),'y',round(min(v[1] for v in a),3),round(max(v[1] for v in a),3))
