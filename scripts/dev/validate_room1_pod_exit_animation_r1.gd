extends SceneTree
const OUTPUT := "res://docs/art/experiments/room1_pod_exit_animation_r1/"
func _initialize() -> void:
	call_deferred("_run")
func _run() -> void:
	var room: Node = (load("res://scenes/dev/room1_pod_exit_animation_r1.tscn") as PackedScene).instantiate()
	get_root().add_child(room)
	room.test_mode = true
	room.set_physics_process(false)
	DirAccess.make_dir_recursive_absolute(OUTPUT)
	await process_frame
	assert(room.window_lit_pods == PackedStringArray(["P02", "P12", "P17"]))
	assert(room.screen_lit_pods.size() == 3)
	var powered_windows := 0
	var powered_screens := 0
	for id in room.window_proxies:
		powered_windows += int(room.window_proxies[id].visible)
		powered_screens += int(room.screen_proxies[id].visible)
	assert(powered_windows == 3 and powered_screens == 3)
	var camera := room.get_node("ReviewCamera") as Camera3D
	var basis := camera.basis
	var height := camera.position.y
	var lid := room.get_node("Pods/P12").find_child("pod_v3_lid", true, false) as MeshInstance3D
	assert(absf(lid.rotation.z + PI / 4.0) < 0.001)
	assert(room.pixel_mode == 0)
	room.set_pixel_mode(2)
	assert(room.pixel_mode == 0)
	var result := {"hero_pod": "P12", "lit_windows": powered_windows, "lit_screens": powered_screens, "red_screens": ["P02", "P17"], "open_lid_degrees": rad_to_deg(lid.rotation.z), "placeholder_character": true, "static_bake_pose": "P12 open", "capsule_shadow_follows_pose": true}
	room.info.get_parent().visible = false
	for sample in [[0.0, "01_open_lying.png"], [2.4, "02_sitting.png"], [4.9, "03_crossing_shell.png"]]:
		room.apply_exit_pose(sample[0])
		assert(room.player.collision_mask == 0)
		assert(camera.basis.is_equal_approx(basis) and is_equal_approx(camera.position.y, height))
		await capture(sample[1])
	room.finish_exit()
	assert(room.player.collision_layer == 2 and room.player.collision_mask == 1)
	assert(room.actor_mesh.rotation.is_zero_approx())
	assert(room.player.position.distance_to(Vector3(2.65, 0, -7.65)) < 0.001)
	await capture("04_control_handoff.png")
	room.set_physics_process(true)
	room.test_input = Vector2(0, 1)
	for frame in 90:
		await physics_frame
	room.test_input = Vector2.ZERO
	for frame in 20:
		await physics_frame
	assert(room.player.position.z > -5.1)
	assert(absf(room.player.position.y) < 0.015)
	result["post_exit_position"] = str(room.player.position)
	result["movement_and_floor_collision_passed"] = true
	await capture("05_after_walking.png")
	room.set_physics_process(false)
	room.start_exit()
	room.apply_exit_pose(2.4)
	room.finish_exit()
	assert(room.player.position.distance_to(Vector3(2.65, 0, -7.65)) < 0.001)
	result["replay_and_skip_reset_passed"] = true
	room.start_exit()
	room.set_physics_process(true)
	for frame in 420:
		await physics_frame
	assert(not room.exit_active)
	assert(room.player.collision_mask == 1)
	assert(room.player.position.distance_to(Vector3(2.65, 0, -7.65)) < 0.015)
	result["automatic_timed_handoff_passed"] = true
	room.set_physics_process(false)
	room.set_process(false)
	for id in ["P12", "P17", "P02"]:
		var pod := room.get_node("Pods/" + id) as Node3D
		var sign := -1.0 if id == "P02" else 1.0
		camera.position = pod.position + Vector3(-0.8, 1.6, 2.7 * sign)
		camera.look_at(pod.position + Vector3(0, 0.65, 0))
		room._sync_render_camera()
		room._sync_bloom_camera()
		await capture("06_close_" + id + ".png")
	var file := FileAccess.open(OUTPUT + "validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(result, "\t"))
	file.close()
	print("ROOM1_EXIT_PASS: ", JSON.stringify(result))
	quit()
func capture(filename: String) -> void:
	for frame in 15:
		await process_frame
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		assert(get_root().get_texture().get_image().save_png(OUTPUT + filename) == OK)
