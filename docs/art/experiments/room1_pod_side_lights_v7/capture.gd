extends SceneTree
const OUT:="res://docs/art/experiments/room1_pod_side_lights_v7/evidence/"
var room:Node
var camera:Camera3D
var records:Array=[]
func _initialize()->void:call_deferred("capture")
func shot(name:String)->void:
	for i in 18:await process_frame
	await RenderingServer.frame_post_draw
	assert(get_root().get_texture().get_image().save_png(OUT+name+".png")==OK)
	records.append({"file":name+".png","open":room.open_pod,"glass":room.pane_visible,"tubes":room.side_tubes_enabled,"windows":room.windows_on,"reflections":room.reflection_on,"camera":[camera.global_position.x,camera.global_position.y,camera.global_position.z],"fov":camera.fov})
func look(pos:Vector3,target:Vector3,fov:float)->void:
	camera.global_position=pos;camera.look_at(target);camera.fov=fov
	room._sync_render_camera();room._sync_bloom_camera()
func close_view()->void:look(Vector3(1.775,1.8,-4.45),Vector3(3.65,.43,-7.65),44)
func head_view()->void:look(Vector3(2.15,1.22,-8.9),Vector3(3.525,.53,-8.29),48)
func capture()->void:
	room=load("res://scenes/dev/room1_pod_side_lights_v7.tscn").instantiate();get_root().add_child(room)
	if not room.has_method("apply_sample_state"):quit(2);return
	for i in 25:await process_frame
	room.position_structure_review();room.set_process(false);room.set_physics_process(false)
	room.info.get_parent().visible=false;camera=room.get_node("ReviewCamera") as Camera3D
	for opened in [false,true]:
		room.set_pod_candidate(true,opened);close_view();await shot("new_open" if opened else "new_closed")
		room.teleport_player(Vector3(4.8,0,-4.75));camera.fov=50;room._sync_render_camera();room._sync_bloom_camera()
		await shot("game_open" if opened else "game_closed")
		room.teleport_player(Vector3(3.525,0,-4.75))
	room.set_pod_candidate(true,true);look(Vector3(2.4,1.7,-5.6),Vector3(3.525,.28,-7.65),52);await shot("bed_and_side_tubes")
	room.side_tubes_enabled=false;room.apply_sample_state();await shot("bed_tubes_off_control")
	room.side_tubes_enabled=true;room.apply_sample_state();await shot("bed_tubes_restored")
	look(Vector3(3.525,1.35,-9.0),Vector3(3.525,.3,-7.6),56);await shot("head_end_both_sides")
	room.set_pod_candidate(true,false);head_view();await shot("glass_powered")
	room.set_pane_visible(false);await shot("glass_hidden_control")
	room.set_pane_visible(true);room.windows_on=false;room.apply_sample_state();await shot("glass_unpowered")
	room.windows_on=true;room.reflection_on=false;room.apply_sample_state();await shot("glass_no_reflection_control")
	room.reflection_on=true;room.apply_sample_state();await shot("glass_restored")
	var lights:={}
	for id in ["P02","P12","P17"]:lights[id]={"energy":room.window_proxies[id].light_energy,"visible":room.window_proxies[id].visible}
	var tubes:Array=[]
	for pose in room.pod_candidates:
		for child in room.pod_candidates[pose].find_children("InnerTube*","MeshInstance3D",true,false):
			if str(child.name).begins_with("InnerTube"):
				tubes.append({"pose":pose,"name":str(child.name),"position":[child.position.x,child.position.y,child.position.z],"size":[child.mesh.size.x,child.mesh.size.y,child.mesh.size.z]})
	FileAccess.open(OUT+"runtime_readback.json",FileAccess.WRITE).store_string(JSON.stringify({"chamber_proxies":lights,"ambient_energy":room.get_node("WorldEnvironment").environment.ambient_light_energy,"strip_energy":room.continuous_baked_energy,"strip_proxy_count":room.actual_strip_lights.size(),"fixtures":tubes,"interior_shaders":room.side_light_materials.size(),"glass_shader":room.pod_glass[0].get_active_material(0).shader.resource_path}))
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records))
	print("POD_SIDE_LIGHTS_V7_CAPTURE_COMPLETE");quit()
