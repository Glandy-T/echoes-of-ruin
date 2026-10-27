"""Read-only UV, rig, and deformation audit. Outputs stay in this directory."""
import bpy, json, math
from collections import defaultdict
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent
SRC=OUT.parents[1]/'player_basemesh_v2'/'body_165cm_review_v2.blend'
BODY='Body_165cm_CC0_pistachio'; RIG='Body_Rig_original'; EPS=1e-9

def area(p):
    return .5*sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p)))

def clip(subject, clipper):
    out=subject
    for i,a in enumerate(clipper):
        b=clipper[(i+1)%len(clipper)]; inp=out; out=[]
        if not inp: break
        def inside(q): return (b[0]-a[0])*(q[1]-a[1])-(b[1]-a[1])*(q[0]-a[0]) >= -EPS
        def hit(p,q):
            rx,ry=q[0]-p[0],q[1]-p[1]; sx,sy=b[0]-a[0],b[1]-a[1]; d=rx*sy-ry*sx
            if abs(d)<EPS: return q
            t=((a[0]-p[0])*sy-(a[1]-p[1])*sx)/d; return (p[0]+t*rx,p[1]+t*ry)
        prev=inp[-1]; pi=inside(prev)
        for cur in inp:
            ci=inside(cur)
            if ci != pi: out.append(hit(prev,cur))
            if ci: out.append(cur)
            prev,pi=cur,ci
    return out

def uv_audit(ob):
    me=ob.data; uv=me.uv_layers.active; me.calc_loop_triangles()
    tris=[]; zero=[]; outside=[]; dens=[]; stacks=defaultdict(list)
    for n,t in enumerate(me.loop_triangles):
        p=[tuple(uv.data[i].uv) for i in t.loops]; sa=area(p); ua=abs(sa)
        if ua<EPS: zero.append(n)
        if any(x<0-EPS or x>1+EPS or y<0-EPS or y>1+EPS for x,y in p): outside.append(n)
        p3=[me.vertices[i].co for i in t.vertices]; a3=.5*((p3[1]-p3[0]).cross(p3[2]-p3[0])).length
        if a3>EPS and ua>EPS: dens.append(ua/a3)
        stacks[tuple(sorted((round(x,7),round(y,7)) for x,y in p))].append((n,1 if sa>=0 else -1))
        if sa<0:p=[p[0],p[2],p[1]]
        xs=[q[0] for q in p]; ys=[q[1] for q in p]
        tris.append((p,(min(xs),min(ys),max(xs),max(ys)),ua))
    groups=[v for v in stacks.values() if len(v)>1]
    # Partial overlap test, not counting exact stacks; broad phase is 32x32 bins.
    grid=defaultdict(list)
    for i,(_,b,_) in enumerate(tris):
        for y in range(max(0,int(math.floor(b[1]*32))),min(31,int(math.floor(b[3]*32)))+1):
            for x in range(max(0,int(math.floor(b[0]*32))),min(31,int(math.floor(b[2]*32)))+1): grid[x,y].append(i)
    pairs=set()
    for vals in grid.values():
        for i,a in enumerate(vals):
            for b in vals[i+1:]: pairs.add((a,b) if a<b else (b,a))
    partial=[]
    for a,b in pairs:
        pa,ba,aa=tris[a]; pb,bb,ab=tris[b]
        if ba[2]<bb[0] or bb[2]<ba[0] or ba[3]<bb[1] or bb[3]<ba[1]: continue
        inter=abs(area(clip(pa,pb)))
        if inter>EPS and inter<min(aa,ab)*.999999:
            partial.append({'triangles':[a,b],'uv_overlap_area':inter})
    dens.sort(); q=lambda f: dens[min(len(dens)-1,int(len(dens)*f))] if dens else None
    return {'layer':uv.name,'triangles':len(tris),'zero_area_triangles':len(zero),'zero_area_samples':zero[:20],
      'outside_0_1_triangles':len(outside),'outside_samples':outside[:20],
      'identical_uv_stack_groups':len(groups),'identical_uv_stack_pairs':sum(len(v)*(len(v)-1)//2 for v in groups),
      'opposite_winding_exact_pairs_likely_mirrors':sum(sum(1 for i,x in enumerate(v) for y in v[i+1:] if x[1]!=y[1]) for v in groups),
      'partial_non_identical_overlap_pairs':len(partial),'partial_overlap_samples':partial[:12],
      'uv_to_object_area_ratio':{'min':q(0),'median':q(.5),'p95':q(.95),'max':q(1)}}

def rig_audit(ob,rig):
    bones={b.name:b for b in rig.data.bones if b.use_deform}; counts={g.name:0 for g in ob.vertex_groups}
    infl=[]; empty=[]; over4=[]; under=[]; over=[]
    for v in ob.data.vertices:
        w=[]
        for x in v.groups:
            name=ob.vertex_groups[x.group].name
            if x.weight>EPS:
                counts[name]+=1
                if name in bones:w.append(x.weight)
        s=sum(w); infl.append(len(w))
        if not w: empty.append(v.index)
        if len(w)>4:over4.append(v.index)
        if w and s<.999:under.append({'vertex':v.index,'sum':s})
        if w and s>1.001:over.append({'vertex':v.index,'sum':s})
    gaps=[]
    for b in rig.data.bones:
        if b.parent:
            gap=(b.head_local-b.parent.tail_local).length
            if gap>1e-4:gaps.append({'bone':b.name,'gap':gap})
    return {'bone_count':len(rig.data.bones),'deform_bone_count':len(bones),'roots':[b.name for b in rig.data.bones if not b.parent],
      'missing_deform_bone_for_vertex_group':[g.name for g in ob.vertex_groups if g.name not in bones],
      'vertex_groups_with_nonzero_assignments':{n:c for n,c in counts.items() if c},
      'unweighted_vertices':len(empty),'unweighted_samples':empty[:20],
      'influences_per_vertex':{'min':min(infl),'max':max(infl),'mean':sum(infl)/len(infl),'over_four':len(over4),'over_four_samples':over4[:20]},
      'under_normalized':len(under),'under_normalized_samples':under[:10],'over_normalized':len(over),'over_normalized_samples':over[:10],
      'unconnected_child_bones':gaps,'constraints':{b.name:len(b.constraints) for b in rig.pose.bones if b.constraints}}

def look(obj,target): obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def uv_render(ob):
    sc=bpy.data.scenes.new('AUDIT_UV'); sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.light='FLAT'; sc.display.shading.color_type='MATERIAL'
    sc.render.resolution_x=sc.render.resolution_y=1024;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.filepath=str(OUT/'uv_layout.png')
    verts=[];faces=[];uv=ob.data.uv_layers.active
    for p in ob.data.polygons:
        f=[]
        for l in p.loop_indices:
            u=uv.data[l].uv; f.append(len(verts));verts.append((u.x-.5,u.y-.5,0))
        faces.append(f)
    me=bpy.data.meshes.new('AUDIT_UV');me.from_pydata(verts,[],faces);o=bpy.data.objects.new('AUDIT_UV',me);sc.collection.objects.link(o)
    m=bpy.data.materials.new('AUDIT_UV_FACE');m.diffuse_color=(.4,.72,.9,1);me.materials.append(m)
    wire=bpy.data.materials.new('AUDIT_UV_WIRE');wire.diffuse_color=(.015,.025,.04,1);me.materials.append(wire)
    mod=o.modifiers.new('AUDIT_UV_WIREFRAME','WIREFRAME');mod.thickness=.0015;mod.material_offset=1
    cd=bpy.data.cameras.new('AUDIT_UV');cd.type='ORTHO';cd.ortho_scale=1.1;c=bpy.data.objects.new('AUDIT_UV',cd);c.location=(0,0,2);sc.collection.objects.link(c);sc.camera=c
    bpy.context.window.scene=sc;bpy.ops.render.render(write_still=True);bpy.data.scenes.remove(sc,do_unlink=True)

def set_pose(rig,name):
    bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='POSE')
    for b in rig.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
    if name=='shoulder_elbow':
        rig.pose.bones['upper_arm.L'].rotation_euler.y=math.radians(-38);rig.pose.bones['upper_arm.R'].rotation_euler.y=math.radians(38)
        rig.pose.bones['forearm.L'].rotation_euler.y=math.radians(-52);rig.pose.bones['forearm.R'].rotation_euler.y=math.radians(52)
    if name=='hip_knee':
        rig.pose.bones['thigh.L'].rotation_euler.x=math.radians(-28);rig.pose.bones['thigh.R'].rotation_euler.x=math.radians(22)
        rig.pose.bones['shin.L'].rotation_euler.x=math.radians(52);rig.pose.bones['shin.R'].rotation_euler.x=math.radians(-48)
    bpy.ops.object.mode_set(mode='OBJECT');rig.select_set(False);bpy.context.view_layer.update()

def evaluated_dims(ob):
    e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());vs=[e.matrix_world@v.co for v in e.data.vertices]
    return [round(max(v[i] for v in vs)-min(v[i] for v in vs),6) for i in range(3)]

def checker_material():
    m=bpy.data.materials.new('AUDIT_UV_CHECKER');m.use_nodes=True;n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');tex=n.new('ShaderNodeTexChecker');coord=n.new('ShaderNodeTexCoord')
    tex.inputs['Scale'].default_value=12;m.node_tree.links.new(coord.outputs['UV'],tex.inputs['Vector']);m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);m.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface']);return m

def pose_render(ob,rig,name,checker=False):
    sc=bpy.data.scenes['01_BODY_MASTER_165cm'];bpy.context.window.scene=sc
    for x in sc.objects:x.hide_render=x not in {ob,rig}
    m=checker_material() if checker else (bpy.data.materials.get('AUDIT_BODY') or bpy.data.materials.new('AUDIT_BODY'));m.diffuse_color=(.62,.71,.78,1)
    if ob.data.materials:ob.data.materials[0]=m
    else:ob.data.materials.append(m)
    set_pose(rig,name)
    cd=bpy.data.cameras.new('AUDIT_CAM_'+name);cd.type='ORTHO';cd.ortho_scale=2.1;c=bpy.data.objects.new(cd.name,cd);c.location=(3.2,-6,1.05);look(c,(0,0,.85));sc.collection.objects.link(c);sc.camera=c
    for i,(loc,en) in enumerate([((-3,-4,4),800),((4,-2,2),350),((0,3,3),250)]):
        ld=bpy.data.lights.new('AUDIT_L'+str(i),'AREA');ld.energy=en;ld.shape='DISK';ld.size=4;l=bpy.data.objects.new(ld.name,ld);l.location=loc;look(l,(0,0,.8));sc.collection.objects.link(l)
    sc.render.engine='BLENDER_EEVEE' if checker else 'BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True
    sc.render.resolution_x=700;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.filepath=str(OUT/('pose_'+name+'.png'));bpy.ops.render.render(write_still=True)
    d=evaluated_dims(ob)
    for x in [x for x in list(sc.objects) if x.name.startswith('AUDIT_')]:bpy.data.objects.remove(x,do_unlink=True)
    return d

bpy.ops.wm.open_mainfile(filepath=str(SRC),use_scripts=False)
body=bpy.data.objects[BODY];rig=bpy.data.objects[RIG]
report={'source':str(SRC),'blender_version':bpy.app.version_string,'target_scene':'01_BODY_MASTER_165cm','target_body':BODY,'target_rig':RIG,
 'base_mesh':{'vertices':len(body.data.vertices),'triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'shape_key_Key_1_value':body.data.shape_keys.key_blocks['Key 1'].value,'raw_object_dimensions_m':[round(v,6) for v in body.dimensions]},'uv':uv_audit(body),'rig':rig_audit(body,rig)}
uv_render(body);report['evaluated_dimensions_m']={}
for preset in ['rest','shoulder_elbow','hip_knee']:report['evaluated_dimensions_m'][preset]=pose_render(body,rig,preset)
set_pose(rig,'rest'); pose_render(body,rig,'uv_checker_rest',checker=True)
(OUT/'audit_report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))
