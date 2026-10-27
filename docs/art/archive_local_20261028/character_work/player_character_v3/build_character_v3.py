"""Editable separated protagonist trial from a licensed human base mesh.

Run in Blender 5.0.1 with --background --factory-startup --disable-autoexec.
Diagnostic poses are technical checks, not production animation clips.
"""
import bpy
import bmesh
import math
import json
import sys
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / 'player_basemesh_v2/body_165cm_review_v2.blend'
sys.path.insert(0, str(ROOT))
for name in ['evidence', 'uv_guides', 'textures', 'references']:
    (ROOT / name).mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE), use_scripts=False)
body = bpy.data.objects['Body_165cm_CC0_pistachio']
rig = bpy.data.objects['Body_Rig_original']
for ob in list(bpy.data.objects):
    if ob not in (body, rig):
        bpy.data.objects.remove(ob, do_unlink=True)
scene = bpy.data.scenes.new('01_CHARACTER_EDITABLE')
scene.collection.objects.link(body)
scene.collection.objects.link(rig)
bpy.context.window.scene = scene
for sc in list(bpy.data.scenes):
    if sc != scene:
        bpy.data.scenes.remove(sc)
bpy.context.preferences.filepaths.save_version = 0
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
body.name = 'Body'
rig.name = 'Character_Rig'

def select_only(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.hide_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob

def mesh_world_bounds(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    pts = [ev.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return [[min(p[i] for p in pts), max(p[i] for p in pts)] for i in range(3)]

# Freeze the source's actual female shape while retaining interpolated weights.
select_only(body)
bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
sub = next(m for m in body.modifiers if m.type == 'SUBSURF')
bpy.ops.object.modifier_apply(modifier=sub.name)
mw = body.matrix_world.copy()
body.parent = None
body.matrix_world = mw
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
select_only(rig)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# The source's legs are spread in its A-pose. Rebase only the leg splay so the
# long garment can be made around a natural stance. Preserve upper-body A-pose.
for side in ('L', 'R'):
    pb = rig.pose.bones['thigh.' + side]
    b = pb.bone
    direction = b.tail_local - b.head_local
    q = direction.rotation_difference(Vector((0, 0, -1)))
    pb.matrix = Matrix.Translation(b.head_local) @ q.to_matrix().to_4x4() @ Matrix.Translation(-b.head_local) @ b.matrix_local
bpy.context.view_layer.update()
select_only(body)
arm = next(m for m in body.modifiers if m.type == 'ARMATURE')
bpy.ops.object.modifier_apply(modifier=arm.name)
select_only(rig)
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.armature_apply(selected=False)
bpy.ops.object.mode_set(mode='OBJECT')
arm = body.modifiers.new('Skin', 'ARMATURE')
arm.object = rig

# Uniform scale of geometry and bind bones, with unit transforms afterwards.
bpy.context.view_layer.update()
box = mesh_world_bounds(body)
s = 1.65 / (box[2][1]-box[2][0])
transform = Matrix.Scale(s,4) @ Matrix.Translation((0,0,-box[2][0]))
body.data.transform(transform)
rig.data.transform(transform)
bpy.context.view_layer.update()
body['source'] = 'pistachio / Human Basemeshes / CC0'
body['modifications'] = 'source female shape and one subdivision baked; leg splay rebased; 165cm; skin weights retained'
body['source_original'] = '../player_basemesh_v2/source/original/Human Basemeshes.blend'
rig.show_in_front = True

def mat(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color,1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color,1)
    bs.inputs['Roughness'].default_value = .9
    bs.inputs['Specular IOR Level'].default_value = .18
    return m

skin = mat('Skin_placeholder_replaceable', (.51,.36,.265))
clothmat = mat('Robe_offwhite_replaceable', (.77,.81,.80))
hairmat = mat('Hair_blueblack_replaceable', (.017,.026,.036))
body.data.materials.clear()
body.data.materials.append(skin)
for p in body.data.polygons:
    p.use_smooth = True

def vertex_weights(ob):
    return [{ob.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight > 1e-6} for v in ob.data.vertices]

def set_weights(ob, weights):
    names = sorted(set(k for w in weights for k in w))
    groups = {n: ob.vertex_groups.new(name=n) for n in names}
    for i, ws in enumerate(weights):
        total = sum(ws.values())
        if total:
            for n,w in ws.items():
                if w > 1e-6:
                    groups[n].add([i],w/total,'REPLACE')

def boundary_loops(me):
    bm = bmesh.new(); bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    graph = {}
    for e in bm.edges:
        if e.is_boundary:
            a,b = [v.index for v in e.verts]
            graph.setdefault(a,[]).append(b); graph.setdefault(b,[]).append(a)
    assert all(len(v)==2 for v in graph.values()), 'Branched clothing boundary'
    loops=[]; unused=set(graph)
    while unused:
        start=min(unused); chain=[start]; previous=None; current=start
        while True:
            nxt=next(n for n in graph[current] if n!=previous)
            if nxt==start: break
            chain.append(nxt); previous,current=current,nxt
        unused.difference_update(chain); loops.append(chain)
    bm.free()
    return loops

def add_skirt_bones():
    select_only(rig)
    bpy.ops.object.mode_set(mode='EDIT')
    for side,sx in [('L',1),('R',-1)]:
        for panel,sy in [('front',-1),('back',1)]:
            a=rig.data.edit_bones.new(f'skirt_{panel}.{side}')
            a.head=(sx*.10,sy*.085,.87);a.tail=(sx*.16,sy*.14,.48)
            a.parent=rig.data.edit_bones['hips'];a.use_deform=True
            b=rig.data.edit_bones.new(f'skirt_{panel}_hem.{side}')
            b.head=a.tail;b.tail=(sx*.20,sy*.18,.155)
            b.parent=a;b.use_connect=True;b.use_deform=True
    bpy.ops.object.mode_set(mode='OBJECT')

add_skirt_bones()

def skirt_weights(x,y,z,waist_z):
    u=min(1,max(0,(waist_z-z)/.22))
    lower=min(1,max(0,(.56-z)/.20))
    # Two adjacent sectors, with continuous transitions through center lines.
    left=.5+.5*math.tanh(x/.075)
    front=.5-.5*math.tanh(y/.07)
    weights={'hips':1-u}
    for side,sw in [('L',left),('R',1-left)]:
        for panel,pw in [('front',front),('back',1-front)]:
            weights[f'skirt_{panel}.{side}']=u*sw*pw*(1-lower)
            weights[f'skirt_{panel}_hem.{side}']=u*sw*pw*lower
    top=sorted(weights.items(),key=lambda p:p[1],reverse=True)[:4]
    total=sum(w for _,w in top)
    return {k:w/total for k,w in top if w>1e-5}

def make_robe():
    weights=vertex_weights(body)
    hand_names=[g.name for g in body.vertex_groups if g.name.startswith(('hand.','palm.','f_','thumb.'))]
    waist_z=rig.data.bones['hips'].head_local.z + .004
    neck_z=rig.data.bones['neck'].head_local.z + .015
    keep=[]
    for p in body.data.polygons:
        vs=[body.data.vertices[i].co for i in p.vertices]
        center=sum(vs,Vector())/len(vs)
        hand=sum(sum(weights[i].get(n,0) for n in hand_names) for i in p.vertices)/len(p.vertices)
        if waist_z < center.z < neck_z and hand < .47:
            keep.append(p)
    used=sorted(set(i for p in keep for i in p.vertices))
    remap={old:new for new,old in enumerate(used)}
    verts=[]; ws=[]
    for i in used:
        v=body.data.vertices[i]
        co=v.co + v.normal*.020
        # Loose plain garment: ease the waist and chest without sculpting anatomy.
        if abs(co.x) < .19 and .85 < co.z < 1.30:
            co.x *= 1.075
            if co.y < 0: co.y = min(co.y,-.115)
            else: co.y=max(co.y,.106)
        verts.append(tuple(co)); ws.append(dict(weights[i]))
    faces=[tuple(remap[i] for i in p.vertices) for p in keep]
    me=bpy.data.meshes.new('Robe_tailored_surface')
    me.from_pydata(verts,[],faces); me.update()
    loops=boundary_loops(me)
    info=[{'n':len(loop),'center':list(sum((me.vertices[i].co for i in loop),Vector())/len(loop))} for loop in loops]
    print('ROBE_BOUNDARIES',json.dumps(info))
    assert len(loops)==4, 'Expected neckline, two cuffs and waist'
    waist=min(loops,key=lambda loop: sum(me.vertices[i].co.z for i in loop)/len(loop))
    waist=sorted(waist,key=lambda i:math.atan2(me.vertices[i].co.x,-me.vertices[i].co.y))
    # Use a regular circular order to extend the lower opening to the ankles.
    for i in waist:
        co=Vector(verts[i]); co.z=waist_z; verts[i]=tuple(co)
    previous=waist
    for z,rx,ry in [(waist_z-.09,.184,.146),(.63,.210,.153),(.42,.242,.169),(.20,.274,.184),(.155,.278,.186)]:
        ring=[]
        for j,i in enumerate(waist):
            a=math.atan2(verts[i][0],-verts[i][1])
            # Small broad folds, no high-frequency ruffles or grime.
            fold=1 + .024*math.cos(6*a)
            co=(rx*math.sin(a)*fold,-ry*math.cos(a)*fold,z)
            ring.append(len(verts)); verts.append(co)
            ws.append(skirt_weights(*co,waist_z))
        for j in range(len(ring)):
            k=(j+1)%len(ring)
            faces.append((previous[j],previous[k],ring[k],ring[j]))
        previous=ring
    bpy.data.meshes.remove(me)
    me=bpy.data.meshes.new('Robe_continuous_sleeves_torso_skirt')
    me.from_pydata(verts,[],faces); me.update()
    ob=bpy.data.objects.new('Robe',me);scene.collection.objects.link(ob)
    set_weights(ob,ws)
    # Recalculate connected surface winding after constructing the skirt.
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
    for p in me.polygons:p.use_smooth=True
    me.materials.append(clothmat)
    ob['construction']='one continuous cloth surface; neck/cuffs/hem are intended openings'
    return ob

robe=make_robe()
# Six paintable UV panels: front/back body + front/back of each sleeve.
weights=vertex_weights(robe)
regions=[]
for p in robe.data.polygons:
    c=sum((robe.data.vertices[i].co for i in p.vertices),Vector())/len(p.vertices)
    arm_weight=sum(sum(w for n,w in weights[i].items() if n.startswith(('upper_arm.','forearm.','hand.'))) for i in p.vertices)/len(p.vertices)
    if arm_weight>.45:
        side='L' if c.x>0 else 'R'
        a=rig.data.bones['upper_arm.'+side].head_local
        b=rig.data.bones['forearm.'+side].tail_local
        t=max(0,min(1,(c-a).dot(b-a)/(b-a).length_squared))
        axis=a.lerp(b,t)
        regions.append(side+('_front' if c.y<axis.y else '_back'))
    else:
        regions.append('body_front' if c.y<0 else 'body_back')
edge_faces={}
for p in robe.data.polygons:
    for key in p.edge_keys:edge_faces.setdefault(tuple(sorted(key)),[]).append(p.index)
for e in robe.data.edges:
    ps=edge_faces.get(tuple(sorted(e.vertices)),[])
    e.use_seam=len(ps)==2 and regions[ps[0]]!=regions[ps[1]]
select_only(robe)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.unwrap(method='ANGLE_BASED',margin=.025)
bpy.ops.uv.pack_islands(rotate=True,margin=.025)
bpy.ops.object.mode_set(mode='OBJECT')
arm=robe.modifiers.new('Skin','ARMATURE');arm.object=rig
solid=robe.modifiers.new('Hem_and_cuff_thickness','SOLIDIFY');solid.thickness=.004;solid.offset=-.2

parts=[body,robe]
try:
    from make_hair import build_hair
except ImportError:
    print('HAIR_MODULE_PENDING')
else:
    parts.extend(build_hair(body,rig,scene.collection,hairmat))

for ob in parts:
    ob['asset_part']=True
scene['status']='Static visual candidate plus diagnostic poses; not animation master approval'
scene['height_m']=1.65

def set_pose(kind):
    for pb in rig.pose.bones:pb.matrix_basis.identity()
    # World-Z rotations close the upper arms from the A-pose to a relaxed stance.
    for side,sgn in [('L',1),('R',-1)]:
        pb=rig.pose.bones['upper_arm.'+side]
        b=pb.bone
        q=Matrix.Rotation(math.radians(-sgn*32),4,'Y')
        # A arm vector has +X/-Z on L: +Y brings it inward.
        q=Matrix.Rotation(math.radians(sgn*32),4,'Y')
        pb.matrix=Matrix.Translation(b.head_local)@q@Matrix.Translation(-b.head_local)@b.matrix_local
    bpy.context.view_layer.update()

def setup_render():
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=1000;scene.render.resolution_y=1000
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX'
    world=bpy.data.worlds.new('Studio');world.use_nodes=True
    world.node_tree.nodes['Background'].inputs[0].default_value=(.105,.13,.16,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.6;scene.world=world
    for name,loc,power,size in [('Key',(-3,-4,5),450,4),('Fill',(4,-2,3),180,4),('Rim',(1,3,4),350,3)]:
        ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size
        lo=bpy.data.objects.new(name,ld);scene.collection.objects.link(lo);lo.location=loc
        lo.rotation_euler=(Vector((0,0,.9))-lo.location).to_track_quat('-Z','Y').to_euler()
    cd=bpy.data.cameras.new('Camera');cd.type='ORTHO';cd.ortho_scale=1.97
    cam=bpy.data.objects.new('Camera',cd);scene.collection.objects.link(cam);scene.camera=cam
    return cam

cam=setup_render()
set_pose('relaxed')
cam.location=(2.8,-6,2.15);cam.rotation_euler=(Vector((0,0,.86))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(ROOT/'evidence/01_character.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'player_character_v3.blend'))
if '--skip-render' not in sys.argv:bpy.ops.render.render(write_still=True)
print('BUILT',len(parts),'parts; body bounds',mesh_world_bounds(body))
