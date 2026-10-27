"""Source-derived robe reduction study. Geometry is never generated from a silhouette."""
import bpy, bmesh, json, math, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from inspect_robe import load_robe

def stats(obj):
    mesh=obj.data; mesh.calc_loop_triangles()
    bm=bmesh.new(); bm.from_mesh(mesh)
    value={'vertices':len(mesh.vertices),'faces':len(mesh.polygons),'triangles':len(mesh.loop_triangles),
           'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_nonboundary_edges':sum(not e.is_manifold and not e.is_boundary for e in bm.edges),
           'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces)}
    bm.free(); return value

def activate(obj):
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active=obj

def preview(scene,obj,filename):
    for other in scene.objects:
        if other.type=='MESH':other.hide_render=other!=obj
    scene.render.filepath=str(ROOT/filename);bpy.ops.render.render(write_still=True)

def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source,audit=load_robe(); source.name='Robe_Original_Reference'
    original_stats=stats(source)
    robe=source.copy();robe.data=source.data.copy();bpy.context.collection.objects.link(robe);robe.name='Robe_Reduced_Study'
    bm=bmesh.new();bm.from_mesh(robe.data);bm.verts.ensure_lookup_table()
    belt_indices=set(audit['component_vertex_indices'][4]+audit['component_vertex_indices'][5])
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index in belt_indices],context='VERTS')
    # Imported seams duplicate vertices; merge only coincident boundary vertices.
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000002)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(robe.data);bm.free();robe.data.update()
    activate(robe)
    before=stats(robe)
    # Lightly smooth small simulation creases before reduction; preserve the neckline/cuffs/hem.
    group=robe.vertex_groups.new(name='Interior_Smoothing')
    bm=bmesh.new();bm.from_mesh(robe.data)
    boundary={v.index for e in bm.edges if e.is_boundary for v in e.verts}
    group.add([v.index for v in robe.data.vertices if v.index not in boundary],1.0,'REPLACE');bm.free()
    smooth=robe.modifiers.new('Soften_small_simulation_folds','SMOOTH');smooth.factor=.5;smooth.iterations=6;smooth.vertex_group=group.name
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    dec=robe.modifiers.new('Source_reduction_3000_triangles','DECIMATE');dec.ratio=min(1.0,3000/before['triangles']);dec.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=dec.name)
    # Preserve source UV for lineage; it remains diagnostic until separately audited.
    robe.data.uv_layers.active.name='UV_Robe_Source_Reduced'
    for p in robe.data.polygons:p.use_smooth=True
    cream=bpy.data.materials.new('Warm_off_white_draft');cream.diffuse_color=(.72,.69,.61,1);cream.use_nodes=True
    cream.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.72,.69,.61,1)
    cream.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.95
    robe.data.materials.clear();robe.data.materials.append(cream)
    robe['status']='Static reduction study; no rig or fit approval'
    scene=bpy.context.scene;scene.name='ROBE_REDUCTION_REVIEW'
    scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=900;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
    scene.display.shading.light='STUDIO';scene.display.shading.studio_light='paint.sl';scene.display.shading.color_type='MATERIAL'
    scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.curvature_ridge_factor=1.1;scene.display.shading.curvature_valley_factor=.7
    scene.world=bpy.data.worlds.new('Review_World');scene.display.shading.background_type='WORLD';scene.world.color=(.18,.19,.20)
    camera_data=bpy.data.cameras.new('Review_Camera');camera=bpy.data.objects.new('Review_Camera',camera_data);scene.collection.objects.link(camera)
    camera.location=(2,-5,2.3);target=Vector((0,.02,.88));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.type='ORTHO';camera_data.ortho_scale=1.75;scene.camera=camera
    source.data.materials[0].diffuse_color=(.075,.09,.105,1)
    preview(scene,source,'01_original_source.png');preview(scene,robe,'02_reduced_offwhite.png')
    camera.location=(0,-5,1.2);camera.rotation_euler=(Vector((0,0,.88))-camera.location).to_track_quat('-Z','Y').to_euler()
    preview(scene,robe,'03_reduced_front.png')
    camera.location=(5,0,1.2);camera.rotation_euler=(Vector((0,0,.88))-camera.location).to_track_quat('-Z','Y').to_euler()
    preview(scene,robe,'04_reduced_side.png')
    camera.location=(2,-5,2.3);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    source.hide_render=True;source.hide_set(True);activate(robe)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'robe_reduced_study_v5.blend'))
    report={'source':original_stats,'without_belt_before_reduction':before,'reduced':stats(robe),'belt_components_removed':[4,5], 'smooth_iterations':6,'reduction_target_triangles':3000,'scope':'Source-scale static study only. Source UV has not yet been verified after reduction; no fitted rig, texture or runtime acceptance.'}
    (ROOT/'reduction_report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
