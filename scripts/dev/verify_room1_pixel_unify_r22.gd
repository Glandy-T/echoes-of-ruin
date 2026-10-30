extends Node

const REPORT := "res://docs/art/experiments/room1_pixel_unify_r22/source/runtime_validation.json"
const ROOT := "res://assets/art/room1_pixel_unify_r22/"
const WALL_SHADER := "res://scripts/dev/room1_complete_surface_r19.gdshader"
const POD_SHADER := "res://scripts/props/cryopod_standard_v8_surface.gdshader"
const VARIANTS := ["a","b","c","d"]
var room:Node3D
var errors:Array[String]=[]
var checks:Dictionary={}
var baseline:Dictionary={}

func _ready() -> void:call_deferred("run")
func check(label:String,condition:bool) -> void:
	checks[label]=condition
	if not condition:
		errors.append(label)
		push_error("R22_CHECK "+label)
func frames(count:int) -> void:
	for _i in count:await get_tree().physics_frame
func node_state() -> Dictionary:
	var result:Dictionary={}
	for node:Node in room.find_children("*","Node3D",true,false):
		if node is MeshInstance3D or node is CollisionObject3D:
			result[str(node.get_path())]={"transform":node.global_transform,"mesh":node.mesh.resource_path if node is MeshInstance3D and node.mesh else "","layer":node.collision_layer if node is CollisionObject3D else -1,"mask":node.collision_mask if node is CollisionObject3D else -1}
	return result
func unchanged_nodes(label:String) -> void:
	var current:=node_state()
	check(label+"_node_set",current.keys().size()==baseline.nodes.keys().size())
	for key in baseline.nodes:
		check(label+"_"+key+"_transform",current.has(key) and current[key].transform.is_equal_approx(baseline.nodes[key].transform))
		check(label+"_"+key+"_mesh",current.has(key) and current[key].mesh==baseline.nodes[key].mesh)
		check(label+"_"+key+"_collision",current.has(key) and current[key].layer==baseline.nodes[key].layer and current[key].mask==baseline.nodes[key].mask)
func expected_pods() -> Dictionary:
	var result:Dictionary={}
	for record:Dictionary in room.room_pod_records:
		var id:=str(record.id)
		result[id+":lid"]=ROOT+"numbered/"+id+"_lid.png"
		result[id+":shell_end"]=ROOT+"numbered/"+id+"_shell_end.png"
		result[id+":shell_side"]=ROOT+"variant_"+VARIANTS[int(record.variant_index)]+"/shell_side.png"
	return result
func report_shaders_are_original(report:Dictionary) -> void:
	var shell_seen:=false
	var pod_seen:=false
	for path:String in report.shaders.values():
		if path==WALL_SHADER:shell_seen=true
		if path==POD_SHADER:pod_seen=true
		check("original_shader_"+path,path==WALL_SHADER or path==POD_SHADER)
	check("both_existing_shader_types_retained",shell_seen and pod_seen)
func unchanged_lightmaps(label:String) -> void:
	for id:String in room.room_pods:
		var pod:Node3D=room.room_pods[id]
		check(label+"_"+id+"_closed_lightmap",pod.closed_irradiance.resource_path==baseline.lightmaps[id].closed)
		check(label+"_"+id+"_open_lightmap",pod.open_irradiance.resource_path==baseline.lightmaps[id].open)

func dynamic_material_state() -> Dictionary:
	var result:Dictionary={}
	for item:Dictionary in room.pixel_snapshots:
		var material:ShaderMaterial=item.material
		var key:=str(material.get_instance_id())
		if str(item.role)=="shell":
			result[key]={"room_pose_blend":material.get_shader_parameter("room_pose_blend"),"baked_energy":material.get_shader_parameter("baked_energy"),"actor_shadow_enabled":material.get_shader_parameter("actor_shadow_enabled")}
		else:
			result[key]={"pose_blend":material.get_shader_parameter("pose_blend"),"baked_energy":material.get_shader_parameter("baked_energy"),"actor_shadow_enabled":material.get_shader_parameter("actor_shadow_enabled")}
	return result

func review_baseline_scope_is_exact() -> bool:
	for item:Dictionary in room.pixel_snapshots:
		var actual:Array=[]
		for key:Variant in item.parameters.keys():actual.append(str(key))
		actual.sort()
		var expected:Array
		if str(item.role)!="shell":expected=["color_map"]
		else:
			var kind:=int((item.material as ShaderMaterial).get_shader_parameter("full_surface_kind"))
			expected=["full_surface_mode"]
			if kind==1:expected.append_array(["full_floor_aged_map","full_floor_leaks_map"])
			elif room.WALL_MAPS.has(kind):expected.append("full_wall_"+str(["","","left","right","front","rear"][kind])+"_map")
		expected.sort()
		if actual!=expected:
			print("R22_BASELINE_SCOPE_MISMATCH role=",item.role," pod=",item.pod_id," actual=",actual," expected=",expected)
			return false
	return true
func run() -> void:
	room=get_parent() as Node3D
	await frames(12)
	room.finish_exit();room.review_ui.close_dialogue()
	baseline.nodes=node_state();baseline.lightmaps={}
	for id:String in room.room_pods:
		var pod:Node3D=room.room_pods[id]
		baseline.lightmaps[id]={"closed":pod.closed_irradiance.resource_path,"open":pod.open_irradiance.resource_path}
	room.set_r22_mode(1)
	var a:Dictionary=room.get_pixel_unify_report()
	check("A_mode",a.mode==1)
	for path:String in a.walls.values():check("A_wall_not_r22_"+path,not path.begins_with(ROOT))
	check("A_floor_not_r22",not str(a.floor).begins_with(ROOT))
	for path:String in a.pods.values():check("A_pod_not_r22_"+path,not path.begins_with(ROOT))
	report_shaders_are_original(a);unchanged_nodes("A");unchanged_lightmaps("A")
	room.set_r22_mode(2)
	var b:Dictionary=room.get_pixel_unify_report()
	check("B_mode",b.mode==2)
	check("B_four_walls",b.walls=={"2":ROOT+"wall_left.png","3":ROOT+"wall_right.png","4":ROOT+"wall_front.png","5":ROOT+"wall_rear.png"})
	check("B_floor",b.floor==ROOT+"floor_with_leaks.png")
	check("B_all_20_pods_three_exterior_maps",b.pods==expected_pods())
	report_shaders_are_original(b);unchanged_nodes("B");unchanged_lightmaps("B")
	room.set_r22_mode(1)
	var restored:Dictionary=room.get_pixel_unify_report()
	check("A_restored",restored.mode==1 and restored.walls==a.walls and restored.floor==a.floor and restored.pods==a.pods and restored.shaders==a.shaders)
	unchanged_nodes("A_restored");unchanged_lightmaps("A_restored")
	check("review_baseline_only_contains_mutated_uniforms",review_baseline_scope_is_exact())
	var hero:Node3D=room.room_pods["P12"]
	for opened:bool in [false,true]:
		hero.set_open_immediate(opened);room._sync_complete_room_pose()
		var pose_label:="open" if opened else "closed"
		var before:=dynamic_material_state()
		room.set_r22_mode(2)
		check(pose_label+"_B_preserves_pose_gi_shadow_energy",dynamic_material_state()==before)
		room.set_r22_mode(1)
		check(pose_label+"_A_restore_preserves_pose_gi_shadow_energy",dynamic_material_state()==before)
	hero.set_open_immediate(false);room._sync_complete_room_pose()
	var report:Dictionary={"result":"PASS" if errors.is_empty() else "FAIL","errors":errors,"checks":checks,"scope":"Review-only r22 swaps four wall maps, the existing continuous floor color map and each of the twenty pods' three exterior color maps. Geometry, transforms, UVs, collision, camera, original shaders, lights and r19 GI maps are unchanged.","expected_pod_maps":expected_pods()}
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(REPORT.get_base_dir()))
	FileAccess.open(REPORT,FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print("R22_UNIFY_RUNTIME ",report.result," checks=",checks.size()," errors=",JSON.stringify(errors))
	get_tree().quit(0 if errors.is_empty() else 1)
