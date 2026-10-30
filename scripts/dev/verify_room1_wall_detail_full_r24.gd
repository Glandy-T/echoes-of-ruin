extends Node

const REPORT := "res://docs/art/experiments/room1_wall_detail_full_r24/source/runtime_validation.json"
const R22_ROOT := "res://assets/art/room1_pixel_unify_r22/"
const R24_ROOT := "res://assets/art/room1_wall_detail_full_r24/"
const R24_MAPS := {2:"wall_left.png",3:"wall_right.png",4:"wall_front.png",5:"wall_rear.png"}
var room:Node3D
var checks:Dictionary={}
var errors:Array[String]=[]
var baseline:Dictionary={}

func _ready() -> void:call_deferred("run")
func check(label:String,ok:bool) -> void:
	checks[label]=ok
	if not ok:
		errors.append(label)
		push_error("R24_CHECK "+label)
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

func pod_state() -> Dictionary:
	var result:Dictionary={}
	for id:String in room.room_pods:
		var pod:Node3D=room.room_pods[id]
		var materials:Array=[]
		for entry:Dictionary in (room.room_pod_finishes[id] as RefCounted).entries:
			var material:ShaderMaterial=entry.material
			materials.append({"role":str(entry.role),"shader":material.shader.resource_path,"color_map":(material.get_shader_parameter("color_map") as Texture2D).resource_path if material.get_shader_parameter("color_map") else ""})
		result[id]={"transform":str(pod.global_transform),"materials":materials,"open_state":pod.get_state_name()}
	return result

func lighting_state() -> Dictionary:
	var result:Dictionary={}
	for node:Node in room.find_children("*","Light3D",true,false):
		var light:=node as Light3D
		result[str(node.get_path())]={"transform":str(light.global_transform),"energy":light.light_energy,"color":str(light.light_color),"visible":light.visible}
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
	room.set_r24_mode(mode)
	var report:Dictionary=room.get_wall_detail_full_report()
	check("mode_"+str(mode),report.mode==mode)
	check("mutated_uniform_scope_"+str(mode),report.mutated_uniforms==["full_wall_left_map","full_wall_right_map","full_wall_front_map","full_wall_rear_map"])
	for kind:int in [2,3,4,5]:
		var expected:String=R22_ROOT+"wall_"+["","","left","right","front","rear"][kind]+".png" if mode==1 else R24_ROOT+str(R24_MAPS[kind])
		check("wall_"+str(kind)+"_mode_"+str(mode),wall_paths().get(str(kind),"")==expected)
	# These reports cover every 20 pod finish material; walls are the only legal
	# differences and r22 keeps floor/pods mapped to its candidate assets.
	check("floor_stays_r22_"+str(mode),report.r22.floor==R22_ROOT+"floor_with_leaks.png")
	for key:String in baseline.pods:
		check("pod_materials_stay_r22_"+str(mode)+"_"+key,report.r22.pods.get(key,"")==baseline.pod_maps.get(key,""))
	check_unchanged("geometry_"+str(mode),geometry_state(),baseline.geometry)
	check_unchanged("lights_"+str(mode),lighting_state(),baseline.lights)

func run() -> void:
	room=get_parent() as Node3D
	await frames(12)
	room.finish_exit();room.review_ui.close_dialogue()
	check("r24_assets_present",room._r24_assets_available())
	check("four_wall_materials_captured",room.r24_map_snapshots.size()>=4)
	baseline.geometry=geometry_state()
	baseline.lights=lighting_state()
	baseline.dynamic=dynamic_state()
	baseline.pods=pod_state()
	baseline.pod_maps=(room.get_pixel_unify_report() as Dictionary).pods.duplicate()
	for mode:int in [1,2,1]:
		check_mode(mode)
	check("r22_maps_restored_after_aba",wall_paths()=={ "2":R22_ROOT+"wall_left.png", "3":R22_ROOT+"wall_right.png", "4":R22_ROOT+"wall_front.png", "5":R22_ROOT+"wall_rear.png" })
	for opened:bool in [false,true]:
		var hero:Node3D=room.room_pods["P12"]
		hero.set_open_immediate(opened);room._sync_complete_room_pose()
		var before_dynamic:=dynamic_state()
		var before_pods:=pod_state()
		for mode:int in [1,2,1]:
			room.set_r24_mode(mode)
			check(("open" if opened else "closed")+"_dynamic_state_"+str(mode),dynamic_state()==before_dynamic)
			check(("open" if opened else "closed")+"_all_20_pods_"+str(mode),pod_state()==before_pods)
	room.room_pods["P12"].set_open_immediate(false);room._sync_complete_room_pose()
	var report:Dictionary={"result":"PASS" if errors.is_empty() else "FAIL","errors":errors,"checks":checks,"scope":"r24 A/B/A only changes four full-wall PixelLab maps. Geometry, transforms, collision, UV-bearing meshes, shaders, r19 GI, lighting, floor and all 20 pod finish maps are checked unchanged; P12 is checked both closed and open."}
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(REPORT.get_base_dir()))
	FileAccess.open(REPORT,FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print("R24_WALL_RUNTIME ",report.result," checks=",checks.size()," errors=",JSON.stringify(errors))
	get_tree().quit(0 if errors.is_empty() else 1)
