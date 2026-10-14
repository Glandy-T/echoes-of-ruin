extends SceneTree

const OUTPUT := "res://docs/art/experiments/room1_glow_sample_r2/"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var room := (load("res://scenes/dev/room1_glow_sample_r2.tscn") as PackedScene).instantiate()
	get_root().add_child(room)
	await process_frame
	assert(room.get_node("Pods/P12").find_child("pod_v3_glass", true, false).get_active_material(0) == room.pixel_glass)
	assert(room.get_node("Pods/P12").find_child("pod_v3_display", true, false).get_active_material(0) == room.soft_screen)
	DirAccess.make_dir_recursive_absolute(OUTPUT)
	await capture("01_screen_soft_glow.png")
	room.halo_on = false
	room.apply_sample_state()
	await capture("02_screen_no_glow.png")
	room.halo_on = true
	room._set_sample_view(2)
	room.apply_sample_state()
	await capture("03_pixel_glass.png")
	room.reflection_on = false
	room.apply_sample_state()
	await capture("04_glass_no_pixel_marks.png")
	room.reflection_on = true
	room.local_light_on = false
	room.apply_sample_state()
	await capture("05_glass_no_interior_light.png")
	room.local_light_on = true
	room._set_sample_view(3)
	room.apply_sample_state()
	await capture("06_whole_pod.png")
	room._set_sample_view(4)
	await capture("07_room_preview.png")
	var differences := {}
	if DisplayServer.get_name() != "headless":
		differences["screen_glow"] = difference("01_screen_soft_glow.png", "02_screen_no_glow.png")
		differences["pixel_reflections"] = difference("03_pixel_glass.png", "04_glass_no_pixel_marks.png")
		differences["interior_visible_light"] = difference("03_pixel_glass.png", "05_glass_no_interior_light.png")
		for value in differences.values():
			assert(value > 0.0005)
	var file := FileAccess.open(OUTPUT + "validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"engine": Engine.get_version_info().string, "actual_shader_overrides": true, "readback": differences, "scope": "Pixel marks coexist with transparency; screen emission edge attenuated. Art review pending. Local only, per user."}, "\t"))
	file.close()
	print("ROOM1_GLOW_R2_PASS: ", JSON.stringify(differences))
	room.queue_free()
	quit()

func capture(filename: String) -> void:
	for frame in 12:
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
