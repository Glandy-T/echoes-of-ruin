"""Reproducible post-repair validation for the compact v2.1 body blend."""
import bpy, json, math
from collections import defaultdict
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
TARGET=ROOT/'body_165cm_validated_v2_1.blend'
BODY='Body_165cm_CC0_pistachio';RIG='Body_Rig_original';EPS=1e-9

def signed_area(p): return .5*sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p)))
def clip(subject,clipper):
    out=subject
    for i,a in enumerate(clipper):
        b=clipper[(i+1)%len(clipper)]; inp=out;out=[]
        if not inp:break
        inside=lambda q:(b[0]-a[0])*(q[1]-a[1])-(b[1]-a[1])*(q[0]-a[0])>=-EPS
        def hit(p,q):
            rx,ry=q[0]-p[0],q[1]-p[1];sx,sy=b[0]-a[0],b[1]-a[1];d=rx*sy-ry*sx
            if abs(d)<EPS:return q
            t=((a[0]-p[0])*sy-(a[1]-p[1])*sx)/d;return (p[0]+t*rx,p[1]+t*ry)
        prev=inp[-1];pin=inside(prev)
        for cur in inp:
            cin=inside(cur)
            if cin != pin:out.append(hit(prev,cur))
            if cin:out.append(cur)
            prev,pin=cur,cin
    return out

def uv_report(ob):
    me=ob.data;uv=me.uv_layers.active;me.calc_loop_triangles();tris=[];groups=defaultdict(list);zero=[];outside=[]
    for i,t in enumerate(me.loop_triangles):
        p=[tuple(uv.data[x].uv) for x in t.loops];sa=signed_area(p);a=abs(sa)
        if a<EPS:zero.append(i)
        if any(x<0-EPS or x>1+EPS or y<0-EPS or y>1+EPS for x,y in p):outside.append(i)
        groups[tuple(sorted((round(x,7),round(y,7)) for x,y in p))].append(i)
        if sa<0:p=[p[0],p[2],p[1]]
        xs=[x for x,y in p];ys=[y for x,y in p]
        world=[ob.matrix_world@me.vertices[x].co for x in t.vertices]
        tris.append({'uv':p,'box':(min(xs),min(ys),max(xs),max(ys)),'area':a,'vertices':list(t.vertices),'center':[sum(v[j] for v in world)/3 for j in range(3)]})
    grid=defaultdict(list)
    for i,t in enumerate(tris):
        x0,y0,x1,y1=t['box']
        for y in range(max(0,int(y0*32)),min(31,int(y1*32))+1):
            for x in range(max(0,int(x0*32)),min(31,int(x1*32))+1):grid[x,y].append(i)
    pairs=set()
    for vals in grid.values():
        for i,a in enumerate(vals):
            for b in vals[i+1:]:pairs.add((a,b) if a<b else (b,a))
    hits=[]
    for a,b in pairs:
        A,B=tris[a],tris[b];ba,bb=A['box'],B['box']
        if ba[2]<bb[0] or bb[2]<ba[0] or ba[3]<bb[1] or bb[3]<ba[1]:continue
        hit=abs(signed_area(clip(A['uv'],B['uv'])))
        if hit>EPS and hit<min(A['area'],B['area'])*.999999:
            shared=sorted(set(A['vertices'])&set(B['vertices']))
            dist=math.dist(A['center'],B['center'])
            hits.append({'triangles':[a,b],'uv_area':hit,'shared_mesh_vertices':shared,'world_center_distance_m':dist,
                         'world_centers_m':[A['center'],B['center']]})
    hits.sort(key=lambda h:-h['uv_area'])
    separate=[h for h in hits if not h['shared_mesh_vertices']]
    # Distances below two millimetres with a shared vertex are numerical/adjacent-seam candidates.
    material=[h for h in hits if not h['shared_mesh_vertices'] and h['uv_area']>=1e-7]
    return {'layer':uv.name,'zero_area_triangles':len(zero),'outside_0_1_triangles':len(outside),
      'exact_uv_stack_groups':sum(len(v)>1 for v in groups.values()),'partial_overlap_pairs':len(hits),
      'partial_overlap_total_uv_area':sum(h['uv_area'] for h in hits),'nonadjacent_partial_overlap_pairs':len(separate),
      'nonadjacent_material_overlap_pairs_over_1e_7':len(material),'largest_partial_overlaps':hits[:16],
      'verdict':'TBD: non-adjacent UV overlap exists; preserve UV for now and repair before final body pixel texture painting.' if material else 'No material non-adjacent partial overlap found.'}

def rig_report(ob,rig):
    bones={b.name for b in rig.data.bones if b.use_deform};hist=[];unweighted=[];bad=[]
    for v in ob.data.vertices:
        vals=[g.weight for g in v.groups if ob.vertex_groups[g.group].name in bones and g.weight>0];hist.append(len(vals))
        if not vals:unweighted.append(v.index)
        if len(vals)>4 or abs(sum(vals)-1)>1e-5:bad.append({'vertex':v.index,'influences':len(vals),'sum':sum(vals)})
    return {'bone_count':len(rig.data.bones),'roots':[b.name for b in rig.data.bones if not b.parent],
      'non_bone_vertex_groups':[g.name for g in ob.vertex_groups if g.name not in bones], 'unweighted_vertices':len(unweighted),
      'max_influences':max(hist),'over_4_or_not_normalized':len(bad),'samples':bad[:20]}

def look(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
def bone_axes(rig,names):
    output={}
    for name in names:
        matrix=rig.data.bones[name].matrix_local.to_3x3()
        output[name]={axis:[round(value,6) for value in matrix @ Vector(vector)] for axis,vector in {'X':(1,0,0),'Y':(0,1,0),'Z':(0,0,1)}.items()}
    return output

def pose(rig,name):
    bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='POSE')
    for b in rig.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0)
    commanded={}
    if name=='shoulder_elbow':
        # Y follows the arm and only twists it. Z is near fore/back and creates an actual hinge/elevation.
        rig.pose.bones['upper_arm.L'].rotation_euler.z=math.radians(42);rig.pose.bones['upper_arm.R'].rotation_euler.z=math.radians(-42)
        rig.pose.bones['forearm.L'].rotation_euler.z=math.radians(68);rig.pose.bones['forearm.R'].rotation_euler.z=math.radians(-68)
        commanded={'upper_arm.L':{'axis':'Z','degrees':42},'upper_arm.R':{'axis':'Z','degrees':-42},'forearm.L':{'axis':'Z','degrees':68},'forearm.R':{'axis':'Z','degrees':-68}}
    elif name=='hip_knee':
        # X is near left/right and perpendicular to the legs; it produces a knee/hip hinge.
        rig.pose.bones['thigh.L'].rotation_euler.x=math.radians(-28);rig.pose.bones['thigh.R'].rotation_euler.x=math.radians(22);rig.pose.bones['shin.L'].rotation_euler.x=math.radians(52);rig.pose.bones['shin.R'].rotation_euler.x=math.radians(-48)
        commanded={'thigh.L':{'axis':'X','degrees':-28},'thigh.R':{'axis':'X','degrees':22},'shin.L':{'axis':'X','degrees':52},'shin.R':{'axis':'X','degrees':-48}}
    bpy.ops.object.mode_set(mode='OBJECT');rig.select_set(False);bpy.context.view_layer.update()
    details={}
    for bone_name,setting in commanded.items():
        rest=rig.data.bones[bone_name]; posed=rig.pose.bones[bone_name]
        rest_head=rig.matrix_world @ rest.head_local;rest_tail=rig.matrix_world @ rest.tail_local
        pose_head=rig.matrix_world @ posed.head;pose_tail=rig.matrix_world @ posed.tail
        details[bone_name]={**setting,'actual_euler_degrees':[round(math.degrees(value),3) for value in posed.rotation_euler],
          'head_displacement_m':[round(value,6) for value in pose_head-rest_head],'tail_displacement_m':[round(value,6) for value in pose_tail-rest_tail]}
    return details
def render_pose(ob,rig,name):
    sc=bpy.context.scene;details=pose(rig,name)
    for x in sc.objects:x.hide_render=x not in {ob,rig}
    m=bpy.data.materials.new('AUDIT_MAT');m.diffuse_color=(.62,.71,.78,1);ob.data.materials.clear();ob.data.materials.append(m)
    cd=bpy.data.cameras.new('AUDIT_CAMERA');cd.type='ORTHO';cd.ortho_scale=2.1;c=bpy.data.objects.new('AUDIT_CAMERA',cd);c.location=(3.2,-6,1.05);look(c,(0,0,.85));sc.collection.objects.link(c);sc.camera=c
    for i,(loc,e) in enumerate([((-3,-4,4),800),((4,-2,2),350),((0,3,3),250)]):
        ld=bpy.data.lights.new('AUDIT_LIGHT'+str(i),'AREA');ld.energy=e;ld.size=4;l=bpy.data.objects.new(ld.name,ld);l.location=loc;look(l,(0,0,.8));sc.collection.objects.link(l)
    sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.render.resolution_x=700;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.filepath=str(ROOT/('pose_'+name+'.png'));bpy.ops.render.render(write_still=True)
    for x in [x for x in list(sc.objects) if x.name.startswith('AUDIT_')]:bpy.data.objects.remove(x,do_unlink=True)
    return details

bpy.ops.wm.open_mainfile(filepath=str(TARGET),use_scripts=False)
body=bpy.data.objects[BODY];rig=bpy.data.objects[RIG]
pose_bones=['upper_arm.L','forearm.L','upper_arm.R','forearm.R','thigh.L','shin.L','thigh.R','shin.R']
report={'source':str(TARGET),'blender_version':bpy.app.version_string,'shape_key_Key_1_value':body.data.shape_keys.key_blocks['Key 1'].value,'uv':uv_report(body),'rig':rig_report(body,rig),'local_bone_axes_in_armature_space':bone_axes(rig,pose_bones),'poses':{}}
for name in ['rest','shoulder_elbow','hip_knee']:report['poses'][name]=render_pose(body,rig,name)
(ROOT/'validation_report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))
