extends SceneTree
const OUTPUT := "res://docs/art/experiments/room1_left_wall_uv_review_r4/"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var room: Node = (load("res://scenes/dev/room1_left_wall_uv_review_r4.tscn") as PackedScene).instantiate()
	get_root().add_child(room)
	room.test_mode = true
	await process_frame
	assert(room.pixel_mode == 0)
	room.set_pixel_mode(2)
	assert(room.pixel_mode == 0)
	var fixed: Array = room.fixed_left_mesh.surface_get_arrays(1)
	var old: Array = room.previous_left_mesh.surface_get_arrays(1)
	assert(fixed[Mesh.ARRAY_VERTEX] == old[Mesh.ARRAY_VERTEX])
	var maximum_uv2_delta := 0.0
	assert(fixed[Mesh.ARRAY_TEX_UV2].size() == old[Mesh.ARRAY_TEX_UV2].size())
	for index in fixed[Mesh.ARRAY_TEX_UV2].size():
		maximum_uv2_delta = maxf(maximum_uv2_delta, fixed[Mesh.ARRAY_TEX_UV2][index].distance_to(old[Mesh.ARRAY_TEX_UV2][index]))
	# Godot packs color/lightmap UVs using a shared quantization range.
	assert(maximum_uv2_delta < 0.0001)
	for uv: Vector2 in fixed[Mesh.ARRAY_TEX_UV]:
		assert(uv.x > -0.0001 and uv.x < 1.0001 and uv.y > -0.0001 and uv.y < 1.0001)
	DirAccess.make_dir_recursive_absolute(OUTPUT)
	room.teleport_player(room.EDGE_POSITIONS[1] + Vector3(0, 0.05, 0))
	await capture("01_left_fixed.png")
	room.left_uv_fixed = false
	room.apply_left_uv_state()
	await capture("02_left_before.png")
	room.left_uv_fixed = true
	room.apply_left_uv_state()
	room.teleport_player(room.EDGE_POSITIONS[2] + Vector3(0, 0.05, 0))
	await capture("03_right_reference.png")
	room.teleport_player(room.START + Vector3(0, 0.05, 0))
	await capture("04_center.png")
	# Equal-distance straight-on views separate UV thickness from perspective.
	room.set_physics_process(false)
	room.set_process(false)
	room.info.get_parent().visible = false
	var camera := room.get_node("ReviewCamera") as Camera3D
	camera.position = Vector3(6.0, 1.7, -4.75)
	camera.look_at(Vector3(0.2, 1.7, -4.75))
	room._sync_render_camera()
	room._sync_bloom_camera()
	await capture("05_left_front_on_fixed.png")
	room.left_uv_fixed = false
	room.apply_left_uv_state()
	await capture("06_left_front_on_before.png")
	room.left_uv_fixed = true
	room.apply_left_uv_state()
	camera.position = Vector3(15.0, 1.7, -4.75)
	camera.look_at(Vector3(20.8, 1.7, -4.75))
	room._sync_render_camera()
	room._sync_bloom_camera()
	await capture("07_right_front_on_reference.png")
	var result := {"color_uv_corrected_to_0_1": true, "geometry_identical": true, "lightmap_uv2_layout_preserved": true, "godot_uv2_quantization_delta": maximum_uv2_delta, "native_resolution_locked": true}
	var file := FileAccess.open(OUTPUT + "validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(result, "\t"))
	file.close()
	print("ROOM1_LEFT_UV_PASS: ", JSON.stringify(result))
	quit()

func capture(filename: String) -> void:
	for frame in 30:
		await process_frame
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		assert(get_root().get_texture().get_image().save_png(OUTPUT + filename) == OK)
