extends SceneTree

const OUTPUT := "res://docs/art/experiments/room1_camera_follow_test_r1/"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var room := (load("res://scenes/dev/room1_camera_follow_test_r1.tscn") as PackedScene).instantiate()
	get_root().add_child(room)
	room.set_process(false)
	await process_frame
	var target := room.get_node("FollowTarget") as Node3D
	var camera := room.get_node("ReviewCamera") as Camera3D
	var fixed_basis := camera.basis
	var fixed_height := camera.position.y
	var starting_camera := camera.position
	DirAccess.make_dir_recursive_absolute(OUTPUT)
	var samples: Array = []
	for sample: Dictionary in [{"name": "01_center", "offset": Vector3.ZERO}, {"name": "02_left", "offset": Vector3(-3, 0, 0)}, {"name": "03_right", "offset": Vector3(3, 0, 0)}, {"name": "04_front", "offset": Vector3(0, 0, 1.2)}, {"name": "05_back", "offset": Vector3(0, 0, -1.2)}]:
		target.position = room.START + sample.offset
		room.update_follow_camera()
		room._update_info()
		assert(camera.basis.is_equal_approx(fixed_basis), "Camera rotated")
		assert(is_equal_approx(camera.position.y, fixed_height), "Camera moved vertically")
		assert((camera.position - starting_camera).is_equal_approx(sample.offset), "Camera did not track X/Z")
		var focus := target.global_position + Vector3(0, room.focus_height_m, 0)
		var screen := camera.unproject_position(focus)
		assert(screen.distance_to(Vector2(get_root().size) * 0.5) < 0.1, "Target left screen center")
		samples.append({"name": sample.name, "camera": [camera.position.x, camera.position.y, camera.position.z], "focus_screen_px": [screen.x, screen.y]})
		await _capture(sample.name + ".png")
	target.position = room.START + Vector3(0, 3, 0)
	target.rotation = Vector3(0.4, 1.0, 0.2)
	room.update_follow_camera()
	assert(camera.position.is_equal_approx(starting_camera), "Camera followed target Y")
	assert(camera.basis.is_equal_approx(fixed_basis), "Camera followed target rotation")
	target.position = room.START
	target.rotation = Vector3.ZERO
	room.move_marker(Vector2(1, 1), 1.0)
	assert(is_equal_approx(target.position.distance_to(room.START), room.marker_speed_m_s), "Diagonal movement faster")
	target.position = room.START
	room.update_follow_camera()
	room.get_node("FollowTarget/ScaleMarker").visible = false
	await _capture("06_reference_without_marker.png")
	var report := {"engine": Engine.get_version_info().string, "scope": "Camera only; no physics, lighting revision or protagonist art", "checks": {"xz_follow": true, "height_locked": true, "rotation_locked": true, "focus_stays_centered": true, "target_y_and_rotation_ignored": true, "normalized_diagonal_marker_movement": true}, "camera": {"projection": "perspective", "horizontal_fov": room.horizontal_fov_degrees, "height_m": fixed_height, "distance_m": room.camera_distance_m, "pitch_degrees": rad_to_deg(atan2(room.camera_height_m - room.focus_height_m, room.camera_distance_m))}, "samples": samples}
	var file := FileAccess.open(OUTPUT + "validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	file.close()
	print("ROOM1_CAMERA_PASS: ", JSON.stringify(report.checks))
	room.queue_free()
	quit()

func _capture(filename: String) -> void:
	for frame in 8:
		await process_frame
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		assert(get_root().get_texture().get_image().save_png(OUTPUT + filename) == OK)
