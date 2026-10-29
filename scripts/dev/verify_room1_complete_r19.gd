extends Node

const REPORT:="res://docs/art/experiments/room1_complete_r19/source/runtime_validation.json"
var room:Node3D
var errors:Array[String]=[]
var checks:Dictionary={}
var pod_records:Array=[]
var walks:Array=[]

func _ready() -> void:call_deferred("run")

func check(label:String,condition:bool) -> void:
	checks[label]=condition
	if not condition:errors.append(label);push_error("R19_CHECK "+label)

func frames(count:int) -> void:
	for i in count:await get_tree().physics_frame

func walk(start:Vector3,direction:Vector2,count:int,label:String) -> Vector3:
	room.call("teleport_player",start)
	room.set("test_input",direction)
	await frames(count)
	room.set("test_input",Vector2.ZERO)
	await frames(2)
	var end:Vector3=room.get("player").global_position
	walks.append({"label":label,"start":str(start),"end":str(end),"steps":count,"contacts":room.get("previous_contacts").duplicate()})
	return end

func run() -> void:
	room=get_parent() as Node3D
	await frames(12)
	room.call("finish_exit");room.get("review_ui").close_dialogue()
	room.set("test_mode",true);room.set("test_input",Vector2.ZERO)
	var pods:Dictionary=room.get("room_pods")
	check("twenty_standard_pods",pods.size()==20)
	var ids:Array=[];var material_ids:Dictionary={}
	for record:Dictionary in room.get("room_pod_records"):
		var id:String=record.id
		var pod:Node3D=pods[id]
		var old:Node3D=room.get_node("Pods/"+id)
		var finish:RefCounted=room.get("room_pod_finishes")[id]
		check(id+"_layout_preserved",pod.global_transform.is_equal_approx(old.global_transform))
		check(id+"_old_visual_hidden",not old.visible)
		check(id+"_number_and_variant",finish.pod_number==int(record.number) and finish.variant==int(record.variant_index))
		ids.append(finish.pod_number)
		var light:Texture2D=pod.closed_irradiance
		check(id+"_own_position_lightmap",light.resource_path.ends_with("/"+id+"_closed.exr"))
		check(id+"_closed_except_hero",id=="P12" or pod.get_state_name()==&"closed")
		check(id+"_only_existing_three_powered",pod.tube_powered==(id in ["P02","P12","P17"]) and pod.screen_powered==(id in ["P02","P12","P17"]))
		for body:CollisionObject3D in old.find_children("*","CollisionObject3D",true,false):check(id+"_old_collision_disabled",body.collision_layer==0 and body.collision_mask==0)
		for entry:Dictionary in finish.entries:
			material_ids[entry.material.get_instance_id()]=true
			var texture:Texture2D=entry.material.get_shader_parameter("color_map")
			check(id+"_"+str(entry.role)+"_exact_bake_color_map",texture.resource_path=="res://"+str(record.bake_color_maps[entry.role]))
			check(id+"_chamber_transform",(entry.material.get_shader_parameter("chamber_from_world") as Transform3D).is_equal_approx(pod.global_transform.affine_inverse()))
		pod_records.append({"id":id,"number":finish.pod_number,"variant":finish.variant,"world_transform":str(pod.global_transform),"lightmap":light.resource_path,"bindings":finish.bindings()})
	ids.sort();check("all_numbers_01_to_20",ids==range(1,21))
	check("240_instance_local_solid_materials",material_ids.size()==240)
	check("p12_has_own_open_map",pods.P12.open_irradiance.resource_path.ends_with("/P12_open.exr"))
	for material:ShaderMaterial in room.get("complete_shell_materials"):
		check("matching_shell_closed_map",material.get_shader_parameter("strip_irradiance").resource_path.ends_with("/room_closed.exr"))
		check("matching_shell_open_map",material.get_shader_parameter("strip_irradiance_open").resource_path.ends_with("/room_open.exr"))
	# All closed for deterministic aisle/collision coverage, then restore P12.
	room.call("teleport_player",Vector3(10.5,.05,-4.75))
	pods.P12.set_open_immediate(false)
	await frames(3)
	for record:Dictionary in room.get("room_pod_records"):
		var id:String=record.id;var pod:Node3D=pods[id]
		var world_direction:Vector3=pod.global_basis*Vector3(0,0,-1)
		var end:=await walk(pod.to_global(Vector3(0,.05,2.0)),Vector2(world_direction.x,world_direction.z),60,"blocked_"+id)
		check(id+"_closed_hull_blocks_actor",pod.to_local(end).z>1.25)
		check(id+"_actor_stays_grounded",absf(end.y)<.15)
	for row in [0,1]:
		for column in range(1,10):
			var first:int=(1 if row==0 else 11)+column-1
			var second:=first+1
			var a:Node3D=pods["P%02d"%first];var b:Node3D=pods["P%02d"%second]
			var x:float=(a.global_position.x+b.global_position.x)*.5
			var start:=Vector3(x,.05,-3.6 if row==0 else -5.9)
			var end:=await walk(start,Vector2(0,1 if row==0 else -1),80,"aisle_%02d_%02d"%[first,second])
			check("aisle_%02d_%02d_passable"%[first,second],absf(end.z-start.z)>2.2 and absf(end.y)<.15)
	var cross_end:=await walk(Vector3(.8,.05,-4.75),Vector2.RIGHT,575,"cross_room_main_aisle")
	check("main_aisle_crosses_room",cross_end.x>19.2 and absf(cross_end.y)<.15)
	var hero:Node3D=pods.P12
	room.call("teleport_player",Vector3(10.5,.05,-4.75))
	hero.request_open();await frames(70)
	check("hero_real_opening_midpoint",hero.get_state_name()==&"opening")
	await frames(90);check("hero_opens",hero.get_state_name()==&"open")
	room.call("teleport_player",hero.to_global(Vector3(0,.44,0)))
	await frames(15);hero.request_close();await frames(15)
	check("occupied_hero_cannot_close",hero.get_state_name()==&"open")
	room.call("teleport_player",Vector3(10.5,.05,-4.75))
	await frames(3) # Physics-space query must observe the actor's new transform.
	hero.request_close();await frames(160)
	check("hero_closes",hero.get_state_name()==&"closed")
	var room_closed_blend:float=room.get("complete_shell_materials")[0].get_shader_parameter("room_pose_blend")
	check("shell_closed_pose_tracks_hero",is_zero_approx(room_closed_blend))
	hero.request_open();await frames(160)
	check("hero_reopens",hero.get_state_name()==&"open")
	check("shell_open_pose_tracks_hero",is_equal_approx(float(room.get("complete_shell_materials")[0].get_shader_parameter("room_pose_blend")),1.0))
	# The original automatic chip door remains a real traversable route.
	room.call("teleport_player",Vector3(10.5,.05,-8.6));await frames(36)
	check("door_still_scans",room.get("feedback_state")=="scanning")
	await frames(330);check("door_still_authorizes",room.get("feedback_state")=="pass" and room.get("door_fraction")>.95)
	room.set("test_input",Vector2(0,-1));await frames(110);room.set("test_input",Vector2.ZERO)
	check("actor_crosses_automatic_door",room.get("player").global_position.z < -10.0)
	await frames(270);check("door_resets_after_pass",room.get("door_fraction")<.05 and room.get("feedback_state")=="idle")
	var report:={"result":"PASS" if errors.is_empty() else "FAIL","errors":errors,"checks":checks,"pods":pod_records,"physical_walks":walks,
		"lighting_assumption":"P12 animated endpoints; nineteen other pods closed and not player-interactable",
		"pixel_art_generated":false,"source_scene":room.scene_file_path}
	FileAccess.open(REPORT,FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print("R19_COMPLETE_RUNTIME ",report.result," checks=",checks.size()," walks=",walks.size()," errors=",JSON.stringify(errors))
	get_tree().quit(0 if errors.is_empty() else 1)
