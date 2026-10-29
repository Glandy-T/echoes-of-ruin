"""Export a bounded Room 1 -> 4F corridor -> West stair Godot greybox.

The doorway-side corridor is clipped at the existing Room 1 shell boundary,
so the Room 1 floor and walls are supplied only by the current Godot scene.
No CAD geometry is imported; the source is the independent v2 Blender model.
"""
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / "docs/art/experiments/cryo_building_stairs_v2/cryo_building_stairs_v2.blend"
DEST = ROOT / "assets/art/cryo_building_room1_route_v3/room1_west_route_v3.glb"
DEST.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))

CX, CY = 93.2, 43.1
ROUTE_RECT = (-2.6, 13.7, 21.0, 45.2)  # frozen 4F SW-01 back edge to West stair
review = bpy.data.collections.new("GODOT_ROOM1_WEST_ROUTE_V3_EXPORT_ONLY")
bpy.context.scene.collection.children.link(review)
selected = []


def bounds(obj):
    pts = [obj.matrix_world @ Vector(p) for p in obj.bound_box]
    return (min(p.x for p in pts)+CX, min(p.y for p in pts)+CY,
            max(p.x for p in pts)+CX, max(p.y for p in pts)+CY,
            min(p.z for p in pts), max(p.z for p in pts))


def crop(rect):
    a,b,c,d = rect
    e,f,g,h = ROUTE_RECT
    result = (max(a,e), max(b,f), min(c,g), min(d,h))
    return result if result[2]-result[0] > .005 and result[3]-result[1] > .005 else None


def box(name, rect, low, high, material):
    x1,y1,x2,y2 = rect
    x1,x2,y1,y2 = x1-CX,x2-CX,y1-CY,y2-CY
    verts = [(x1,y1,low),(x2,y1,low),(x2,y2,low),(x1,y2,low),
             (x1,y1,high),(x2,y1,high),(x2,y2,high),(x1,y2,high)]
    faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),
             (2,3,7,6),(3,0,4,7)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    review.objects.link(obj)
    if material:
        mesh.materials.append(material)
    selected.append(obj)


for obj in list(bpy.data.objects):
    if obj.type != 'MESH':
        continue
    if obj.get('level') == '4F' and (
        obj.get('kind') == 'frozen_floor_cell_clipped_for_stairs'
        or obj.get('frozen_wall_id')
        or obj.get('locked_placeholder')
    ):
        a,b,c,d,low,high = bounds(obj)
        rect = crop((a,b,c,d))
        if rect:
            box('R4F_'+obj.name, rect, low, high,
                obj.data.materials[0] if obj.data.materials else None)
    if obj.get('stair_id') == 'West_Stair' and obj.get('level') in ('1F','2F','3F','4F'):
        selected.append(obj)
    if obj.get('locked_placeholder') and obj.get('level') in ('1F','2F','3F') and obj.get('door_id') in ('D077','D078'):
        selected.append(obj)

bpy.ops.object.select_all(action='DESELECT')
for obj in selected:
    obj.hide_render = False
    obj.hide_set(False)
    obj.select_set(True)
bpy.context.view_layer.objects.active = selected[0]
bpy.ops.export_scene.gltf(filepath=str(DEST), export_format='GLB', use_selection=True,
                          export_apply=True, export_extras=True)
print(f'EXPORTED_MESHES={len(selected)}; BYTES={DEST.stat().st_size}', flush=True)
