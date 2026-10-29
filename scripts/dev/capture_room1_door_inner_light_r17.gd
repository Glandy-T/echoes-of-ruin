extends Node

const OUT:="res://docs/art/experiments/room1_door_inner_light_r17/evidence/"
var room:Node3D
var camera:Camera3D
var report:Array=[]

func _ready() -> void:call_deferred("_capture")

func _state(fraction:float,valid:bool=true,chip:bool=true,occupied:bool=false) -> void:
	room.set("door_fraction",fraction);room.set("pass_valid",valid)
	room.set("chip_enabled",chip);room.set("door_occupied",occupied)
	room.set("scan_complete",valid)
	(room.get("door_mesh") as Node3D).global_position=room.get("door_closed_position")+Vector3(1.52*fraction,0,0)
	(room.get("door_body") as Node3D).global_position=room.get("body_closed_position")+Vector3(1.52*fraction,0,0)
	room.call("_update_feedback")

func _save(name:String) -> void:
	room.call("_sync_render_camera");room.call("_sync_bloom_camera")
	for i in 12:await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var frame:=get_viewport().get_texture().get_image()
	assert(frame!=null)
	assert(frame.save_png(OUT+name+".png")==OK)
	var material:ShaderMaterial=room.get("inner_light_material")
	report.append({"image":name+".png","resolution":[frame.get_width(),frame.get_height()],
		"fixed":room.get("inner_light_fixed"),"door_fraction":room.get("door_fraction"),
		"state":room.get("feedback_state"),"power":material.get_shader_parameter("passage_power"),
		"leaf_min_x":material.get_shader_parameter("leaf_min_x"),"leaf_max_x":material.get_shader_parameter("leaf_max_x"),
		"camera":str(camera.global_transform),"fov":camera.fov})
	print("R17_SHOT ",name)

func _capture() -> void:
	room=get_parent() as Node3D
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	for i in 10:await get_tree().process_frame
	room.call("finish_exit");room.call("teleport_player",Vector3(10.5,0.05,-7.7))
	for i in 10:await get_tree().process_frame
	room.set_process(false);room.set_physics_process(false)
	for key in ["paper_hero","bloom_paper_hero"]:
		var paper:Sprite3D=room.get(key)
		if paper:paper.visible=false
	var info:Label=room.get("info")
	if info:info.get_parent().visible=false
	var ui:Node=room.get("review_ui")
	if ui:
		var pause:Control=ui.get("pause_button")
		if pause:pause.visible=false
	camera=room.get_node("ReviewCamera") as Camera3D
	var game_transform:=camera.global_transform
	var game_fov:=camera.fov
	for fixed in [false,true]:
		room.call("set_inner_light_fix",fixed)
		var prefix:="fixed_" if fixed else "old_"
		for fraction in [0.0,0.2,0.5,1.0]:
			_state(fraction)
			await _save(prefix+"game_"+str(roundi(fraction*100)))
	# Technical closer angles use same scene lighting, never saved into the game camera.
	room.call("set_inner_light_fix",true)
	for fraction in [0.0,0.2,0.5,1.0]:
		_state(fraction)
		(room.get("inner_light_material") as ShaderMaterial).set_shader_parameter("passage_power",0.0)
		await _save("emitter_off_game_"+str(roundi(fraction*100)))
	_state(0.0)
	(room.get("inner_light_material") as ShaderMaterial).set_shader_parameter("passage_power",1.0)
	await _save("covered_leaf_forced_power")
	_state(0.5);await _save("fixed_closing_50")
	camera.fov=55
	for angle in ["front","left","right"]:
		camera.global_position=Vector3(10.5 if angle=="front" else (8.9 if angle=="left" else 12.1),1.7,-4.4)
		camera.look_at(Vector3(10.5,1.2,-9.43),Vector3.UP)
		for fraction in [0.2,0.5,1.0]:
			_state(fraction)
			await _save("fixed_"+angle+"_"+str(roundi(fraction*100)))
	_state(0.0,false,true,false);await _save("fixed_idle")
	_state(0.0,false,true,true);await _save("fixed_scanning")
	_state(0.0,false,false,true);await _save("fixed_denied_window_only")
	camera.global_transform=game_transform;camera.fov=game_fov
	var file:=FileAccess.open(OUT+"capture_states.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"\t"));file.close()
	get_tree().quit()
