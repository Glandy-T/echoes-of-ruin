extends SceneTree
const OUT := "res://docs/art/experiments/room1_pod_exit_animation_r3/"
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	var room: Node = load("res://scenes/dev/room1_pod_exit_animation_r3.tscn").instantiate()
	get_root().add_child(room)
	room.finish_exit()
	room.set_process(false)
	room.set_physics_process(false)
	room.info.get_parent().visible = false
	DirAccess.make_dir_recursive_absolute(OUT)
	var result := {}
	for id in ["P02", "P12", "P17"]:
		var pod := room.get_node("Pods/" + id) as Node3D
		var glass := pod.find_child("pod_v3_glass", true, false) as MeshInstance3D
		var point := glass.global_transform * glass.mesh.get_aabb().get_center()
		var camera := room.get_node("ReviewCamera") as Camera3D
		camera.position = point + Vector3(1.1, 0.9, 1.5)
		camera.look_at(point)
		room._sync_render_camera()
		room._sync_bloom_camera()
		room.windows_on = true
		room.apply_sample_state()
		var on := await capture(id + "_on.png")
		room.windows_on = false
		room.apply_sample_state()
		var off := await capture(id + "_off.png")
		var diff := difference(on, off, Vector2i(camera.unproject_position(point)), 120)
		assert(diff > 0.01)
		result[id + "_window_blue_difference"] = diff
	room.windows_on = true
	room.apply_sample_state()
	room.teleport_player(Vector3(3.525, 0, -4.75))
	room._sync_render_camera()
	room._sync_bloom_camera()
	var game_on := await capture("game_on.png")
	room.windows_on = false
	room.apply_sample_state()
	var game_off := await capture("game_off.png")
	var front_glass := room.get_node("Pods/P02").find_child("pod_v3_glass", true, false) as MeshInstance3D
	var front_point := front_glass.global_transform * front_glass.mesh.get_aabb().get_center()
	var game_diff := difference(game_on, game_off, Vector2i(room.get_node("ReviewCamera").unproject_position(front_point)), 60)
	assert(game_diff > 0.01)
	result["game_P02_blue_difference"] = game_diff
	assert(room.interior_window_materials.size() == 3)
	assert(room.window_lit_pods.size() == 3)
	for id in room.interior_window_materials:
		assert(room.room_glass_shaders[id].shader == room.room_glass_shaders.P02.shader)
		assert(room.room_glass_shaders[id].get_shader_parameter("chamber_powered") == 0.0)
		for mat in room.interior_window_materials[id]:
			assert(mat.shader == room.interior_window_materials.P02[0].shader)
	for material in room.interior_window_materials.P02:
		assert(material.get_shader_parameter("window_powered") == 0.0)
	assert(room.room_glass_shaders.P02.get_shader_parameter("chamber_powered") == 0.0)
	result["glass_transmission_follows_window_switch"] = true
	result["window_materials_P02_P12_P17"] = true
	result["three_lit_pods_preserved"] = true
	result["all_three_share_glass_and_interior_shaders"] = true
	result["method"] = "Local interior irradiance plus transparent glass transmitted-radiance approximation; existing shadowed spill retained"
	FileAccess.open(OUT + "validation.json", FileAccess.WRITE).store_string(JSON.stringify(result, "\t"))
	print("WINDOW_R3_PASS ", JSON.stringify(result))
	quit()
func capture(name: String) -> Image:
	for frame in 15:
		await process_frame
	await RenderingServer.frame_post_draw
	var img := get_root().get_texture().get_image()
	assert(img.save_png(OUT + name) == OK)
	return img
func difference(a: Image, b: Image, center: Vector2i, radius: int) -> float:
	var value := 0.0
	var count := 0
	for y in range(maxi(0, center.y-radius), mini(a.get_height(), center.y+radius)):
		for x in range(maxi(0, center.x-radius), mini(a.get_width(), center.x+radius)):
			value += maxf(a.get_pixel(x,y).b-b.get_pixel(x,y).b, 0)
			count += 1
	return value / maxf(count, 1)
