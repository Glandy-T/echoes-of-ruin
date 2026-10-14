extends SceneTree

const OUTPUT := "res://docs/art/experiments/room1_glow_sample_r1/"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var room := (load("res://scenes/dev/room1_glow_sample_r1.tscn") as PackedScene).instantiate()
	get_root().add_child(room)
	await process_frame
	assert(room.sample_ready and room.window_lit_pods == PackedStringArray(["P12"]))
	assert(not room.glass_materials["P12"].emission_enabled)
	assert(room.glass_materials["P12"].transparency == BaseMaterial3D.TRANSPARENCY_ALPHA)
	assert(not room.window_backers["P12"].visible)
	DirAccess.make_dir_recursive_absolute(OUTPUT)
	await capture("01_screen_glow.png")
	room.halo_on = false
	room.apply_sample_state()
	await capture("02_screen_no_glow.png")
	room.halo_on = true
	room._set_sample_view(2)
	room.apply_sample_state()
	await capture("03_window_glow.png")
	room.halo_on = false
	room.apply_sample_state()
	await capture("04_window_no_glow.png")
	room.halo_on = true
	room.local_light_on = false
	room.apply_sample_state()
	await capture("05_window_no_local_light.png")
	room.local_light_on = true
	room._set_sample_view(3)
	room.apply_sample_state()
	await capture("06_whole_pod.png")
	room._set_sample_view(4)
	await capture("07_room_preview.png")
	var results := {}
	if DisplayServer.get_name() != "headless":
		results["screen_glow_mean_difference"] = image_difference("01_screen_glow.png", "02_screen_no_glow.png")
		results["window_glow_mean_difference"] = image_difference("03_window_glow.png", "04_window_no_glow.png")
		results["interior_light_mean_difference"] = image_difference("03_window_glow.png", "05_window_no_local_light.png")
		assert(results.screen_glow_mean_difference > 0.0005, "Screen glow has no rendered effect")
		assert(results.window_glow_mean_difference > 0.0005, "Window glow has no rendered effect")
		assert(results.interior_light_mean_difference > 0.0005, "Interior light has no rendered effect")
	var file := FileAccess.open(OUTPUT + "validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"engine": Engine.get_version_info().string, "renderer": "gl_compatibility", "readback": results, "single_powered_pod": "P12", "screen_core_energy": room.screen_core_energy, "window_interior_light_energy": room.window_light_energy, "glass_emission": false, "old_window_backer_hidden": true, "glow_intensity": room.halo_intensity, "glow_threshold": room.halo_threshold, "scope": "Closeup fluorescence candidate; not art approval."}, "\t"))
	file.close()
	print("ROOM1_GLOW_SAMPLE_PASS: ", JSON.stringify(results))
	room.queue_free()
	quit()

func capture(filename: String) -> void:
	for frame in 12:
		await process_frame
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		assert(get_root().get_texture().get_image().save_png(OUTPUT + filename) == OK)

func image_difference(a: String, b: String) -> float:
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
