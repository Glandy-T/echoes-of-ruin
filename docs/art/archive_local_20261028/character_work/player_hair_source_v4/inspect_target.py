"""Small geometric measurements used to place the two front sections."""
import bpy, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/original/source/Long hair.blend'),use_scripts=False)
hair=bpy.data.objects['Plain.001']; body=bpy.data.objects['Body.001']
def world(o,v):
    p=o.matrix_world@v.co;p.x-=.6;return [round(x,6) for x in p]
out={'hair_vertices':[{'id':v.index,'co':world(hair,v)} for v in hair.data.vertices],
     'hair_faces':[list(p.vertices) for p in hair.data.polygons],
     'body_upper_vertices':[world(body,v) for v in body.data.vertices if world(body,v)[2]>.95],
     'material_colors':{m.name:[(n.type,{i.name:list(i.default_value) for i in n.inputs if i.type=='RGBA'}) for n in m.node_tree.nodes] for m in bpy.data.materials if m.use_nodes}}
(ROOT/'target_measurements.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps(out))
