"""Read the third-party blend with auto execution disabled; write inventory only."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
load_warning = None
try:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'source/original/Human Basemeshes.blend'), use_scripts=False)
except RuntimeError as exc:
    # Blender 5 removes an orphaned legacy shape-key datablock during migration.
    # Continue only for this exact warning after the source actually loaded.
    if "ShapeKey KEKey.000 has an invalid 'from' pointer" not in str(exc) or not bpy.data.objects:
        raise
    load_warning = str(exc)
items = []
for ob in bpy.data.objects:
    item = {'name': ob.name, 'type': ob.type, 'location': list(ob.location),
            'rotation': list(ob.rotation_euler), 'scale': list(ob.scale),
            'dimensions': list(ob.dimensions), 'parent': ob.parent.name if ob.parent else None,
            'modifiers': [{'name': m.name, 'type': m.type,
                           'object': getattr(getattr(m, 'object', None), 'name', None),
                           'levels': getattr(m, 'levels', None),
                           'render_levels': getattr(m, 'render_levels', None),
                           'show_viewport': m.show_viewport} for m in ob.modifiers]}
    if ob.type == 'MESH':
        ob.data.calc_loop_triangles()
        item.update(vertices=len(ob.data.vertices), polygons=len(ob.data.polygons),
                    triangles=len(ob.data.loop_triangles),
                    uv_layers=[u.name for u in ob.data.uv_layers],
                    groups=[g.name for g in ob.vertex_groups],
                    shape_keys=list(ob.data.shape_keys.key_blocks.keys()) if ob.data.shape_keys else [])
        item['bounds'] = [list(ob.matrix_world @ Vector(v)) for v in ob.bound_box]
    if ob.type == 'ARMATURE':
        item['bones'] = [{'name': b.name, 'head': list(b.head_local), 'tail': list(b.tail_local),
                          'deform': b.use_deform} for b in ob.data.bones]
    items.append(item)
result = {'blender_version': bpy.app.version_string, 'load_warning': load_warning, 'objects': items,
          'text_blocks': [t.name for t in bpy.data.texts],
          'actions': [a.name for a in bpy.data.actions]}
(ROOT / 'evidence/source_inventory.json').write_text(json.dumps(result, indent=2), encoding='utf8')
print(json.dumps(result, indent=2))
