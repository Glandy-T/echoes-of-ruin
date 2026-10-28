extends SceneTree

func _initialize() -> void:
	call_deferred("run_checks")

func run_checks() -> void:
	var state := root.get_node("GameState")
	state.reset_demo_state()
	var old_room = load("res://scenes/areas/military_facility/cryo_room_4f_01.tscn").instantiate()
	root.add_child(old_room)
	await process_frame
	await process_frame
	var ui = old_room.get_node("GameUI")
	var player = old_room.get_node("Player")
	var terminal = old_room.get_node("IdentityTerminal")
	var door = old_room.get_node("ExitDoor")
	assert(not door.opened and not terminal.used)
	terminal._activate()
	assert(terminal.used and door.opened and bool(state.get_flag(&"cryo_room_exit_authorized")))
	assert(ui.is_dialogue_open() and player.input_locked)
	ui.close_dialogue()
	assert(not player.input_locked)
	print("OLD: terminal opens door, stores runtime flag, dialogue locks/unlocks player")
	old_room.queue_free()
	await process_frame
	state.reset_demo_state()
	var room = load("res://scenes/dev/room1_sprite_player_lighting_r2.tscn").instantiate()
	root.add_child(room)
	for i in 10:
		await physics_frame
	room.teleport_player(Vector3(3.525, 0.05, -4.75))
	var start: Vector3 = room.player.global_position
	room.test_mode = true
	room.test_input = Vector2(-1, 0)
	await create_timer(0.8).timeout
	assert(room.paper_walking and room.paper_hero.texture.resource_path.ends_with("walk.png"))
	assert(start.distance_to(room.player.global_position) > 0.2)
	room.test_input = Vector2.ZERO
	await create_timer(0.5).timeout
	assert(not room.paper_walking and room.paper_hero.texture.resource_path.ends_with("idle.png"))
	room.strip_on = false
	room._sync_paper_lighting()
	assert(room.paper_light_material.get_shader_parameter("strip_on") == 0.0)
	room.strip_on = true
	room._sync_paper_lighting()
	assert(room.paper_light_material.get_shader_parameter("strip_on") == 1.0)
	print("NEW: movement, walk/idle transition, light toggle passed")
	quit()

