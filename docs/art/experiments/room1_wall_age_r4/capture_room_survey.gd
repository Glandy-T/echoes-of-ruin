extends SceneTree

const OUT := "res://docs/art/experiments/room1_wall_age_r4/survey/"
var room: Node
var camera: Camera3D
var records: Array = []

func _initialize() -> void:
	call_deferred("capture")

func _shot(name: String, kind: String) -> void:
	room._sync_render_camera()
	room._sync_bloom_camera()
	for _frame in 15:
		await process_frame
	await RenderingServer.frame_post_draw
	var image := get_root().get_texture().get_image()
	assert(image.save_png(OUT + name + ".png") == OK)
	var wall_material: ShaderMaterial = room.structure_materials["Wall_left"][0]
	records.append({"file": name + ".png", "kind": kind, "size": [image.get_width(), image.get_height()], "camera_position": [camera.global_position.x, camera.global_position.y, camera.global_position.z], "camera_basis": str(camera.global_transform.basis), "fov": camera.fov, "age_variant": room.age_variant, "age_label": "r4_moderate_strength_aging" if room.age_variant == 1 else "r3_light_aging", "wall_map": (wall_material.get_shader_parameter("wall_structure_map") as Texture2D).resource_path, "floor_map": "res://assets/art/room1_surface_structure_r2/floor_sample.png", "base_color_preview": room.base_color_mode})

func capture() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	room = load("res://scenes/dev/room1_wall_age_r4.tscn").instantiate()
	get_root().add_child(room)
	for _frame in 15:
		await process_frame
	room.position_structure_review()
	room.set_process(false)
	room.set_physics_process(false)
	room.info.get_parent().visible = false
	room.set_base_color_mode(false)
	room.set_age_variant(1)
	camera = room.get_node("ReviewCamera") as Camera3D

	var index := 0
	for z in [-3.4, -5.75]:
		for x in [3.525, 10.5, 17.475]:
			room.teleport_player(Vector3(x, 0.0, z))
			index += 1
			await _shot("%02d_game" % index, "Unchanged gameplay camera; left/centre/right in both pod rows")

	var front := room.get_node("Shell").find_child("Wall_front", true, false) as MeshInstance3D
	var original_visible := front.visible
	var original_shadow := front.cast_shadow
	var corners := [["07_rear_left", Vector3(3.8, 2.4, -5.7), Vector3(0.2, 1.5, -9.3), false], ["08_rear_right", Vector3(17.2, 2.4, -5.7), Vector3(20.8, 1.5, -9.3), false], ["09_front_left", Vector3(3.8, 2.4, -3.8), Vector3(0.2, 1.5, -0.2), true], ["10_front_right", Vector3(17.2, 2.4, -3.8), Vector3(20.8, 1.5, -0.2), true], ["11_door", Vector3(10.5, 2.0, -5.2), Vector3(10.5, 1.45, -9.3), false]]
	for view in corners:
		front.visible = bool(view[3]) or original_visible
		front.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if bool(view[3]) else original_shadow
		camera.global_position = view[1]
		camera.look_at(view[2], Vector3.UP)
		camera.fov = 55.0
		await _shot(view[0], "Temporary technical inspection camera; front wall is actually shown only for front-corner inspection")
		front.visible = original_visible
		front.cast_shadow = original_shadow

	for view in [["12_overview_front", Vector3(10.5, 15.0, -1.0), Vector3(10.5, 0.0, -4.75)], ["13_overview_rear", Vector3(10.5, 15.0, -8.5), Vector3(10.5, 0.0, -4.75)]]:
		camera.global_position = view[1]
		camera.look_at(view[2], Vector3.UP)
		camera.fov = 70.0
		await _shot(view[0], "Temporary technical overview; all 20 pods and continuous floor coverage, not gameplay camera")

	FileAccess.open(OUT + "capture_record.json", FileAccess.WRITE).store_string(JSON.stringify({"scene": "room1_wall_age_r4.tscn", "geometry": room.baked_geometry_path, "irradiance": room.irradiance_path, "scope": "Six gameplay views, four corners, door and two complete-pod overviews. r4 moderate-strength aging is limited to the left-wall source patch; front wall is explicitly shown in both front-corner checks.", "captures": records}))
	print("ROOM1_WALL_AGE_R4_SURVEY_COMPLETE", records.size())
	quit()
