from pathlib import Path
import bpy, json
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'room1_floor_palette_r9'/'room1_floor_palette_r9_packed.blend'
bpy.ops.wm.open_mainfile(filepath=str(SRC))
rows=[]
for o in bpy.data.objects:
    if 'P12' in o.name or o.name.startswith('ContinuousRibbon_'):
        rows.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'hidden':bool(o.hide_render),'materials':[m.name for m in o.data.materials] if o.type=='MESH' else []})
print(json.dumps(rows,ensure_ascii=False,indent=2))
