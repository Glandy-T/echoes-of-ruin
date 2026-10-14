extends SceneTree

const OUTPUT := "res://docs/art/experiments/room1_lighting_shadow_test_r2/"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var room := (load("res://scenes/dev/room1_lighting_shadow_test_r2.tscn") as PackedScene).instantiate()
	get_root().add_child(room)
	await process_frame
	room.movement_view = false
	room.get_node("FollowTarget/ScaleMarker").visible = false
	assert(room.actual_strip_lights.size() == 14)
	assert(room.floor_chunk_count == 10)
	assert(room.room_screen_shaders.size() == 20)
	assert(room.window_lit_pods.size() == 3 and room.screen_lit_pods.size() == 3)
	for material in room.strip_materials:
		assert(material.get_shader_parameter("strip_light_energy") == 0.0)
	for id in room.window_backers:
		assert(not room.window_backers[id].visible)
	DirAccess.make_dir_recursive_absolute(OUTPUT)
	await capture("01_center.png")
	room.shadows_on = false
	room.apply_sample_state()
	await capture("02_center_no_strip_shadows.png")
	room.shadows_on = true
	room.strip_on = false
	room.apply_sample_state()
	await capture("03_pods_only.png")
	room.windows_on = false
	room.screens_on = false
	room.apply_sample_state()
	await capture("04_all_lights_off.png")
	room.strip_on = true
	room.apply_sample_state()
	await capture("05_strip_only.png")
	room.windows_on = true
	room.screens_on = true
	room.apply_sample_state()
	room.get_node("FollowTarget").position = Vector3(3.525, 0, -4.75)
	room.update_follow_camera()
	await capture("06_left_lit_pods.png")
	room.shadows_on = false
	room.apply_sample_state()
	await capture("07_left_no_strip_shadows.png")
	room.shadows_on = true
	room.apply_sample_state()
	room.get_node("FollowTarget").position = room.EDGE_POSITIONS[2]
	room.update_follow_camera()
	await capture("08_right.png")
	room.get_node("FollowTarget").position = room.EDGE_POSITIONS[4]
	room.update_follow_camera()
	await capture("09_back.png")
	var differences := {}
	if DisplayServer.get_name() != "headless":
		differences["actual_strip_contribution"] = difference("01_center.png", "03_pods_only.png")
		differences["center_strip_shadows"] = difference("01_center.png", "02_center_no_strip_shadows.png")
		differences["left_strip_shadows"] = difference("06_left_lit_pods.png", "07_left_no_strip_shadows.png")
		for value in differences.values():
			assert(value > 0.00005)
	var file := FileAccess.open(OUTPUT + "validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"engine": Engine.get_version_info().string, "ambient": room.room_ambient_energy, "light_energy": room.actual_strip_energy, "strip_spots": 8, "strip_omnis": 6, "analytical_fill_disabled": true, "backers_hidden": true, "lit_ids": room.window_lit_pods, "readback": differences, "scope": "Room lighting candidate, overlapping shadowed positional lights approximate a strip; local only, art review pending."}, "\t"))
	file.close()
	print("ROOM1_LIGHTING_SHADOW_R2_PASS: ", JSON.stringify(differences))
	room.queue_free()
	quit()

func capture(filename: String) -> void:
	for frame in 16:
		await process_frame
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		assert(get_root().get_texture().get_image().save_png(OUTPUT + filename) == OK)

func difference(a: String, b: String) -> float:
	var first := Image.load_from_file(OUTPUT + a)
	var second := Image.load_from_file(OUTPUT + b)
	var total := 0.0
	var count := 0
	for y in range(140, first.get_height(), 4):
		for x in range(0, first.get_width(), 4):
			var delta := first.get_pixel(x, y) - second.get_pixel(x, y)
			total += (absf(delta.r) + absf(delta.g) + absf(delta.b)) / 3.0
			count += 1
	return total / count
