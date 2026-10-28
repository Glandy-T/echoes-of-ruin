extends SceneTree

func _initialize() -> void:
	call_deferred("run_checks")

func press(action: StringName) -> void:
	var event := InputEventAction.new()
	event.action = action
	event.pressed = true
	Input.parse_input_event(event)

func release(action: StringName) -> void:
	var event := InputEventAction.new()
	event.action = action
	event.pressed = false
	Input.parse_input_event(event)

func run_checks() -> void:
	var room = load("res://scenes/dev/room1_dialogue_adapter_review_r1.tscn").instantiate()
	root.add_child(room)
	for i in 30:
		await physics_frame
	assert(room.player_near)
	assert(room.review_ui.interaction_name_label.visible)
	press(&"interact")
	await process_frame
	await process_frame
	release(&"interact")
	assert(room.review_ui.is_dialogue_open() and room.input_locked)
	room.test_mode = true
	room.test_input = Vector2(-1, 0)
	var start: Vector3 = room.player.global_position
	await create_timer(0.5).timeout
	assert(Vector2(room.player.global_position.x - start.x, room.player.global_position.z - start.z).length() < 0.01)
	press(&"dialogue_advance")
	await process_frame
	await process_frame
	release(&"dialogue_advance")
	await process_frame
	assert(room.review_ui.is_dialogue_open())
	press(&"dialogue_advance")
	await process_frame
	await process_frame
	release(&"dialogue_advance")
	assert(not room.review_ui.is_dialogue_open() and not room.input_locked)
	await create_timer(0.5).timeout
	assert(start.distance_to(room.player.global_position) > 0.2)
	room.test_input = Vector2.ZERO
	room.teleport_player(room.interaction_area.global_position + Vector3(4, 0, 0))
	for i in 10:
		await physics_frame
	assert(not room.player_near and not room.review_ui.interaction_name_label.visible)
	print("PASS: Area3D entry/exit, prompt, E interaction, dialogue pages, movement lock and resume")
	quit()
