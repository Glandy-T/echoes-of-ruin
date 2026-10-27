extends SceneTree
func _initialize() -> void:
	call_deferred("capture")
func capture() -> void:
	var room: Node = load("res://scenes/dev/room1_surface_sample_r1.tscn").instantiate()
	room.lightmap_bake_override = "res://assets/art/room1_corner_quality_r3"
	get_root().add_child(room)
	for frame in 15: await process_frame
	room.position_surface_review()
	room.set_process(false)
	room.set_physics_process(false)
	room.info.get_parent().visible = false
	room.set_surface_sample_mode(0)
	for material in room.baked_receivers:
		material.set_shader_parameter("strip_irradiance",load("res://assets/art/room1_corner_quality_r3/strip_irradiance.exr"))
	for frame in 15: await process_frame
	await RenderingServer.frame_post_draw
	get_root().get_texture().get_image().save_png("res://docs/art/experiments/room1_corner_quality_r3/evidence/raw_1024.png")
	print("RAW_QUALITY_CAPTURE_COMPLETE")
	quit()
