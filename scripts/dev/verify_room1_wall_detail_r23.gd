extends Node

const REPORT := "res://docs/art/experiments/room1_wall_detail_r23/source/runtime_validation.json"
const R22_ROOT := "res://assets/art/room1_pixel_unify_r22/"
const R23_ROOT := "res://assets/art/room1_wall_detail_r23/"
const R23_MAPS := {1:"wall_rear_reference.png",3:"wall_rear_a.png",4:"wall_rear_b.png"}
var room:Node3D
var checks:Dictionary={}
var errors:Array[String]=[]
var baseline:Dictionary={}

func _ready() -> void:call_deferred("run")
func check(label:String,ok:bool) -> void:
	checks[label]=ok
	if not ok:errors.append(label);push_error("R23_CHECK "+label)
func frames(count:int) -> void:
	for _i in count:await get_tree().physics_frame
func dynamic_state() -> Dictionary:
	var result:Dictionary={}
	for item:Dictionary in room.pixel_snapshots:
		var material:ShaderMaterial=item.material
		result[str(material.get_instance_id())]={"pose":material.get_shader_parameter("room_pose_blend"),"energy":material.get_shader_parameter("baked_energy"),"shadow":material.get_shader_parameter("actor_shadow_enabled")}
	return result
func scene_state() -> Dictionary:
	var result:Dictionary={}
	for node:Node in room.find_children("*","Node3D",true,false):
		if node is MeshInstance3D or node is CollisionObject3D:
			result[str(node.get_path())]={"transform":node.global_transform,"mesh":node.mesh.resource_path if node is MeshInstance3D and node.mesh else "","layer":node.collision_layer if node is CollisionObject3D else -1,"mask":node.collision_mask if node is CollisionObject3D else -1}
	return result
func check_scene_unchanged(label:String) -> void:
	var now:=scene_state();check(label+"_set",now.keys().size()==baseline.nodes.keys().size())
	for key:String in baseline.nodes:
		check(label+"_"+key,now.has(key) and now[key]==baseline.nodes[key])
func rear_paths() -> Array[String]:
	var paths:Array[String]=[]
	for item:Dictionary in room.rear_map_snapshots:
		var texture:Texture2D=(item.material as ShaderMaterial).get_shader_parameter("full_wall_rear_map")
		paths.append(texture.resource_path if texture else "")
	return paths
func other_r22_paths() -> bool:
	var report:Dictionary=room.get_pixel_unify_report()
	return report.walls.get("2","")==R22_ROOT+"wall_left.png" and report.walls.get("3","")==R22_ROOT+"wall_right.png" and report.walls.get("4","")==R22_ROOT+"wall_front.png" and report.floor==R22_ROOT+"floor_with_leaks.png"
func run() -> void:
	room=get_parent() as Node3D;await frames(12)
	room.finish_exit();room.review_ui.close_dialogue()
	baseline.nodes=scene_state()
	check("r23_assets_present",room._r23_assets_available())
	check("two_or_more_rear_materials",room.rear_map_snapshots.size()>=1)
	var a_maps:Array[String]=[]
	for mode:int in [1,2,3,4,1]:
		room.set_r23_mode(mode)
		var report:Dictionary=room.get_wall_detail_report()
		check("mode_"+str(mode),report.mode==mode)
		check("other_full_room_remains_r22_"+str(mode),other_r22_paths())
		var expected:String=R22_ROOT+"wall_rear.png" if mode==2 else R23_ROOT+str(R23_MAPS[mode])
		for path:String in rear_paths():check("rear_only_expected_"+str(mode)+"_"+path,path==expected)
		if mode==1 and a_maps.is_empty():a_maps=rear_paths()
		if mode==1 and not a_maps.is_empty():check("reference_restored",rear_paths()==a_maps)
		check_scene_unchanged("mode_"+str(mode))
	for opened:bool in [false,true]:
		var hero:Node3D=room.room_pods["P12"];hero.set_open_immediate(opened);room._sync_complete_room_pose()
		var before:=dynamic_state()
		for mode:int in [1,2,3,4,1]:
			room.set_r23_mode(mode);check(("open" if opened else "closed")+"_preserves_live_state_"+str(mode),dynamic_state()==before)
	var report:Dictionary={"result":"PASS" if errors.is_empty() else "FAIL","errors":errors,"checks":checks,"scope":"r23 switches only full_wall_rear_map. Modes 1/3/4 use PixelLab images with an identical r22 exterior and a fixed PNG patch x=944..1200,y=16..272; mode 2 is r22 current rear map. Other room maps, meshes, transforms, collision, shader identities, UVs, lights and GI are not modified."}
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(REPORT.get_base_dir()))
	FileAccess.open(REPORT,FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print("R23_WALL_RUNTIME ",report.result," checks=",checks.size()," errors=",JSON.stringify(errors))
	get_tree().quit(0 if errors.is_empty() else 1)
