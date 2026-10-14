extends SceneTree

const OUTPUT := "res://docs/art/experiments/room1_camera_bounds_test_r2/"
var samples: Array = []

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var room := (load("res://scenes/dev/room1_camera_bounds_test_r2.tscn") as PackedScene).instantiate()
	get_root().add_child(room)
	room.set_process(false)
	await process_frame
	var camera := room.get_node("ReviewCamera") as Camera3D
	var target := room.get_node("FollowTarget") as Node3D
	var fixed_basis := camera.basis
	var initial_camera := camera.position
	DirAccess.make_dir_recursive_absolute(OUTPUT)
	var names := ["01_center", "02_left", "03_right", "04_front", "05_back", "06_front_left", "07_front_right", "08_back_left", "09_back_right"]
	for index in room.EDGE_POSITIONS.size():
		target.position = room.EDGE_POSITIONS[index]
		room.update_follow_camera()
		assert(camera.basis.is_equal_approx(fixed_basis))
		assert(is_equal_approx(camera.position.y, room.camera_height_m))
		assert(camera.position.z >= room.minimum_camera_z_m - 0.0001 and camera.position.z <= room.maximum_camera_z_m + 0.0001)
		var bounds: Array = []
		# Project a box containing the entire marker, rather than just its center.
		for x in [-0.22, 0.22]:
			for y in [0.0, 1.65]:
				for z in [-0.22, 0.22]:
					var point := target.position + Vector3(x, y, z)
					assert(not camera.is_position_behind(point))
					var pixel := camera.unproject_position(point)
					assert(pixel.x > 0 and pixel.x < get_root().size.x and pixel.y > 0 and pixel.y < get_root().size.y, "Marker clips frame: " + names[index])
					bounds.append([pixel.x, pixel.y])
		samples.append({"name": names[index], "camera": [camera.position.x, camera.position.y, camera.position.z], "marker_projection": bounds})
		await _capture(names[index] + ".png")
	for node_name: String in room.SHADOW_ONLY_NAMES:
		var object := room.get_node("Shell").find_child(node_name, true, false) as MeshInstance3D
		assert(object.visible and object.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY)
	assert(room.get_node("Shell").find_child("Wall_left", true, false).visible)
	# The central corridor still follows exactly; a side edge stops the camera.
	target.position = room.START + Vector3(1, 0, 0)
	room.update_follow_camera()
	assert((camera.position - initial_camera).is_equal_approx(Vector3(1, 0, 0)))
	target.position = Vector3(0.55, 0, -4.75)
	room.update_follow_camera()
	var stopped := camera.position
	target.position.x = 0.8
	room.update_follow_camera()
	assert(camera.position.is_equal_approx(stopped))
	target.position = room.START + Vector3(0, 3, 0)
	target.rotation.y = 1.2
	room.update_follow_camera()
	assert(camera.position.is_equal_approx(initial_camera) and camera.basis.is_equal_approx(fixed_basis))
	target.position = room.START
	target.rotation = Vector3.ZERO
	room.update_follow_camera()
	# Render a control image to prove the invisible roof still occludes direct light.
	for node_name: String in room.SHADOW_ONLY_NAMES:
		room.get_node("Shell").find_child(node_name, true, false).visible = false
	await _capture("10_shadow_disabled_control.png")
	var shadow_readback := {}
	if DisplayServer.get_name() != "headless":
		var closed := Image.load_from_file(OUTPUT + "01_center.png")
		var control := Image.load_from_file(OUTPUT + "10_shadow_disabled_control.png")
		var closed_luminance := _floor_luminance(closed)
		var control_luminance := _floor_luminance(control)
		assert(control_luminance > closed_luminance + 0.03, "Shadow-only roof did not darken the floor")
		shadow_readback = {"closed_floor_luminance": closed_luminance, "hidden_roof_floor_luminance": control_luminance, "passed": true}
	var report := {"engine": Engine.get_version_info().string, "checks": {"whole_marker_inside_frame_at_9_positions": true, "height_and_orientation_locked": true, "center_follows_edge_stops": true, "side_walls_visible": true, "front_and_roof_shadow_only": true, "target_y_and_rotation_ignored": true}, "samples": samples, "scope": "Camera boundaries and shadow-only shell; no character physics or final lighting."}
	report["rendered_shadow_readback"] = shadow_readback
	var file := FileAccess.open(OUTPUT + "validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	file.close()
	print("ROOM1_BOUNDS_PASS: ", JSON.stringify(report.checks))
	room.queue_free()
	quit()

func _capture(filename: String) -> void:
	for frame in 8:
		await process_frame
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		assert(get_root().get_texture().get_image().save_png(OUTPUT + filename) == OK)

func _floor_luminance(image: Image) -> float:
	var total := 0.0
	var count := 0
	for y in range(550, 660, 8):
		for x in range(500, 780, 8):
			total += image.get_pixel(x, y).get_luminance()
			count += 1
	return total / count
