"""Editable source-based character fitting study, Blender 5.0."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
BODY=ROOT/'body/body_uv_ready_v5.blend'
HAIR=WORK/'player_hair_source_v4/hair_front_locks_v4.blend'
ROBE=ROOT/'robe/robe_reduced_study_v5.blend'

def append(path,names):
    with bpy.data.libraries.load(str(path),link=False) as (src,dst):dst.objects=names
    for obj in dst.objects:
        bpy.context.scene.collection.objects.link(obj);obj.hide_set(False);obj.hide_render=False
    return dst.objects

def material(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1)
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.95
    return m

def render(scene,name,pos,target=(0,0,.84),scale=1.95):
    scene.camera.location=pos;scene.camera.rotation_euler=(Vector(target)-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=scale
    scene.render.filepath=str(ROOT/name);bpy.ops.render.render(write_still=True)

def main():
    bpy.ops.wm.open_mainfile(filepath=str(BODY),use_scripts=False)
    bpy.context.preferences.filepaths.save_version=0
    scene=bpy.context.scene;scene.name='CHARACTER_ASSEMBLED_V5_REVIEW'
    body=bpy.data.objects['Body_165cm_CC0_pistachio'];rig=bpy.data.objects['Body_Rig_original']
    for o in list(bpy.data.objects):
        if o not in (body,rig):bpy.data.objects.remove(o,do_unlink=True)
    robe=append(ROBE,['Robe_Reduced_Study'])[0];robe.name='Robe_White_Fitted'
    hairs=append(HAIR,['Hair_Back_SOURCE_UNCHANGED','Hair_Front.L','Hair_Front.R'])
    # Fit with distinct component transforms; keep original source copies in their own files.
    for v in robe.data.vertices:
        v.co.x*=.94;v.co.y=v.co.y*1.20-.015;v.co.z=v.co.z*.90+.005
        # Source cuffs sit behind this body's A-pose wrists. Sweep sleeves forward.
        sleeve=max(0,min(1,(abs(v.co.x)-.15)/.32))
        if v.co.z> .87:v.co.y-=.16*sleeve
        waist=math.exp(-((v.co.z-.97)/.17)**2)
        v.co.x*=1+.12*waist
        if v.co.z<.83:
            t=min(1,(.83-v.co.z)/.65);v.co.x*=1+.36*t
    bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get();evaluated=body.evaluated_get(deps);mesh=evaluated.to_mesh()
    verts=[body.matrix_world@v.co for v in mesh.vertices];faces=[tuple(p.vertices) for p in mesh.polygons]
    tree=BVHTree.FromPolygons(verts,faces)
    nudged=0
    for v in robe.data.vertices:
        near,normal,index,distance=tree.find_nearest(v.co)
        if abs(v.co.x)<.175 and distance<.12 and (v.co-near).dot(normal)<.018 and v.co.z>.70:
            v.co=near+normal*.018;nudged+=1
    # Smooth capsule clearance for sleeves, using actual source rig arm centers.
    for v in robe.data.vertices:
        if abs(v.co.x)<.175 or v.co.z<.88:continue
        side='L' if v.co.x>0 else 'R'
        nearest=None
        for bn in ('upper_arm.','forearm.'):
            bone=rig.data.bones[bn+side];a=rig.matrix_world@bone.head_local;b=rig.matrix_world@bone.tail_local
            t=max(0,min(1,(v.co-a).dot(b-a)/(b-a).length_squared));q=a+t*(b-a);r=v.co-q
            if nearest is None or r.length<nearest[0]:nearest=(r.length,q,r,bn,t)
        length,q,r,bn,t=nearest
        radius=(.086-.012*t) if bn=='upper_arm.' else (.074-.017*t)
        if 1e-6<length<radius:v.co=q+r.normalized()*radius
    evaluated.to_mesh_clear()
    robe.data.update()
    for hair in hairs:
        hair.name=hair.name.replace('SOURCE_UNCHANGED','Fitted')
        for v in hair.data.vertices:
            p=v.co.copy();v.co=(p.x,p.y,p.z+.20)
            head_weight=max(0,min(1,(p.z-1.22)/.12))
            v.co.x*=1+.06*head_weight
            v.co.z+=.12*(p.z-1.35)*head_weight
            if 'Front' in hair.name:
                t=max(0,min(1,(1.375-p.z)/.288));t=t*t*(3-2*t)
                v.co.y-=.04+.03*t
            else:
                v.co.y+=head_weight*(.35*p.y-.045)
                v.co.y+=.11*math.exp(-((v.co.z-1.35)/.20)**2)
        hair.data.materials.clear();hair.data.materials.append(material(hair.name+'_black',(.021,.018,.015)))
    # Keep the full editable body. Hide only skin that is covered by the garment,
    # as an explicit, reversible wardrobe mask (not a collision validation result).
    keep=body.vertex_groups.new(name='WARDROBE_VisibleSkin')
    visible=[]
    for v in body.data.vertices:
        p=body.data.shape_keys.key_blocks['Key 1'].data[v.index].co if body.data.shape_keys else v.co
        if p.z<.215 or (p.z>1.32 and abs(p.x)<.085) or p.z>1.405 or (abs(p.x)>.47 and p.z<1.04):visible.append(v.index)
    keep.add(visible,1.0,'REPLACE')
    mask=body.modifiers.new('Wardrobe - hide covered skin (reversible)','MASK');mask.vertex_group=keep.name;mask.threshold=.5
    # Put the mask before subdivision; preserve source mesh and all weights.
    bpy.context.view_layer.objects.active=body
    while list(body.modifiers).index(mask)>0:bpy.ops.object.modifier_move_up(modifier=mask.name)
    body['wardrobe_mask_note']='Full body retained. Disable Mask modifier to inspect covered skin. This does not prove garment collision clearance.'
    body.data.materials.clear();body.data.materials.append(material('Skin_draft',(.50,.35,.25)))
    for p in body.data.polygons:p.material_index=0
    scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1000;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
    scene.display.shading.light='STUDIO';scene.display.shading.studio_light='paint.sl';scene.display.shading.color_type='MATERIAL'
    scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.curvature_ridge_factor=1;scene.display.shading.curvature_valley_factor=.5
    if not scene.world:scene.world=bpy.data.worlds.new('ReviewWorld')
    scene.world.color=(.19,.20,.21);scene.display.shading.background_type='WORLD'
    cam=bpy.data.objects.new('Character_ReviewCamera',bpy.data.cameras.new('Character_ReviewCamera'));scene.collection.objects.link(cam);cam.data.type='ORTHO';scene.camera=cam
    render(scene,'01_assembled_threequarter.png',(2,-5,2))
    render(scene,'02_assembled_front.png',(0,-5,1.1))
    render(scene,'03_assembled_side.png',(5,0,1.1))
    render(scene,'04_assembled_back.png',(0,5,1.1))
    render(scene,'05_assembled_game_angle.png',(3,-6,2),scale=2.2)
    render(scene,'06_head_closeup.png',(1,-4,1.75),target=(0,-.015,1.43),scale=.64)
    render(scene,'01_assembled_threequarter.png',(2,-5,2))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'character_fitting_draft_v5.blend'))
    (ROOT/'fitting_report.json').write_text(json.dumps({'status':'static draft for visual review','body_height_m':1.65,'body_source':str(BODY),'robe_vertices_pushed_clear_of_body':nudged,'scope':'Source-derived body, hair, robe remain separate. No garment or hair rig yet. Not an animation/runtime pass.'},indent=2),encoding='utf8')
if __name__=='__main__':main()
