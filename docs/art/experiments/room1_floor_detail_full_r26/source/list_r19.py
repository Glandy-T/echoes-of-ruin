import bpy
bpy.ops.wm.open_mainfile(filepath=r'docs/art/experiments/room1_complete_r19/room1_complete_r19.blend')
for o in bpy.data.objects:
 if o.name.startswith('R19_P12') and o.type=='MESH': print(o.name, len(o.data.vertices), [m.name for m in o.data.materials])
