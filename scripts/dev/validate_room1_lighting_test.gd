extends SceneTree

const OUTPUT := "res://docs/art/experiments/room1_lighting_test_r1/"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var room := (load("res://scenes/dev/room1_lighting_test_r1.tscn") as PackedScene).instantiate()
	get_root().add_child(room)
	room.set_process(false)
	await process_frame
	assert(room.lighting_ready)
	assert(room.window_materials.size() == 20 and room.screen_materials.size() == 20)
	for pod in room.get_node("Pods").get_children():
		assert(pod.find_child("pod_v3_glass", true, false).get_active_material(0) == room.glass_materials[pod.name])
		assert(pod.find_child("pod_v3_display", true, false).get_active_material(0) == room.screen_materials[pod.name])
	var powered_windows: Array = []
	var powered_screens: Array = []
	for id in room.window_materials:
		if room.window_materials[id].emission_enabled:
			powered_windows.append(str(id))
		assert(room.glass_materials[id].transparency == BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS)
		assert(not room.glass_materials[id].emission_enabled)
		assert(room.window_materials[id].get_instance_id() != room.window_materials["P01"].get_instance_id() or str(id) == "P01")
	for id in room.screen_materials:
		if room.screen_materials[id].emission_enabled:
			powered_screens.append(str(id))
	assert(powered_windows.size() == 3 and powered_screens.size() == 3)
	assert(not room.get_node("ReviewLights").visible)
	var left := room.get_node("Shell").find_child("Wall_left", true, false) as MeshInstance3D
	var corrected_surfaces := 0
	for surface in left.mesh.get_surface_count():
		var material := left.get_surface_override_material(surface) as ShaderMaterial
		if material:
			var offset: Vector3 = material.get_shader_parameter("uv_offset")
			var arrays: Array = left.mesh.surface_get_arrays(surface)
			for uv: Vector2 in arrays[Mesh.ARRAY_TEX_UV]:
				var corrected := uv + Vector2(offset.x, offset.y)
				assert(corrected.x >= -0.0001 and corrected.x <= 1.0001 and corrected.y >= -0.0001 and corrected.y <= 1.0001)
			corrected_surfaces += 1
	assert(corrected_surfaces == 1)
	DirAccess.make_dir_recursive_absolute(OUTPUT)
	await _capture("01_center.png")
	room.get_node("FollowTarget").position = room.EDGE_POSITIONS[1]
	room.update_follow_camera()
	await _capture("02_left_wall_fixed.png")
	room.get_node("FollowTarget").position = Vector3(3.525, 0, -4.75)
	room.update_follow_camera()
	room.get_node("FollowTarget/ScaleMarker").visible = false
	await _capture("03_lit_pod.png")
	room.strip_on = false
	room.apply_lighting()
	room._update_info()
	await _capture("04_pod_lights_only.png")
	room.windows_on = false
	room.apply_lighting()
	room._update_info()
	await _capture("05_screen_only.png")
	room.screens_on = false
	room.apply_lighting()
	room._update_info()
	await _capture("06_all_emitters_off.png")
	for id in room.window_proxies:
		assert(not room.window_proxies[id].visible and not room.screen_proxies[id].visible)
	room.strip_on = true
	room.apply_lighting()
	room._update_info()
	await _capture("07_strip_only.png")
	var report := {"engine": Engine.get_version_info().string, "checks": {"left_wall_uv_in_0_1": true, "per_pod_materials_independent": true, "3_lit_17_unlit": true, "glass_alpha_depth_prepass": true, "old_point_bulbs_and_directional_fill_disabled": true, "individual_light_groups_switch_off": true}, "powered_windows": powered_windows, "powered_screens": powered_screens, "strip_surface_energy": room.strip_surface_energy, "strip_light_energy": room.strip_light_energy, "scope": "Lighting and glass candidate. Continuous strip is analytical fill, no GI or actual line-light shadows. Lit IDs are temporary."}
	var file := FileAccess.open(OUTPUT + "validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	file.close()
	print("ROOM1_LIGHTING_PASS: ", JSON.stringify(report.checks))
	room.queue_free()
	quit()

func _capture(filename: String) -> void:
	for frame in 12:
		await process_frame
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		assert(get_root().get_texture().get_image().save_png(OUTPUT + filename) == OK)
