extends Node

const OUT:="res://docs/art/experiments/room1_door_soft_glow_r18/evidence/"
var room:Node3D
var camera:Camera3D
var records:Array=[]

func _ready() -> void:call_deferred("_capture")

func _state(fraction:float,authorized:bool=true) -> void:
	room.set("door_fraction",fraction);room.set("pass_valid",authorized)
	room.set("chip_enabled",true);room.set("door_occupied",false)
	room.set("scan_complete",authorized)
	(room.get("door_mesh") as Node3D).global_position=room.get("door_closed_position")+Vector3(1.52*fraction,0,0)
	(room.get("door_body") as Node3D).global_position=room.get("body_closed_position")+Vector3(1.52*fraction,0,0)
	room.call("_update_feedback")

func _shot(name:String) -> void:
	room.call("_sync_render_camera");room.call("_sync_bloom_camera");room.call("_sync_door_glow")
	for i in 15:await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image:=get_viewport().get_texture().get_image()
	assert(image.save_png(OUT+name+".png")==OK)
	var source:SubViewport=room.get("door_glow_source")
	assert(source.get_texture().get_image().save_png(OUT+name+"_source.png")==OK)
	records.append({"file":name+".png","halo":room.get("door_glow_on"),"fraction":room.get("door_fraction"),"camera":str(camera.global_transform),"fov":camera.fov,"output":[image.get_width(),image.get_height()],"mask_size":[source.size.x,source.size.y]})
	print("R18_SHOT ",name)

func _capture() -> void:
	room=get_parent() as Node3D
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	for i in 10:await get_tree().process_frame
	room.call("finish_exit");room.call("teleport_player",Vector3(10.5,0.05,-7.7))
	for i in 10:await get_tree().process_frame
	room.set_process(false);room.set_physics_process(false)
	for key in ["paper_hero","bloom_paper_hero"]:
		var hero:Sprite3D=room.get(key)
		if hero:hero.visible=false
	var info:Label=room.get("info")
	if info:info.get_parent().visible=false
	var ui:Node=room.get("review_ui")
	if ui and ui.get("pause_button"):(ui.get("pause_button") as Control).visible=false
	camera=room.get_node("ReviewCamera") as Camera3D
	for soft in [false,true]:
		room.call("set_door_glow",soft)
		for fraction in [0.0,0.2,0.5,1.0]:
			_state(fraction)
			await _shot(("soft_" if soft else "core_")+"game_"+str(roundi(fraction*100)))
	camera.fov=55
	for angle in ["front","left","right"]:
		camera.global_position=Vector3(10.5 if angle=="front" else (8.9 if angle=="left" else 12.1),1.7,-4.4)
		camera.look_at(Vector3(10.5,1.2,-9.43),Vector3.UP)
		_state(0.5 if angle!="front" else 1.0)
		for soft in [false,true]:
			room.call("set_door_glow",soft)
			await _shot(("soft_" if soft else "core_")+angle)
	# A paper actor must also cut the visible-source mask, including alpha.
	camera.global_position=Vector3(10.5,1.7,-4.4)
	camera.look_at(Vector3(10.5,1.2,-9.43),Vector3.UP)
	_state(1.0)
	var actor:Sprite3D=room.get("paper_hero")
	var saved_actor:=actor.global_transform
	actor.visible=true
	actor.global_position=Vector3(9.83,actor.global_position.y,-8.5)
	for soft in [false,true]:
		room.call("set_door_glow",soft)
		await _shot(("soft_" if soft else "core_")+"actor_occlusion")
	actor.visible=false;actor.global_transform=saved_actor
	# Six established row/column game positions: halo must remain local to door.
	camera.fov=50
	for row_z in [-4.75,-8.0]:
		for column_x in [3.525,10.5,17.475]:
			room.call("teleport_player",Vector3(column_x,0.05,row_z))
			for soft in [false,true]:
				room.call("set_door_glow",soft)
				await _shot(("soft_" if soft else "core_")+"room_"+str(column_x)+"_"+str(row_z))
	_state(0.0,false)
	await _shot("idle_restored")
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"\t"))
	get_tree().quit()
