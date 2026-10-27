extends SceneTree
const OUT := "res://docs/art/experiments/room1_floor_palette_r9/evidence/"
var room: Node
var camera: Camera3D
var records: Array = []
func _initialize() -> void: call_deferred("capture")
func _shot(name: String) -> void:
	for i in 15: await process_frame
	await RenderingServer.frame_post_draw
	var image := get_root().get_texture().get_image()
	assert(image.save_png(OUT+name+".png")==OK)
	records.append({"file":name+".png","new_palette":room.floor_contact_enabled,"new_gi":room.surface_lighting_enabled,"base_color":room.base_color_mode,"camera":[camera.global_position.x,camera.global_position.y,camera.global_position.z],"fov":camera.fov})
func _look(pos: Vector3,target: Vector3,fov: float=52.0) -> void:
	camera.global_position=pos;camera.look_at(target);camera.fov=fov;room._sync_render_camera();room._sync_bloom_camera()
func _game() -> void:
	room.teleport_player(Vector3(17.475,0,-4.75));camera.fov=50;room._sync_render_camera();room._sync_bloom_camera()
func capture() -> void:
	room=load("res://scenes/dev/room1_floor_palette_r9.tscn").instantiate();get_root().add_child(room)
	for i in 20: await process_frame
	room.position_structure_review();room.set_process(false);room.set_physics_process(false);room.info.get_parent().visible=false
	room.set_full_surface_mode(3);camera=room.get_node("ReviewCamera") as Camera3D
	for mode in [0,1,2]:
		room.set_floor_contact(mode>0);room.set_surface_lighting(mode==2)
		_game()
		_look(Vector3(4.125,2.25,.7),Vector3(1.775,.18,-1.85));await _shot(["pod_r8_original","pod_r9_same_light","pod_r9_final"][mode])
		_game();await _shot(["game_r8_original","game_r9_same_light","game_r9_final"][mode])
	room.set_base_color_mode(true);await _shot("game_r9_base_color")
	room.set_base_color_mode(false);await _shot("game_r9_after_n")
	room.set_floor_contact(false);room.set_floor_contact(true);await _shot("game_r9_after_f")
	room.set_surface_lighting(false);room.set_surface_lighting(true);await _shot("game_r9_after_i")
	room.set_base_color_mode(true)
	for enabled in [false,true]:
		room.set_floor_contact(enabled);_look(Vector3(10.5,24,-1),Vector3(10.5,0,-4.75),53);await _shot("floor_r9_base_color" if enabled else "floor_r8_base_color")
	room.set_base_color_mode(false)
	_look(Vector3(7.625,2.25,.7),Vector3(5.275,.18,-1.85));await _shot("leak_r9_final")
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records))
	print("FLOOR_PALETTE_R9_CAPTURE_COMPLETE");quit()
