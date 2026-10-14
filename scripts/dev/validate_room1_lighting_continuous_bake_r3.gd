extends SceneTree

const OUTPUT := "res://docs/art/experiments/room1_lighting_continuous_bake_r3/"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var room := (load("res://scenes/dev/room1_lighting_continuous_bake_r3.tscn") as PackedScene).instantiate()
	get_root().add_child(room)
	await process_frame
	room.movement_view = false
	room.get_node("FollowTarget/ScaleMarker").visible = false
	assert(room.actual_strip_lights.is_empty())
	assert(room.continuous_ready and room.baked_receivers.size() >= 129)
	var receiver_count := 0
	for mesh: MeshInstance3D in room.find_children("*", "MeshInstance3D", true, false):
		if mesh.get_active_material(0) is ShaderMaterial and mesh.get_active_material(0).shader.resource_path.ends_with("room1_baked_strip_receiver_r3.gdshader"):
			assert(mesh.mesh.surface_get_arrays(0)[Mesh.ARRAY_TEX_UV2].size() > 0)
			receiver_count += 1
	assert(receiver_count == 129)
	DirAccess.make_dir_recursive_absolute(OUTPUT)
	await capture("01_center.png")
	var wall_metrics := {}
	if DisplayServer.get_name() != "headless":
		var rendered := Image.load_from_file(OUTPUT + "01_center.png")
		wall_metrics["upper_wall"] = region_luminance(rendered, Rect2i(900, 75, 250, 40))
		wall_metrics["lower_wall"] = region_luminance(rendered, Rect2i(900, 235, 250, 40))
		assert(wall_metrics.upper_wall > wall_metrics.lower_wall)
	room.strip_on = false
	room.apply_sample_state()
	await capture("02_pods_only.png")
	room.windows_on = false
	room.screens_on = false
	room.apply_sample_state()
	await capture("03_all_off.png")
	room.strip_on = true
	room.apply_sample_state()
	await capture("04_strip_only.png")
	room.windows_on = true
	room.screens_on = true
	room.apply_sample_state()
	room.get_node("FollowTarget").position = Vector3(3.525, 0, -4.75)
	room.update_follow_camera()
	await capture("05_left.png")
	room.get_node("FollowTarget").position = room.EDGE_POSITIONS[2]
	room.update_follow_camera()
	await capture("06_right.png")
	room.get_node("FollowTarget").position = room.EDGE_POSITIONS[4]
	room.update_follow_camera()
	await capture("07_back.png")
	room.get_node("FollowTarget").position = room.START
	room.update_follow_camera()
	room.get_node("FollowTarget/ScaleMarker").visible = true
	await capture("08_marker.png")
	var differences := {}
	if DisplayServer.get_name() != "headless":
		differences["continuous_strip_contribution"] = difference("01_center.png", "02_pods_only.png")
		differences["strip_only_vs_off"] = difference("04_strip_only.png", "03_all_off.png")
		for value in differences.values():
			assert(value > 0.0001)
	var file := FileAccess.open(OUTPUT + "validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"engine": Engine.get_version_info().string, "strip_point_or_spot_lights": 0, "baked_meshes_with_uv2": receiver_count, "ambient_energy": room.room_ambient_energy, "baked_energy": room.continuous_baked_energy, "lit_ids": room.window_lit_pods, "readback": differences, "wall_gradient": wall_metrics, "scope": "Four continuous emitting surfaces baked with static geometry occlusion; dynamic shadow not implemented; local only; art review pending."}, "\t"))
	file.close()
	print("ROOM1_CONTINUOUS_PASS: ", JSON.stringify(differences))
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

func region_luminance(rendered: Image, region: Rect2i) -> float:
	var sum := 0.0
	var count := 0
	for y in range(region.position.y, region.end.y, 2):
		for x in range(region.position.x, region.end.x, 2):
			var color := rendered.get_pixel(x, y)
			sum += color.r * 0.2126 + color.g * 0.7152 + color.b * 0.0722
			count += 1
	return sum / count
