"""Source-based editable rig trial. Blender 5.0; no baked animation or cloth simulation."""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from assemble_character import render

def clamp(v):return max(0,min(1,v))
def write_weights(obj,values,rig):
    obj.vertex_groups.clear()
    groups={n:obj.vertex_groups.new(name=n) for n in sorted({n for row in values for n in row})}
    for i,row in enumerate(values):
        row=sorted(((n,w) for n,w in row.items() if w>1e-6),key=lambda q:-q[1])[:4]
        total=sum(w for n,w in row)
        for n,w in row:groups[n].add([i],w/total,'REPLACE')
    world=obj.matrix_world.copy();obj.parent=rig;obj.matrix_world=world
    mod=obj.modifiers.new('Character skeleton','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=False

def interpolation(z,centers,names):
    if z>=centers[0]:return {names[0]:1.0}
    if z<=centers[-1]:return {names[-1]:1.0}
    for i in range(len(centers)-1):
        if centers[i]>=z>=centers[i+1]:
            t=(centers[i]-z)/(centers[i]-centers[i+1]);return {names[i]:1-t,names[i+1]:t}

def reset(rig):
    for b in rig.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
    bpy.context.view_layer.update()

def set_pose(rig,pose):
    reset(rig)
    for name,axis,deg in pose:rig.pose.bones[name].rotation_euler['XYZ'.index(axis)]=math.radians(deg)
    bpy.context.view_layer.update()

def main():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'character_fitting_draft_v5.blend'),use_scripts=False)
    bpy.context.preferences.filepaths.save_version=0
    scene=bpy.context.scene;body=bpy.data.objects['Body_165cm_CC0_pistachio'];rig=bpy.data.objects['Body_Rig_original'];robe=bpy.data.objects['Robe_White_Fitted']
    hairs=[bpy.data.objects[n] for n in ('Hair_Back_Fitted','Hair_Front.L','Hair_Front.R')]
    # All additional bone coordinates are specified in metres, then transformed
    # into the existing armature's local coordinates (its source scale is retained).
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
    bpy.ops.object.mode_set(mode='EDIT');inv=rig.matrix_world.inverted();added=[]
    def bone(name,a,b,parent):
        e=rig.data.edit_bones.new(name);e.head=inv@Vector(a);e.tail=inv@Vector(b);e.parent=rig.data.edit_bones[parent];e.use_connect=False;added.append(name)
    back=[(0,.17,1.46),(0,.18,1.22),(0,.185,1.02),(0,.22,.82)]
    for i in range(3):bone('hair_back.%02d'%(i+1),back[i],back[i+1],'head' if i==0 else 'hair_back.%02d'%i)
    for side,s in [('L',1),('R',-1)]:
        chain=[(s*.082,-.045,1.54),(s*.082,-.072,1.39),(s*.074,-.123,1.285)]
        for i in range(2):bone('hair_front.%02d.%s'%(i+1,side),chain[i],chain[i+1],'head' if i==0 else 'hair_front.01.'+side)
    directions=[('F',(0,-1)),('L',(1,0)),('B',(0,1)),('R',(-1,0))]
    for name,(dx,dy) in directions:
        a=(dx*.15,dy*.125,.93);b=(dx*.22,dy*.15,.54);c=(dx*.28,dy*.16,.18)
        bone('skirt.01.'+name,a,b,'hips');bone('skirt.02.'+name,b,c,'skirt.01.'+name)
    bpy.ops.object.mode_set(mode='OBJECT')
    # Barycentric transfer of the original body's rig weights to the robe torso/sleeves.
    coords=[body.matrix_world@v.co for v in body.data.shape_keys.key_blocks['Key 1'].data]
    body.data.calc_loop_triangles();triangles=[tuple(t.vertices) for t in body.data.loop_triangles]
    tree=BVHTree.FromPolygons(coords,triangles,all_triangles=True)
    deform={b.name for b in rig.data.bones if b.use_deform}
    source_weights=[{body.vertex_groups[g.group].name:g.weight for g in v.groups if body.vertex_groups[g.group].name in deform} for v in body.data.vertices]
    def skin_weight(p):
        q,n,index,d=tree.find_nearest(p);ids=triangles[index];a,b,c=[coords[i] for i in ids];u=b-a;v=c-a;w=q-a
        det=u.dot(u)*v.dot(v)-u.dot(v)**2
        s=(w.dot(u)*v.dot(v)-w.dot(v)*u.dot(v))/det;t=(w.dot(v)*u.dot(u)-w.dot(u)*u.dot(v))/det
        bs=[max(0,1-s-t),max(0,s),max(0,t)];result={}
        for i,factor in zip(ids,bs):
            for name,weight in source_weights[i].items():result[name]=result.get(name,0)+factor*weight
        return result
    robe_weights=[]
    for vert in robe.data.vertices:
        p=robe.matrix_world@vert.co
        if p.z>=1.00:row=skin_weight(p)
        elif p.z>=.87:
            t=clamp((p.z-.87)/.13);row={n:w*t for n,w in skin_weight(p).items()};row['hips']=row.get('hips',0)+(1-t)
        else:
            # Four skirt sectors with two controls each; independent from the legs.
            angle=(math.atan2(p.x,-p.y)%(2*math.pi))/(math.pi/2);i=int(angle)%4;t=angle-int(angle)
            row={}
            for sector,factor in [(directions[i][0],1-t),(directions[(i+1)%4][0],t)]:
                for n,w in interpolation(p.z,[.88,.70,.30],['hips','skirt.01.'+sector,'skirt.02.'+sector]).items():row[n]=row.get(n,0)+factor*w
        robe_weights.append(row)
    write_weights(robe,robe_weights,rig)
    for hair in hairs:
        rows=[]
        for v in hair.data.vertices:
            if 'Back' in hair.name:row=interpolation(v.co.z,[1.48,1.36,1.13,.86],['head','hair_back.01','hair_back.02','hair_back.03'])
            else:
                side=hair.name[-1];row=interpolation(v.co.z,[1.54,1.465,1.32],['head','hair_front.01.'+side,'hair_front.02.'+side])
            rows.append(row)
        write_weights(hair,rows,rig)
    scene['validation_scope']='Bounded pose trial only. Skirt/hair have hand-keyable chains, no physics or finished walk cycle.'
    rig['added_controls']='7 hair + 8 skirt deform bones; original 59 body bones retained.'
    rig.show_in_front=True
    for o in [body,robe,*hairs]:o['separate_editable_mesh']=True
    poses={
      '10_rig_rest':[],
      '11_rig_arms':[('upper_arm.L','Z',42),('upper_arm.R','Z',-42),('forearm.L','Z',68),('forearm.R','Z',-68)],
      '12_rig_step':[('thigh.L','X',-22),('thigh.R','X',16),('shin.L','X',32),('shin.R','X',-22),('skirt.01.F','X',-14),('skirt.01.B','X',-8),('skirt.02.F','X',8)],
      '13_rig_head_hair':[('head','Y',18),('hair_back.01','X',-8),('hair_front.01.L','X',8),('hair_front.01.R','X',8)],
      '14_rig_crouch':[('thigh.L','X',-40),('thigh.R','X',-40),('shin.L','X',55),('shin.R','X',55),('spine','X',15),('skirt.01.F','X',-28),('skirt.01.B','X',-28),('skirt.01.L','X',-28),('skirt.01.R','X',-28)],
    }
    for name,pose in poses.items():
        set_pose(rig,pose);render(scene,name+'.png',(2,-5,2))
    set_pose(rig,[]);render(scene,'15_rig_side.png',(5,0,1.1))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'character_rig_trial_v5.blend'))
    report={'original_body_bones':59,'added_bones':added,'total_bones':len(rig.data.bones),'pose_commands_degrees':poses,'scope':'Manual deform controls; no physics or approved animation. Meshes and UVs separate. Wardrobe body mask reversible.'}
    (ROOT/'rig_trial_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
if __name__=='__main__':main()
