extends SceneTree
const OUT:="res://docs/art/experiments/room1_pod_standard_v8/evidence/"
var room:Node
var camera:Camera3D
var pod:Node3D
var records:Array=[]
func _initialize()->void:call_deferred("capture")
func shot(name:String)->void:
	for i in 12:
		room._sync_actor_shadow()
		room._sync_standard_visuals()
		await process_frame
	await RenderingServer.frame_post_draw
	assert(get_root().get_texture().get_image().save_png(OUT+name+".png")==OK)
	records.append({"file":name+".png","state":pod.get_state_name(),"tubes":pod.tube_powered,"screen":pod.screen_powered,"camera":[camera.global_position.x,camera.global_position.y,camera.global_position.z],"fov":camera.fov})
func look(pos:Vector3,target:Vector3,fov:float)->void:
	camera.global_position=pos;camera.look_at(target);camera.fov=fov
	room._sync_render_camera();room._sync_bloom_camera()
func close_view()->void:look(Vector3(1.775,1.8,-4.45),Vector3(3.65,.43,-7.65),44)
func head_view()->void:look(Vector3(2.15,1.22,-8.9),Vector3(3.525,.53,-8.29),48)
func capture()->void:
	room=load("res://scenes/dev/room1_pod_standard_v8_review.tscn").instantiate();get_root().add_child(room)
	if not room.has_method("_sync_standard_visuals"):push_error("Standard review failed to load");quit(2);return
	for i in 25:await process_frame
	room.position_structure_review();room.set_process(false);room.set_physics_process(false)
	room.info.get_parent().visible=false;camera=room.get_node("ReviewCamera") as Camera3D;pod=room.standard
	for opened in [false,true]:
		pod.set_open_immediate(opened);close_view();await shot("new_open" if opened else "new_closed")
		room.teleport_player(Vector3(4.8,0,-4.75));camera.fov=50;room._sync_render_camera();room._sync_bloom_camera()
		await shot("game_open" if opened else "game_closed")
		room.teleport_player(Vector3(3.525,0,-4.75))
	close_view()
	for i in 11:
		pod.set_open_progress(float(i)/10.0)
		await shot("animation_%02d"%i)
	pod.set_open_immediate(true);close_view()
	pod.set_screen_powered(false);await shot("screen_off_tubes_on")
	pod.set_screen_powered(true);pod.set_tube_powered(false);await shot("screen_on_tubes_off")
	pod.set_tube_powered(true);await shot("open_controls_restored")
	look(Vector3(4.1,1.1,-5.4),Vector3(3.525,.56,-6.58),38)
	await shot("screen_default_placeholder")
	pod.set_screen_background(Color("526c76"),0.0);await shot("screen_black_reference")
	pod.set_screen_background(Color("526c76"),0.8);await shot("screen_background_restored")
	pod.set_screen_state("TEST 12","STANDBY",.65,.35,.8);await shot("screen_data_example")
	pod.set_screen_state("----","----",0.0,0.0,0.0)
	look(Vector3(3.05,.9,-7.0),Vector3(3.525,.56,-6.6),55);await shot("foot_end_interior_open")
	pod.set_open_immediate(false);head_view();await shot("glass_powered")
	pod.set_glass_visible(false);await shot("glass_hidden_control")
	pod.set_glass_visible(true);pod.set_tube_powered(false);await shot("glass_tubes_off")
	pod.set_tube_powered(true);await shot("glass_restored")
	# Replay the real controller, not a second static model swap.
	pod.set_open_immediate(false);pod.request_open()
	await create_timer(2.5).timeout
	close_view();await shot("real_animation_finished")
	var proxy:Light3D=room.window_proxies["P12"]
	FileAccess.open(OUT+"runtime_readback.json",FileAccess.WRITE).store_string(JSON.stringify({"state":pod.get_state_name(),"source":pod.scene_file_path,"old_p12_hidden":not room.get_node("Pods/P12").visible,"old_p12_collisions_removed":room.original_p12_collision_count,"old_point_light_visible":proxy.visible,"old_point_light_energy":proxy.light_energy,"ambient_energy":room.get_node("WorldEnvironment").environment.ambient_light_energy,"strip_energy":room.continuous_baked_energy,"strip_proxy_count":room.actual_strip_lights.size(),"screen_background_energy":pod.screen_background_energy,"screen_background_tint":pod.screen_background_tint.to_html(false)}))
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records))
	print("POD_STANDARD_V8_CAPTURE_COMPLETE");quit()
