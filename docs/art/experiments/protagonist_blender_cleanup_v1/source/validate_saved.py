from pathlib import Path
import bpy,bmesh,json,hashlib,math

EXP=Path(__file__).resolve().parents[1]
RAW=EXP.parent/'protagonist_tripo_h25_v1/model/protagonist_tripo_h25_v1_raw.glb'
def audit(obj):
 mesh=obj.data;mesh.calc_loop_triangles();bm=bmesh.new();bm.from_mesh(mesh)
 result={'name':obj.name,'vertices':len(mesh.vertices),'polygons':len(mesh.polygons),'triangles':len(mesh.loop_triangles),'boundary_edges':sum(e.is_boundary for e in bm.edges),'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'non_manifold_vertices':sum(not v.is_manifold for v in bm.verts),'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'UV_layers':len(mesh.uv_layers),'has_custom_normals':mesh.has_custom_normals,'bounds':[[min((obj.matrix_world@v.co)[i] for v in mesh.vertices),max((obj.matrix_world@v.co)[i] for v in mesh.vertices)] for i in range(3)]}
 bm.free();return result
bpy.ops.wm.open_mainfile(filepath=str(EXP/'model/protagonist_cleanup_v1.blend'))
parts=list(bpy.data.collections['01_LOCAL_CLEANUP_CANDIDATE'].objects)
assert all(o.type=='MESH' for o in parts)
saved=[audit(o) for o in parts]
assert not any(o.type=='ARMATURE' for o in bpy.context.scene.objects)
assert all(row['UV_layers']==0 for row in saved)
assert all(math.isfinite(c) for o in parts for v in o.data.vertices for c in v.co)
ref=bpy.data.objects['REFERENCE_H25_UNMODIFIED'];reference_bounds=audit(ref)['bounds']
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(EXP/'model/protagonist_cleanup_v1.glb'))
glb=[audit(o) for o in bpy.context.scene.objects if o.type=='MESH']
assert len(glb)==len(saved)
assert set(o['name'] for o in glb)==set(o['name'] for o in saved)
assert sum(o['triangles'] for o in saved)==sum(o['triangles'] for o in glb)
assert not any(o.type in ['CAMERA','LIGHT','ARMATURE'] for o in bpy.context.scene.objects)
report={'raw_SHA256':hashlib.sha256(RAW.read_bytes()).hexdigest(),'expected_raw_SHA256':'04227946df3e2ccd11952bc6084086521a13c3839f716fa73d4392af9d47a2a2','saved_blend_meshes':saved,'reimported_GLB_meshes':glb,'GLB_triangle_count_matches':True,'GLB_contains_only_candidate_meshes':True,'original_reference_bounds':reference_bounds,'cloud_calls':0,'new_textures':0,'UV_created':False,'animation_or_art_approval':False,'note':'Static file readback and topology statistics only. Remaining source defects are reported per object; this is not rig-ready certification.'}
assert report['raw_SHA256']==report['expected_raw_SHA256']
(EXP/'source/validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('SAVED_BLEND_AND_REIMPORTED_GLB_CHECKED;NOT_FINAL_ART_OR_ANIMATION_APPROVAL')
print(json.dumps([{k:r[k] for k in ['name','vertices','triangles','boundary_edges','non_manifold_vertices','degenerate_faces']} for r in saved]))
