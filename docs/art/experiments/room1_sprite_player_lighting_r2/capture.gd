extends SceneTree

const OUT := "res://docs/art/experiments/room1_sprite_player_lighting_r2/evidence/"
var room: Node3D

func _initialize() -> void:
	call_deferred("capture")

func shot(name: String) -> void:
	for i in 12:
		await process_frame
	await RenderingServer.frame_post_draw
	assert(get_root().get_texture().get_image().save_png(OUT + name + ".png") == OK)

func capture() -> void:
	room = load("res://scenes/dev/room1_sprite_player_lighting_r2.tscn").instantiate()
	get_root().add_child(room)
	for i in 30:
		await process_frame
	room.position_structure_review()
	room.info.get_parent().visible = false
	room.standard.set_open_immediate(true)
	room.teleport_player(Vector3(3.525, 0.01, -4.75))
	room.strip_on = true
	room.apply_sample_state()
	await shot("open_light_on")
	room.strip_on = false
	room.apply_sample_state()
	await shot("open_light_off")
	room.strip_on = true
	room.apply_sample_state()
	await shot("open_light_restored")
	var start: Vector3 = room.player.global_position
	room.test_mode = true
	room.test_input = Vector2(-1, 0)
	await create_timer(0.8).timeout
	await shot("walk_light_on")
	var walk := {"distance_m": start.distance_to(room.player.global_position), "walking": room.paper_walking, "texture": room.paper_hero.texture.resource_path, "frame": room.paper_hero.frame, "light_level": room.paper_light_level_at(room.player.global_position + Vector3(0, 0.825, 0))}
	assert(walk.walking and walk.texture.ends_with("walk.png") and walk.distance_m > 0.2)
	FileAccess.open(OUT + "readback.json", FileAccess.WRITE).store_string(JSON.stringify({
		"scene": room.scene_file_path,
		"light_model": "continuous_ribbon_position_approximation",
		"strip_on": room.paper_light_material.get_shader_parameter("strip_on"),
		"start_light_level": room.paper_light_level_at(start + Vector3(0, 0.825, 0)),
		"texture_filter": room.paper_hero.texture_filter,
		"walk": walk
	}, "\t"))
	quit()
