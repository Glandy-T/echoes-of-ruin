extends SceneTree
const OUTPUT := "res://docs/art/experiments/room1_pixel_motion_test_r2/"
var room: Node

func _initialize() -> void:
	call_deferred("_run")

func sample_steps(smoothing: bool) -> Dictionary:
	room.motion_smoothing = smoothing
	room.teleport_player(Vector3(6, 0.01, -4.75))
	room.test_input = Vector2.RIGHT
	for frame in 30:
		await process_frame
	var last: Vector3 = room.render_camera.position
	var maximum_step := 0.0
	var stalls := 0
	var reversed := 0
	for frame in 90:
		await process_frame
		var now: Vector3 = room.render_camera.position
		var step := now.x - last.x
		maximum_step = maxf(maximum_step, absf(step))
		if absf(step) < 0.000001:
			stalls += 1
		if step < -0.000001:
			reversed += 1
		assert(is_equal_approx(now.y, room.camera_height_m))
		assert(room.render_camera.basis.is_equal_approx(room.locked_basis))
		last = now
	return {"maximum_step_m": maximum_step, "stationary_frames": stalls, "reversed_frames": reversed}

func _run() -> void:
	room = (load("res://scenes/dev/room1_pixel_motion_test_r2.tscn") as PackedScene).instantiate()
	get_root().add_child(room)
	room.test_mode = true
	await process_frame
	var old_ticks := Engine.physics_ticks_per_second
	var old_fps := Engine.max_fps
	Engine.physics_ticks_per_second = 10
	Engine.max_fps = 120
	var baseline := await sample_steps(false)
	var interpolated := await sample_steps(true)
	assert(interpolated.maximum_step_m < baseline.maximum_step_m)
	assert(interpolated.stationary_frames < baseline.stationary_frames)
	assert(interpolated.reversed_frames == 0)
	Engine.physics_ticks_per_second = old_ticks
	Engine.max_fps = old_fps
	room.test_input = Vector2.ZERO
	room.teleport_player(room.START + Vector3(0, 0.05, 0))
	room.motion_smoothing = true
	DirAccess.make_dir_recursive_absolute(OUTPUT)
	for mode in [0, 1]:
		room.set_pixel_mode(mode)
		for frame in 16:
			await process_frame
		if DisplayServer.get_name() != "headless":
			await RenderingServer.frame_post_draw
			assert(get_root().get_texture().get_image().save_png(OUTPUT + "preview_%d.png" % mode) == OK)
	room.teleport_player(Vector3(3.525, 0.05, -4.75))
	room.test_input = Vector2.DOWN
	for frame in 130:
		await physics_frame
	assert(room.player.position.z < -3.1 and room.player.position.z > -3.4)
	room.teleport_player(Vector3(12, 0.05, -4.75))
	assert(room.previous_physics_position.is_equal_approx(room.current_physics_position))
	var file := FileAccess.open(OUTPUT + "validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"baseline_10hz": baseline, "interpolated_10hz": interpolated, "collision_preserved": true, "teleport_resets_history": true, "scope": "Render interpolation only. Low-resolution perspective aliasing remains. Default native resolution."}, "\t"))
	file.close()
	print("ROOM1_MOTION_PASS: ", JSON.stringify(baseline), " -> ", JSON.stringify(interpolated))
	quit()
