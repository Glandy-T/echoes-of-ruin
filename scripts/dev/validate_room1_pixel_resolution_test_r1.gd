extends SceneTree
const OUTPUT := "res://docs/art/experiments/room1_pixel_resolution_test_r1/"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var room: Node = (load("res://scenes/dev/room1_pixel_resolution_test_r1.tscn") as PackedScene).instantiate()
	get_root().add_child(room)
	room.test_mode = true
	await process_frame
	for frame in 30:
		await physics_frame
	DirAccess.make_dir_recursive_absolute(OUTPUT)
	var report := {}
	for index in 3:
		room.set_pixel_mode(index)
		for frame in 12:
			await process_frame
		assert(room.render_viewport.size == room.PIXEL_SIZES[index])
		assert(room.presentation.texture_filter == CanvasItem.TEXTURE_FILTER_NEAREST)
		assert(room.render_camera.global_transform.is_equal_approx(room.get_node("ReviewCamera").global_transform))
		if DisplayServer.get_name() != "headless":
			await RenderingServer.frame_post_draw
			var rendered: Image = room.render_viewport.get_texture().get_image()
			assert(rendered.get_size() == room.PIXEL_SIZES[index])
			assert(rendered.save_png(OUTPUT + "native_%d.png" % index) == OK)
			var screenshot := get_root().get_texture().get_image()
			assert(screenshot.save_png(OUTPUT + "comparison_%d.png" % index) == OK)
			report[str(index)] = {"native_size": rendered.get_size(), "presentation_size": room.presentation.size}
	room.set_pixel_mode(1)
	room.test_input = Vector2(0, 1)
	room.teleport_player(Vector3(3.525, 0.05, -4.75))
	for frame in 120:
		await physics_frame
	room.test_input = Vector2.ZERO
	assert(room.player.position.z < -3.1 and room.player.position.z > -3.4)
	assert(is_equal_approx(room.get_node("ReviewCamera").position.y, room.camera_height_m))
	var file := FileAccess.open(OUTPUT + "validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"engine": Engine.get_version_info().string, "modes": report, "nearest_presentation": true, "camera_sync": true, "physics_block_in_low_resolution": true, "scope": "Rendering comparison only; UI at full resolution; no project settings or assets changed; pixel density not approved."}, "\t"))
	file.close()
	print("ROOM1_PIXEL_PASS: ", JSON.stringify(report))
	quit()
