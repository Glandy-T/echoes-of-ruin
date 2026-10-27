extends SceneTree
func _initialize() -> void:
	call_deferred("capture")
func capture() -> void:
	var room: Node = load("res://scenes/dev/room1_surface_sample_r1.tscn").instantiate()
	room.lightmap_bake_override = "res://assets/art/room1_wall_finish_r4"
	get_root().add_child(room)
	for frame in 15: await process_frame
	room.position_surface_review()
	room.teleport_player(Vector3(10.5,0,-2))
	room._sync_render_camera()
	room._sync_bloom_camera()
	room.set_process(false)
	room.set_physics_process(false)
	room.info.get_parent().visible = false
	var states := ["on","off","restored"]
	for index in states.size():
		room.strip_on = index != 1
		room.apply_sample_state()
		for frame in 15: await process_frame
		await RenderingServer.frame_post_draw
		get_root().get_texture().get_image().save_png("res://docs/art/experiments/room1_wall_finish_r4/evidence/06_strip_"+states[index]+".png")
	print("STRIP_TOGGLE_CAPTURE_COMPLETE")
	quit()
