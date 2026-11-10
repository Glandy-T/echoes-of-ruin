"""Build review-only FA-A / FA-B facades from the frozen standard-floor plan.

The source deliberately makes no opening, EN attachment, or new machine anchor.
It is geometry/UV handoff only; PixelLab-owned 256px maps are intentionally not
generated here.  Materials retain the required atlas and world-density metadata.
"""
from pathlib import Path
import json, sys
import bpy

ROOT = Path(__file__).resolve().parents[5]
PLAN = ROOT / "docs/cad/cryo_standard_floor/v3_trim/floor_layout.json"
OUT = ROOT / "docs/art/experiments/cryo_building_review_v1"
MODELS = ROOT / "assets/art/cryo_building_review_v1/models"
BLEND = OUT / "model/facade_assembly_v1.blend"
PLACEMENT = OUT / "facade_material_placement.json"
with PLAN.open(encoding="utf-8") as f:
    DATA = json.load(f)
P = DATA["parameters"]

# Local coordinates match the frozen blockout convention: source-plan centre is 0,0.
X0, X1 = -P["CenterX"], P["MainWidth"] - P["CenterX"]
Y0, Y1 = P["FloorSouth"] - P["CenterY"], P["FloorNorth"] - P["CenterY"]
Z0, Z1 = 0.0, 16 * P["StoreyHeight"]
B4Z = -4 * P["StoreyHeight"]
STOREY = P["StoreyHeight"]
ATLAS = 256
PX_PER_M = 80

COLORS = {
    "M06-01": (0.42, 0.46, 0.45, 1), "M06-02": (0.34, 0.38, 0.38, 1),
    "M06-03": (0.46, 0.49, 0.47, 1), "M06-J": (0.18, 0.22, 0.22, 1),
    "M06-R": (0.29, 0.33, 0.34, 1), "M07": (0.25, 0.32, 0.34, 1), "M06-BASE": (0.33,0.37,0.34,1),
}

def col(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent.children if parent else bpy.context.scene.collection.children).link(c)
    return c

def material(name):
    m = bpy.data.materials.new(name)
    m.diffuse_color = COLORS[name]
    m.use_nodes = True
    bsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    bsdf.inputs["Base Color"].default_value = COLORS[name]
    bsdf.inputs["Roughness"].default_value = .86 if name.startswith("M06") else .70
    bsdf.inputs["Metallic"].default_value = .0 if name.startswith("M06") else .34
    m["texture_atlas_expected"] = "PixelLab pending: 256x256 px"
    m["uv_world_density_px_per_m"] = PX_PER_M
    m["atlas_meters_per_repeat"] = ATLAS / PX_PER_M
    return m

MATS = {name: material(name) for name in COLORS}
BATCHES = {}

def cube(name, loc, dims, c, mat, **tags):
    # Panel-heavy facades are batched by collection/material rather than emitting
    # thousands of Blender objects. This keeps the GLBs light while all seam faces
    # and their metric UV scale remain explicit mesh geometry.
    key=(c.name, mat.name)
    b=BATCHES.setdefault(key, {"collection":c,"material":mat,"verts":[],"faces":[],"names":[],"origins":{}})
    x,y,z=loc; dx,dy,dz=(d/2 for d in dims)
    n=len(b["verts"])
    b["verts"].extend([(x-dx,y-dy,z-dz),(x+dx,y-dy,z-dz),(x+dx,y+dy,z-dz),(x-dx,y+dy,z-dz),
                       (x-dx,y-dy,z+dz),(x+dx,y-dy,z+dz),(x+dx,y+dy,z+dz),(x-dx,y+dy,z+dz)])
    p=len(b['faces']);b["faces"].extend([(n,n+3,n+2,n+1),(n+4,n+5,n+6,n+7),(n,n+1,n+5,n+4),
                       (n+1,n+2,n+6,n+5),(n+2,n+3,n+7,n+6),(n+3,n,n+4,n+7)])
    if 'native_map_center_top' in tags:
        for i in range(6):b['origins'][p+i]=tags['native_map_center_top']
    b["names"].append(name)

def flush_batches():
    for (collection_name, mat_name), b in BATCHES.items():
        mesh=bpy.data.meshes.new(f"{collection_name}_{mat_name}_Mesh")
        mesh.from_pydata(b["verts"], [], b["faces"]); mesh.update()
        uv=mesh.uv_layers.new(name="UV0_World80pxm")
        for poly in mesh.polygons:
            n=poly.normal
            for li in poly.loop_indices:
                co=mesh.vertices[mesh.loops[li].vertex_index].co
                pair=(co.x,co.y) if abs(n.z)>.5 else ((co.y,co.z) if abs(n.x)>.5 else (co.x,co.z))
                if poly.index in b['origins']:
                    x,top=b['origins'][poly.index];uv.data[li].uv=(.52+(co.x-x)*PX_PER_M/ATLAS,1+(co.z-top)*PX_PER_M/ATLAS)
                else: uv.data[li].uv=(pair[0]/(ATLAS/PX_PER_M),pair[1]/(ATLAS/PX_PER_M))
        mesh.materials.append(b["material"])
        o=bpy.data.objects.new(f"{collection_name}_{mat_name}_Geometry",mesh)
        o["uv0_density_px_per_m"]=PX_PER_M; o["uv0_atlas_size_px"]=[ATLAS,ATLAS]; o["uv0_repeat_m"]=ATLAS/PX_PER_M
        o["batched_component_count"]=len(b["names"])
        b["collection"].objects.link(o)

def node_empty(name, loc, c, **tags):
    o = bpy.data.objects.new(name, None)
    o.empty_display_type = 'ARROWS'; o.empty_display_size = 1.8; o.location = loc
    for k, v in tags.items(): o[k] = v
    c.objects.link(o)
    return o

def envelope_backer(c):
    # Closed shell behind panel seams; exactly frozen main envelope, no new tower/holes.
    cube("FrozenEnvelope_Back_South", ((X0+X1)/2,Y0+.08,Z1/2), (X1-X0,.13,Z1), c, MATS["M06-BASE"], frozen_envelope=True)
    cube("FrozenEnvelope_Back_North", ((X0+X1)/2,Y1-.08,Z1/2), (X1-X0,.13,Z1), c, MATS["M06-BASE"], frozen_envelope=True)
    cube("FrozenEnvelope_Back_West", (X0+.08,(Y0+Y1)/2,Z1/2), (.13,Y1-Y0,Z1), c, MATS["M06-BASE"], frozen_envelope=True)
    cube("FrozenEnvelope_Back_East", (X1-.08,(Y0+Y1)/2,Z1/2), (.13,Y1-Y0,Z1), c, MATS["M06-BASE"], frozen_envelope=True)
    cube("SharedRoofDeck",(0,0,Z1-.07),(X1-X0,Y1-Y0,.14),c,MATS['M06-BASE'])
    for loc,dims in [((0,Y0-.023,.3),(X1-X0,.045,.6)),((0,Y1+.023,.3),(X1-X0,.045,.6)),((X0-.023,0,.3),(.045,Y1-Y0,.6)),((X1+.023,0,.3),(.045,Y1-Y0,.6))]:
        cube('SharedPlinth',loc,dims,c,MATS['M06-BASE'])

def panel(c, face, a0, a1, z0, z1, variant, ordinal):
    # outward panel is 40mm proud of backer, joints remain 18mm real gaps.
    material=MATS['M06-02' if ordinal%13 in (5,8) else 'M06-03' if ordinal%17 in (3,11) else 'M06-01']
    z0=max(z0,.600)
    if z1<=z0:return
    depth = .015
    if face == "S": loc=((a0+a1)/2,Y0-depth/2,z0+(z1-z0)/2); dims=(a1-a0,depth,z1-z0)
    elif face == "N": loc=((a0+a1)/2,Y1+depth/2,z0+(z1-z0)/2); dims=(a1-a0,depth,z1-z0)
    elif face == "W": loc=(X0-depth/2,(a0+a1)/2,z0+(z1-z0)/2); dims=(depth,a1-a0,z1-z0)
    else: loc=(X1+depth/2,(a0+a1)/2,z0+(z1-z0)/2); dims=(depth,a1-a0,z1-z0)
    return cube(f"{variant}_Panel_{face}_{ordinal:04d}",loc,dims,c,material, panel_face=face, panel_extent_m=[a0,a1,z0,z1])

def panels_a(c, face, length):
    # Center-symmetric horizontal 3.20m grid, three rows per floor, with remainder panels.
    rows = [0, STOREY/3, 2*STOREY/3, STOREY]
    xs = [length/2]
    n=1
    while xs[-1] < length: xs.extend([length/2-n*3.2, length/2+n*3.2]); n += 1
    cuts = sorted({max(0,min(length,x)) for x in xs} | {0,length})
    ordinal=0
    for level in range(16):
        for r in range(3):
            for i in range(len(cuts)-1):
                a0,a1=cuts[i]+.009,cuts[i+1]-.009
                if a1>a0: panel(c,face,a0-length/2,a1-length/2,level*STOREY+rows[r]+.009,level*STOREY+rows[r+1]-.009,"FA-A",ordinal); ordinal+=1

def panels_b(c, face, length):
    # 1.20m full-storey vertical panels, real 18mm vertical and 20mm floor joints.
    cuts=[0.0]; x=0
    while x < length: x=min(length,x+1.2); cuts.append(x)
    ordinal=0
    for level in range(16):
        for i in range(len(cuts)-1):
            a0,a1=cuts[i]+.009,cuts[i+1]-.009
            if a1>a0: panel(c,face,a0-length/2,a1-length/2,level*STOREY+.010,(level+1)*STOREY-.010,"FA-B",ordinal); ordinal+=1

def traffic_trims(c, variant):
    # Exact frozen elevator-node exterior strips.  Stairs remain mineral, never windowed.
    for node in DATA["elevator_nodes"]:
        x1,x2=node["x1"]-P["CenterX"],node["x2"]-P["CenterX"]
        y1,y2=node["y1"]-P["CenterY"],node["y2"]-P["CenterY"]
        side=-1 if (x1+x2)/2<0 else 1; exterior=x1 if side<0 else x2
        # Actual node volume, including its mineral return walls and closed roof.
        cube(f"{variant}_{node['id']}_MineralVolume",((x1+x2)/2,(y1+y2)/2,Z1/2),(x2-x1,y2-y1,Z1),c,MATS['M06-01'])
        if variant=='FA-A':
            for y in [y1+.075,y2-.075]:cube(f'{node["id"]}_Edge150',(exterior+side*.011,y,Z1/2),(.023,.15,Z1),c,MATS['M07'])
        else:
            a=y1
            while a<y2-1e-6:
                b=min(a+.60,y2)
                if b-a>.025:cube(f'{node["id"]}_ZincModule',(exterior+side*.013,(a+b)/2,Z1/2),(.026,b-a-.025,Z1),c,MATS['M07'])
                a=b
        # node seams/corners intentionally no invented machinery or aperture.
        node_empty(f"NODE_{node['id']}",((x1+x2)/2,(y1+y2)/2,0),c, frozen_node=node['id'], source="floor_layout.json")
    for st in DATA["stairs"]:
        x1,x2=st['x1']-P['CenterX'],st['x2']-P['CenterX'];y1,y2=st['y1']-P['CenterY'],st['y2']-P['CenterY']
        if x1<X0 or x2>X1:
            cube(f"{variant}_{st['id']}_MineralStairReturn",((x1+x2)/2,(y1+y2)/2,Z1/2),(x2-x1,y2-y1,Z1),c,MATS['M06-01'])
        node_empty(f"NODE_{st['id']}",((st['x1']+st['x2'])/2-P['CenterX'],(st['y1']+st['y2'])/2-P['CenterY'],0),c, frozen_node=st['id'], material_policy="M06_continuous_corner")

def placed_facade_details(c, variant):
    # M06-J is restrained, physical corner-return joint shadow only; it is not a
    # black storey belt. M06-R placements exactly match the review JSON E3 sources.
    cube(f"{variant}_M06J_WestCorner",(X0-.046,Y0+.20,Z1/2),(.008,.40,Z1),c,MATS["M06-J"], purpose="corner_return_joint")
    cube(f"{variant}_M06J_EastCorner",(X1+.046,Y1-.20,Z1/2),(.008,.40,Z1),c,MATS["M06-J"], purpose="corner_return_joint")
    cube(f"{variant}_E3_Runoff_S",(-28.8,Y0-.016,59.4),(.60,.002,2.8),c,MATS["M06-R"], age_region="E3", source="south_coping_joint",native_map_center_top=(-28.8,Z1))
    cube(f"{variant}_E3_Runoff_N",(35.2,Y1+.016,59.4),(.60,.002,2.8),c,MATS["M06-R"], age_region="E3", source="north_coping_joint",native_map_center_top=(35.2,Z1))

def common_k01(c):
    # 600mm parapet is the approved art addition, no playable roof equipment.
    z=Z1+.30
    for name,loc,dims in [
        ("K01_Parapet_S",((X0+X1)/2,Y0,z),(X1-X0,.18,.6)), ("K01_Parapet_N",((X0+X1)/2,Y1,z),(X1-X0,.18,.6)),
        ("K01_Parapet_W",(X0,(Y0+Y1)/2,z),(.18,Y1-Y0,.6)), ("K01_Parapet_E",(X1,(Y0+Y1)/2,z),(.18,Y1-Y0,.6))]:
        cube(name,loc,dims,c,MATS["M06-01"], art_addition=True, no_new_floor=True)
    cube("K01_M07_Coping_S",((X0+X1)/2,Y0,Z1+.62),(X1-X0,.24,.06),c,MATS["M07"], cap_visible_mm=60)
    cube("K01_M07_Coping_N",((X0+X1)/2,Y1,Z1+.62),(X1-X0,.24,.06),c,MATS["M07"], cap_visible_mm=60)
    cube("K01_M07_Coping_W",(X0,(Y0+Y1)/2,Z1+.62),(.24,Y1-Y0,.06),c,MATS["M07"], cap_visible_mm=60)
    cube("K01_M07_Coping_E",(X1,(Y0+Y1)/2,Z1+.62),(.24,Y1-Y0,.06),c,MATS["M07"], cap_visible_mm=60)

def technical_b4(c):
    # Separate technical B4-B1 assembly: has no exterior weather-mask placement.
    tech=col("TECHNICAL_B4_B1_ASSEMBLY",c)
    for name,loc,dims in [
       ("B4B1_S",((X0+X1)/2,Y0,(B4Z)/2),(X1-X0,.12,-B4Z)), ("B4B1_N",((X0+X1)/2,Y1,(B4Z)/2),(X1-X0,.12,-B4Z)),
       ("B4B1_W",(X0,(Y0+Y1)/2,(B4Z)/2),(.12,Y1-Y0,-B4Z)), ("B4B1_E",(X1,(Y0+Y1)/2,(B4Z)/2),(.12,Y1-Y0,-B4Z))]:
       cube(name,loc,dims,tech,MATS["M06-01"], engineering_section_only=True, weathering="none")
    node_empty("B4_TECHNICAL_ASSEMBLY_ANCHOR",(0,0,B4Z),tech, technical_stack="B4_to_B1", no_new_attachment=True)

def export_collection(c, path):
    bpy.ops.object.select_all(action='DESELECT')
    def visit(cc):
        for o in cc.objects: o.select_set(True)
        for child in cc.children: visit(child)
    visit(c)
    bpy.context.view_layer.objects.active = next((o for o in c.objects if o.type == 'MESH'), None)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True,
                              export_apply=True, export_extras=True, export_materials='EXPORT')

def build():
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for cc in list(bpy.data.collections): bpy.data.collections.remove(cc)
    BATCHES.clear()
    root=col("CRYO_BUILDING_REVIEW_V1_FACADES")
    root["source_plan"]="docs/cad/cryo_standard_floor/v3_trim/floor_layout.json"
    root["coordinate_origin"]="frozen plan centre; z=1F slab datum"
    root["main_envelope_m"]=[P['MainWidth'],P['MainDepth']]
    root["above_ground_floors"]=16
    root["underground_technical_floors"]=4
    root["status"]="REVIEW_CANDIDATE__NO_GODOT_SCENE_MODIFIED"
    ka=col("EXTERIOR_K01_COMMON",root); common_k01(ka)
    for variant, make in (("FA-A",panels_a),("FA-B",panels_b)):
        c=col(variant,root); envelope_backer(c)
        make(c,"S",X1-X0); make(c,"N",X1-X0); make(c,"W",Y1-Y0); make(c,"E",Y1-Y0)
        traffic_trims(c,variant); placed_facade_details(c,variant); technical_b4(c)
        c["variant"] = variant; c["same_frozen_envelope"] = True; c["new_openings"] = False
        c["EN_attachment"] = "ASSET_ONLY__NO_CONFIRMED_FROZEN_EXTERIOR_EXIT_ANCHOR"
        c["machine_attachment"] = "NONE__NO_NEW_MACHINE_ANCHOR_OR_PORTAL"
    flush_batches()
    export_collection(bpy.data.collections["FA-A"], MODELS / "FA-A_complete_envelope.glb")
    export_collection(bpy.data.collections["FA-B"], MODELS / "FA-B_complete_envelope.glb")
    export_collection(ka, MODELS / "EXTERIOR_K01_common.glb")
    sys.path.insert(0,str(BLEND.parent))
    from bind_preview_materials import bind
    bind(MODELS.parent/'textures')
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))

if __name__ == '__main__': build()
