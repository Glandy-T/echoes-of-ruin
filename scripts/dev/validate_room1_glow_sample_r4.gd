extends SceneTree

const OUTPUT := "res://docs/art/experiments/room1_glow_sample_r4/"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var room := (load("res://scenes/dev/room1_glow_sample_r4.tscn") as PackedScene).instantiate()
	get_root().add_child(room)
	await process_frame
	assert(room.bloom_camera != null and room.blur_viewports.size() == 5)
	DirAccess.make_dir_recursive_absolute(OUTPUT)
	await capture("01_diffuse_glow.png")
	if DisplayServer.get_name() != "headless":
		assert(room.bloom_source.get_texture().get_image().save_png(OUTPUT + "09_source_mask.png") == OK)
		assert(room.blur_viewports[4].get_texture().get_image().save_png(OUTPUT + "10_far_halo.png") == OK)
	var display := room.get_node("Pods/P12").find_child("pod_v3_display", true, false) as MeshInstance3D
	var bounds := Rect2()
	for corner in 8:
		var point := (room.get_node("ReviewCamera") as Camera3D).unproject_position(display.global_transform * display.mesh.get_aabb().get_endpoint(corner))
		bounds = Rect2(point, Vector2.ZERO) if corner == 0 else bounds.expand(point)
	room.bloom_overlay.visible = false
	await capture("02_no_wide_halo.png")
	room.diffuse_on = false
	room.apply_sample_state()
	await capture("03_r3_comparison.png")
	room.diffuse_on = true
	room.halo_on = false
	room.apply_sample_state()
	await capture("04_no_glow.png")
	room.halo_on = true
	room.screens_on = false
	room.apply_sample_state()
	assert(not room.bloom_overlay.visible)
	await capture("05_screen_off.png")
	room.screens_on = true
	room.apply_sample_state()
	room._set_sample_view(2)
	await capture("06_glass.png")
	room._set_sample_view(3)
	await capture("07_whole_pod.png")
	room._set_sample_view(4)
	await capture("08_room.png")
	var differences := {}
	if DisplayServer.get_name() != "headless":
		differences["wide_halo"] = difference("01_diffuse_glow.png", "02_no_wide_halo.png")
		differences["new_vs_r3"] = difference("01_diffuse_glow.png", "03_r3_comparison.png")
		differences["all_glow"] = difference("01_diffuse_glow.png", "04_no_glow.png")
		differences["outside_screen_boundary"] = outside_difference(bounds)
		for value in differences.values():
			assert(value > 0.00005)
	var file := FileAccess.open(OUTPUT + "validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"engine": Engine.get_version_info().string, "readback": differences, "screen_power_controls_halo": true, "blur_passes": 4, "scope": "Screen-only two-scale Gaussian bloom with depth occluders and synchronized camera; glass seam deferred; local only; art review pending."}, "\t"))
	file.close()
	print("ROOM1_GLOW_R4_PASS: ", JSON.stringify(differences))
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

func outside_difference(bounds: Rect2) -> float:
	var first := Image.load_from_file(OUTPUT + "01_diffuse_glow.png")
	var second := Image.load_from_file(OUTPUT + "02_no_wide_halo.png")
	var inner := bounds.grow(4.0)
	var outer := bounds.grow(48.0)
	var total := 0.0
	var count := 0
	for y in range(140, first.get_height(), 2):
		for x in range(0, first.get_width(), 2):
			var point := Vector2(x, y)
			if outer.has_point(point) and not inner.has_point(point):
				var delta := first.get_pixel(x, y) - second.get_pixel(x, y)
				total += (absf(delta.r) + absf(delta.g) + absf(delta.b)) / 3.0
				count += 1
	return total / maxi(count, 1)
