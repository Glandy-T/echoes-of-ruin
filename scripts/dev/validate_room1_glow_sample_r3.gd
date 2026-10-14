extends SceneTree

const OUTPUT := "res://docs/art/experiments/room1_glow_sample_r3/"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var room := (load("res://scenes/dev/room1_glow_sample_r3.tscn") as PackedScene).instantiate()
	get_root().add_child(room)
	await process_frame
	assert(room.soft_screen.shader.resource_path.ends_with("room1_screen_content_emission_r3.gdshader"))
	DirAccess.make_dir_recursive_absolute(OUTPUT)
	await capture("01_content_glow.png")
	room.content_emission_on = false
	room.apply_sample_state()
	await capture("02_old_frame_emission.png")
	room.content_emission_on = true
	room.gentler_spill_on = false
	room.apply_sample_state()
	await capture("03_old_spill.png")
	room.gentler_spill_on = true
	room.halo_on = false
	room.apply_sample_state()
	await capture("04_no_glow.png")
	room.halo_on = true
	room.local_light_on = false
	room.apply_sample_state()
	await capture("05_no_local_light.png")
	room.local_light_on = true
	room.apply_sample_state()
	room._set_sample_view(2)
	await capture("06_glass_unchanged.png")
	room._set_sample_view(3)
	await capture("07_whole_pod.png")
	var differences := {}
	if DisplayServer.get_name() != "headless":
		differences["content_emission"] = difference("01_content_glow.png", "02_old_frame_emission.png")
		differences["gentler_spill"] = difference("01_content_glow.png", "03_old_spill.png")
		differences["glow"] = difference("01_content_glow.png", "04_no_glow.png")
		differences["local_light"] = difference("01_content_glow.png", "05_no_local_light.png")
		for value in differences.values():
			assert(value > 0.00005)
	var file := FileAccess.open(OUTPUT + "validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"engine": Engine.get_version_info().string, "readback": differences, "scope": "Screen content emission and gentler local spill; glass seam deferred. Local only, art review pending."}, "\t"))
	file.close()
	print("ROOM1_GLOW_R3_PASS: ", JSON.stringify(differences))
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
