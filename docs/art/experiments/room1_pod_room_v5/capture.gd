extends SceneTree
const OUT := "res://docs/art/experiments/room1_pod_room_v5/evidence/"
var room: Node
var camera: Camera3D
var records: Array = []
func _initialize() -> void: call_deferred("capture")
func shot(name: String) -> void:
	for i in 18: await process_frame
	await RenderingServer.frame_post_draw
	var image := get_root().get_texture().get_image()
	assert(image.save_png(OUT+name+".png")==OK)
	records.append({"file":name+".png","new_pod":room.revised_pod,"open":room.open_pod,"glass":room.pane_visible,"reflection":room.reflection_on,"window_power":room.windows_on,"local_light":room.local_light_on,"strip":room.strip_on,"base_color":room.base_color_mode,"camera":[camera.global_position.x,camera.global_position.y,camera.global_position.z],"fov":camera.fov})
func look(pos: Vector3,target: Vector3,fov: float) -> void:
	camera.global_position=pos
	camera.look_at(target)
	camera.fov=fov
	room._sync_render_camera()
	room._sync_bloom_camera()
func game() -> void:
	room.teleport_player(Vector3(3.525,0,-4.75))
	camera.fov=50
	room._sync_render_camera()
	room._sync_bloom_camera()
func close_view() -> void:
	look(Vector3(1.775,1.8,-4.45),Vector3(3.65,.43,-7.65),44)
func head_view() -> void:
	look(Vector3(2.15,1.22,-8.9),Vector3(3.525,.53,-8.29),48)
func capture() -> void:
	var baseline=load("res://scenes/dev/room1_floor_palette_r9.tscn").instantiate()
	get_root().add_child(baseline)
	for i in 25: await process_frame
	baseline.position_structure_review()
	baseline.set_process(false)
	baseline.set_physics_process(false)
	baseline.info.get_parent().visible=false
	baseline.teleport_player(Vector3(3.525,0,-4.75))
	baseline.get_node("ReviewCamera").fov=50
	baseline._sync_render_camera()
	baseline._sync_bloom_camera()
	for i in 18: await process_frame
	await RenderingServer.frame_post_draw
	assert(get_root().get_texture().get_image().save_png(OUT+"original_r9_baseline.png")==OK)
	baseline.queue_free()
	for i in 5: await process_frame
	room=load("res://scenes/dev/room1_pod_room_v5.tscn").instantiate()
	get_root().add_child(room)
	if not room.has_method("set_pod_candidate"):push_error("v5 review failed to load");quit(2);return
	for i in 25: await process_frame
	room.position_structure_review()
	room.set_process(false)
	room.set_physics_process(false)
	room.info.get_parent().visible=false
	room.set_full_surface_mode(3)
	camera=room.get_node("ReviewCamera") as Camera3D
	room.set_pod_candidate(false,true)
	game();await shot("old_game_open")
	close_view();await shot("old_close_open")
	for opened in [false,true]:
		room.set_pod_candidate(true,opened)
		var pose:="open" if opened else "closed"
		game();await shot("new_game_"+pose)
		room.teleport_player(Vector3(4.8,0,-4.75));camera.fov=50;room._sync_render_camera();room._sync_bloom_camera();await shot("new_game_offset_"+pose)
		room.teleport_player(Vector3(3.525,0,-4.75))
		close_view();await shot("new_close_"+pose)
		look(Vector3(2.0,.95,-5.25),Vector3(3.6,.45,-7.6),47);await shot("new_side_"+pose)
		room.set_base_color_mode(true);await shot("base_color_"+pose)
		room.set_base_color_mode(false);await shot("new_side_"+pose+"_restored")
	room.set_pod_candidate(true,false)
	head_view();await shot("glass_powered")
	room.set_pane_visible(false);await shot("glass_hidden_control")
	room.set_pane_visible(true);room.windows_on=false;room.apply_sample_state();await shot("glass_unpowered")
	room.windows_on=true;room.reflection_on=false;room.apply_sample_state();await shot("glass_no_reflection_control")
	room.reflection_on=true;room.apply_sample_state();await shot("glass_restored")
	room.set_pod_candidate(true,true)
	close_view();room.strip_on=false;room.apply_sample_state();await shot("strip_off_control")
	room.strip_on=true;room.apply_sample_state();await shot("strip_restored")
	room.set_pod_candidate(false,true)
	game();await shot("old_game_restored")
	var runtime:={"strip_proxy_light_count":room.actual_strip_lights.size(),"ambient_energy":room.get_node("WorldEnvironment").environment.ambient_light_energy,"baked_energy":room.continuous_baked_energy,"pixel_size":[room.render_viewport.size.x,room.render_viewport.size.y],"p12_position":[room.get_node("Pods/P12").global_position.x,room.get_node("Pods/P12").global_position.y,room.get_node("Pods/P12").global_position.z],"pod_maps":[]}
	for item in room.pod_materials:
		runtime.pod_maps.append({"expected":item.irradiance.resource_path,"bound":item.material.get_shader_parameter("strip_irradiance").resource_path,"shader":item.material.shader.resource_path})
	FileAccess.open(OUT+"runtime_readback.json",FileAccess.WRITE).store_string(JSON.stringify(runtime))
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records))
	print("POD_ROOM_V5_CAPTURE_COMPLETE")
	quit()
