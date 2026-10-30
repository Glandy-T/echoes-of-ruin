extends Node

const REPORT := "res://docs/art/experiments/room1_floor_detail_full_r26/source/runtime_validation.json"
const R25_ROOT := "res://assets/art/room1_floor_detail_r25/"
const R26_ROOT := "res://assets/art/room1_floor_detail_full_r26/"
var room:Node3D
var checks:Dictionary={}
var errors:Array[String]=[]
var baseline:Dictionary={}

func _ready() -> void:call_deferred("run")
func check(label:String,ok:bool) -> void:
	checks[label]=ok
	if not ok:
		errors.append(label)
		push_error("R26_CHECK "+label)
func frames(count:int) -> void:
	for _i in count:await get_tree().physics_frame
func dynamic_state() -> Dictionary:
	var result:Dictionary={}
	for item:Dictionary in room.pixel_snapshots:
		var material:ShaderMaterial=item.material
		result[str(material.get_instance_id())]={"pose":material.get_shader_parameter("room_pose_blend"),"energy":material.get_shader_parameter("baked_energy"),"shadow":material.get_shader_parameter("actor_shadow_enabled"),"shader":material.shader.resource_path}
	return result
func geometry_state() -> Dictionary:
	var result:Dictionary={}
	for node:Node in room.find_children("*","Node3D",true,false):
		if node is MeshInstance3D:
			var mesh_node:=node as MeshInstance3D
			result[str(node.get_path())]={"transform":str(node.global_transform),"mesh":mesh_node.mesh.resource_path if mesh_node.mesh else "","visible":mesh_node.visible}
		elif node is CollisionObject3D:
			var collision:=node as CollisionObject3D
			result[str(node.get_path())]={"transform":str(node.global_transform),"layer":collision.collision_layer,"mask":collision.collision_mask}
	return result
func lighting_state() -> Dictionary:
	var result:Dictionary={}
	for node:Node in room.find_children("*","Light3D",true,false):
		var light:=node as Light3D
		result[str(node.get_path())]={"transform":str(light.global_transform),"energy":light.light_energy,"color":str(light.light_color),"visible":light.visible}
	return result
func pod_state() -> Dictionary:
	var result:Dictionary={}
	for id:String in room.room_pods:
		var pod:Node3D=room.room_pods[id]
		var maps:Array=[]
		for entry:Dictionary in (room.room_pod_finishes[id] as RefCounted).entries:
			var material:ShaderMaterial=entry.material
			var texture:Texture2D=material.get_shader_parameter("color_map")
			maps.append({"role":str(entry.role),"shader":material.shader.resource_path,"color_map":texture.resource_path if texture else ""})
		result[id]={"transform":str(pod.global_transform),"maps":maps,"open":pod.get_state_name()}
	return result
func floor_paths() -> Array[String]:
	var result:Array[String]=[]
	for item:Dictionary in room.r26_floor_snapshots:
		var texture:Texture2D=(item.material as ShaderMaterial).get_shader_parameter("full_floor_leaks_map")
		result.append(texture.resource_path if texture else "")
	return result
func wall_paths() -> Dictionary:
	var result:Dictionary={}
	for item:Dictionary in room.r24_map_snapshots:
		var texture:Texture2D=(item.material as ShaderMaterial).get_shader_parameter(str(item.parameter))
		result[str(item.kind)]=texture.resource_path if texture else ""
	return result
func check_unchanged(label:String,now:Dictionary,then:Dictionary) -> void:
	check(label+"_keys",now.keys().size()==then.keys().size())
	for key:String in then:check(label+"_"+key,now.has(key) and now[key]==then[key])
func check_mode(mode:int) -> void:
	room.set_r26_mode(mode)
	var report:Dictionary=room.get_floor_detail_full_report()
	check("mode_"+str(mode),report.mode==mode)
	check("only_floor_uniforms_"+str(mode),report.mutated_uniforms==["full_floor_aged_map","full_floor_leaks_map"])
	var expected:String=R25_ROOT+"floor_candidate.png" if mode==1 else R26_ROOT+"floor_with_leaks.png"
	for path:String in floor_paths():check("floor_expected_"+str(mode)+"_"+path,path==expected)
	check("r24_wall_lock_"+str(mode),wall_paths()=={"2":"res://assets/art/room1_wall_detail_full_r24/wall_left.png","3":"res://assets/art/room1_wall_detail_full_r24/wall_right.png","4":"res://assets/art/room1_wall_detail_full_r24/wall_front.png","5":"res://assets/art/room1_wall_detail_full_r24/wall_rear.png"})
	check_unchanged("geometry_"+str(mode),geometry_state(),baseline.geometry)
	check_unchanged("lights_"+str(mode),lighting_state(),baseline.lights)
func run() -> void:
	room=get_parent() as Node3D
	await frames(12)
	room.finish_exit();room.review_ui.close_dialogue()
	check("r26_assets_present",room._r26_assets_available())
	check("floor_material_captured",not room.r26_floor_snapshots.is_empty())
	baseline.geometry=geometry_state();baseline.lights=lighting_state();baseline.dynamic=dynamic_state();baseline.pods=pod_state()
	for mode:int in [1,2,1]:check_mode(mode)
	check("r25_floor_restored_after_aba",floor_paths().all(func(path):return path==R25_ROOT+"floor_candidate.png"))
	for opened:bool in [false,true]:
		var hero:Node3D=room.room_pods["P12"]
		hero.set_open_immediate(opened);room._sync_complete_room_pose()
		var before_dynamic:=dynamic_state();var before_pods:=pod_state()
		for mode:int in [1,2,1]:
			room.set_r26_mode(mode)
			check(("open" if opened else "closed")+"_dynamic_"+str(mode),dynamic_state()==before_dynamic)
			check(("open" if opened else "closed")+"_pods_"+str(mode),pod_state()==before_pods)
	room.room_pods["P12"].set_open_immediate(false);room._sync_complete_room_pose()
	var report:Dictionary={"result":"PASS" if errors.is_empty() else "FAIL","errors":errors,"checks":checks,"scope":"r26 A/B/A changes only both floor texture bindings. r25 C and r24 walls are the fixed baseline; models, transforms, collisions, UV-bearing meshes, lights, r19 GI, doors and all 20 pod materials stay unchanged. P12 is checked closed and open."}
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(REPORT.get_base_dir()))
	FileAccess.open(REPORT,FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print("R26_FLOOR_RUNTIME ",report.result," checks=",checks.size()," errors=",JSON.stringify(errors))
	get_tree().quit(0 if errors.is_empty() else 1)
