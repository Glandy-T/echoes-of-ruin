"""Read-only final artifact check for the bounded protagonist cleanup."""
from pathlib import Path
import hashlib, json, struct
import bpy
from mathutils.kdtree import KDTree

EXP = Path(__file__).resolve().parent.parent
RAW = EXP.parent / 'protagonist_tripo_cn_p20_v1'
OUT = EXP / 'source' / 'independent_validation.json'
RAW_HASH = 'f9717909d1df005269bfa695aa8a6863193ce4c27e583b3e52b9360d3ed58ff6'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

raw_obj = RAW / 'model/protagonist_tripo_cn_p20_v1_raw.obj'
blend = EXP / 'model/protagonist_cn_cleanup_v1.blend'
glb = EXP / 'model/protagonist_cn_cleanup_v1.glb'
report = json.loads((EXP / 'source/build_report.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(blend))
before = bpy.data.collections.get('BEFORE_ORIGINAL')
after = bpy.data.collections.get('AFTER_REPAIR')
for collection in (before, after):
    if collection:
        collection.hide_viewport = False
        collection.hide_render = False
        for obj in collection.all_objects:
            obj.hide_viewport = False
            obj.hide_render = False
            obj.hide_set(False)
bpy.context.view_layer.update()
before_meshes = [o for o in before.all_objects if o.type == 'MESH'] if before else []
after_meshes = [o for o in after.all_objects if o.type == 'MESH'] if after else []
source = before_meshes[0] if len(before_meshes) == 1 else None
candidate = after_meshes[0] if len(after_meshes) == 1 else None

checks = {'raw_obj_hash_unchanged': sha(raw_obj) == RAW_HASH, 'before_after_collections_present': before is not None and after is not None, 'one_source_and_one_candidate_mesh': source is not None and candidate is not None}
if source and candidate:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    source_eval = source.evaluated_get(depsgraph)
    candidate_eval = candidate.evaluated_get(depsgraph)
    tree = KDTree(len(source_eval.data.vertices))
    for i, v in enumerate(source_eval.data.vertices): tree.insert(source_eval.matrix_world @ v.co, i)
    tree.balance()
    world_nearest = [tree.find(candidate_eval.matrix_world @ v.co)[2] for v in candidate_eval.data.vertices]
    world_max = max(world_nearest)
    checks.update({'source_untouched_topology': len(source.data.vertices) == 4110 and len(source.data.polygons) == 3020, 'candidate_counts_match_report': len(candidate.data.vertices) == report['weld']['candidate_vertices'] and len(candidate.data.polygons) == report['exact_deletion']['remaining_faces'], 'source_transform_equals_candidate': all(abs(source.matrix_world[r][c] - candidate.matrix_world[r][c]) < 1e-12 for r in range(4) for c in range(4)), 'candidate_custom_corner_normals': candidate.data.has_custom_normals and candidate.data.normals_domain == 'CORNER' and len(candidate.data.corner_normals) == len(candidate.data.loops), 'no_uv_on_candidate': len(candidate.data.uv_layers) == 0, 'no_shape_keys_on_candidate': candidate.data.shape_keys is None, 'no_modifiers_on_candidate': not candidate.modifiers})
    checks['candidate_world_vertices_match_source'] = world_max <= 1e-6
else:
    checks.update({'source_untouched_topology': False, 'candidate_counts_match_report': False, 'source_transform_equals_candidate': False, 'candidate_custom_corner_normals': False, 'no_uv_on_candidate': False, 'no_shape_keys_on_candidate': False, 'no_modifiers_on_candidate': False})
    world_max = None
checks['no_armatures_in_blend'] = not [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
checks['all_five_qa_cameras'] = all(bpy.data.objects.get('QA_'+v) is not None for v in ('front','side','back','quarter','head_back'))

data = glb.read_bytes()
magic, version, total = struct.unpack_from('<4sII', data)
json_length, kind = struct.unpack_from('<II', data, 12)
doc = json.loads(data[20:20+json_length])
checks.update({'candidate_glb_valid_header': magic == b'glTF' and version == 2 and total == len(data) and kind == 0x4E4F534A, 'candidate_glb_one_mesh_no_cameras': len(doc.get('meshes', [])) == 1 and not doc.get('cameras'), 'candidate_glb_no_rig': not doc.get('skins') and not doc.get('animations'), 'candidate_glb_no_uv': all('TEXCOORD_0' not in p.get('attributes', {}) for m in doc['meshes'] for p in m['primitives'])})
visual = {'actual_pngs_reviewed': ['before_front','after_front','before_side','after_side','before_back','after_back','before_quarter','after_quarter','before_head_back','after_head_back'], 'finding': 'Fine independent curls/loops and the selected lower rear curl are reduced while the main head, face, robe, hands, feet and silhouette remain materially unchanged.', 'remaining_limits': ['A narrow long raised strip remains on the right rear hair mass; it reads as a broad modeled lock/seam rather than a free curl at this camera scale.', 'The lower hair edge remains jagged and the hands/feet remain rough AI-generated starting mesh geometry.', 'No UV, texture, rig, deformation, Room 1 placement, game camera or runtime behavior was validated.'], 'user_art_acceptance': 'pending'}
transforms = {}
if source and candidate:
    transforms = {'source_world_matrix': [list(row) for row in source_eval.matrix_world], 'candidate_world_matrix': [list(row) for row in candidate_eval.matrix_world], 'source_location_rotation_scale': [list(source.location), list(source.rotation_euler), list(source.scale)], 'candidate_location_rotation_scale': [list(candidate.location), list(candidate.rotation_euler), list(candidate.scale)], 'max_abs_component_delta': max(abs(source_eval.matrix_world[r][c] - candidate_eval.matrix_world[r][c]) for r in range(4) for c in range(4)), 'candidate_to_source_nearest_world_vertex_max_distance': world_max}
result = {'status': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks, 'visual_review': visual, 'transforms': transforms, 'artifact_sha256': {'blend': sha(blend), 'glb': sha(glb)}}
OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
print(result['status'], sum(checks.values()), '/', len(checks))
assert all(checks.values()), [k for k,v in checks.items() if not v]
