extends SceneTree

const OUT := "res://docs/art/experiments/room1_sprite_player_review_r1/evidence/"
var room: Node3D
var camera: Camera3D

func _initialize() -> void:
	call_deferred("capture")

func shot(name: String) -> void:
	for i in 12:
		await process_frame
	await RenderingServer.frame_post_draw
	assert(get_root().get_texture().get_image().save_png(OUT + name + ".png") == OK)

func capture() -> void:
	room = load("res://scenes/dev/room1_sprite_player_review_r1.tscn").instantiate()
	get_root().add_child(room)
	for i in 30:
		await process_frame
	room.position_structure_review()
	room.info.get_parent().visible = false
	camera = room.get_node("ReviewCamera") as Camera3D
	room.standard.set_open_immediate(true)
	room.teleport_player(Vector3(3.525, 0.01, -4.75))
	await shot("open_idle")
	var walk_start: Vector3 = room.player.global_position
	room.test_mode = true
	room.test_input = Vector2(-1, 0)
	await create_timer(0.8).timeout
	await shot("open_walk")
	var walk_end: Vector3 = room.player.global_position
	var walk_state: Dictionary = {
		"walking": room.paper_walking,
		"texture": room.paper_hero.texture.resource_path,
		"frame": room.paper_hero.frame,
		"hframes": room.paper_hero.hframes,
		"distance_m": walk_start.distance_to(walk_end)
	}
	assert(walk_state.walking and walk_state.texture.ends_with("walk.png") and walk_state.hframes == 6 and walk_state.distance_m > 0.2)
	room.test_input = Vector2.ZERO
	await create_timer(0.5).timeout
	await shot("open_idle_after_stop")
	var idle_after_stop: Dictionary = {
		"walking": room.paper_walking,
		"texture": room.paper_hero.texture.resource_path,
		"frame": room.paper_hero.frame,
		"hframes": room.paper_hero.hframes
	}
	assert(not idle_after_stop.walking and idle_after_stop.texture.ends_with("idle.png") and idle_after_stop.hframes == 4)
	room.test_mode = false
	room.standard.set_open_immediate(false)
	room.teleport_player(Vector3(3.525, 0.01, -4.75))
	await shot("closed_idle")
	FileAccess.open(OUT + "readback.json", FileAccess.WRITE).store_string(JSON.stringify({
		"scene": room.scene_file_path,
		"visible_height_m": room.CHARACTER_HEIGHT_M,
		"pixel_size": room.paper_hero.pixel_size,
		"sprite_position_y": room.paper_hero.position.y,
		"texture_filter": room.paper_hero.texture_filter,
		"billboard": room.paper_hero.billboard,
		"collision_height_m": room.player.get_child(0).shape.height,
		"actor_capsule_layer": room.actor_mesh.layers,
		"walk": {"start": walk_start, "end": walk_end, "state": walk_state},
		"idle_after_stop": idle_after_stop
	}, "\t"))
	quit()
