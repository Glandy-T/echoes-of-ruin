extends SceneTree
const OUT := "res://docs/art/experiments/room1_pod_chamber_v6/evidence/"
var room: Node
var camera: Camera3D
var records: Array = []
func _initialize() -> void:call_deferred("capture")
func shot(name: String) -> void:
	for i in 18:await process_frame
	await RenderingServer.frame_post_draw
	assert(get_root().get_texture().get_image().save_png(OUT+name+".png")==OK)
	records.append({"file":name+".png","dim":room.dim_chamber,"open":room.open_pod,"glass":room.pane_visible,"reflections":room.reflection_on,"windows":room.windows_on,"base_color":room.base_color_mode,"intensity":room.chamber_intensity if room.dim_chamber else 6.0,"proxy_energy":room.window_proxies["P12"].light_energy,"camera":[camera.global_position.x,camera.global_position.y,camera.global_position.z],"fov":camera.fov})
func look(pos: Vector3,target: Vector3,fov: float) -> void:
	camera.global_position=pos;camera.look_at(target);camera.fov=fov
	room._sync_render_camera();room._sync_bloom_camera()
func close_view() -> void:look(Vector3(1.775,1.8,-4.45),Vector3(3.65,.43,-7.65),44)
func head_view() -> void:look(Vector3(2.15,1.22,-8.9),Vector3(3.525,.53,-8.29),48)
func capture() -> void:
	room=load("res://scenes/dev/room1_pod_chamber_v6.tscn").instantiate();get_root().add_child(room)
	if not room.has_method("set_dim_chamber"):push_error("v6 failed to load");quit(2);return
	for i in 25:await process_frame
	room.position_structure_review();room.set_process(false);room.set_physics_process(false)
	room.info.get_parent().visible=false;camera=room.get_node("ReviewCamera") as Camera3D
	for dim in [false,true]:
		room.set_dim_chamber(dim)
		for opened in [false,true]:
			room.set_pod_candidate(true,opened);close_view()
			await shot(("new_" if dim else "old_")+("open" if opened else "closed"))
			if not opened:
				head_view();await shot("new_glass" if dim else "old_glass")
	for opened in [false,true]:
		room.set_pod_candidate(true,opened);room.teleport_player(Vector3(4.8,0,-4.75));camera.fov=50
		room._sync_render_camera();room._sync_bloom_camera();await shot("game_open" if opened else "game_closed")
	room.teleport_player(Vector3(3.525,0,-4.75));room.set_pod_candidate(true,false);head_view()
	room.set_pane_visible(false);await shot("glass_hidden_control")
	room.set_pane_visible(true);room.windows_on=false;room.apply_sample_state();await shot("inner_light_off_control")
	room.windows_on=true;room.reflection_on=false;room.apply_sample_state();await shot("reflection_off_control")
	room.reflection_on=true;room.apply_sample_state();await shot("glass_restored")
	room.set_pod_candidate(true,true);close_view();room.set_base_color_mode(true);await shot("open_base_color")
	room.set_base_color_mode(false);await shot("open_after_n")
	room.set_dim_chamber(false);room.set_dim_chamber(true);await shot("open_after_u")
	var energies:={}
	for id in ["P02","P12","P17"]:energies[id]=room.window_proxies[id].light_energy
	FileAccess.open(OUT+"runtime_readback.json",FileAccess.WRITE).store_string(JSON.stringify({"ambient_energy":room.get_node("WorldEnvironment").environment.ambient_light_energy,"strip_energy":room.continuous_baked_energy,"screen_core_energy":room.screen_core_energy,"chamber_proxies":energies,"glass_shader":room.pod_glass[0].get_active_material(0).shader.resource_path,"chamber_gain":room.chamber_intensity,"strip_proxy_count":room.actual_strip_lights.size()}))
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records))
	print("POD_CHAMBER_V6_CAPTURE_COMPLETE");quit()
