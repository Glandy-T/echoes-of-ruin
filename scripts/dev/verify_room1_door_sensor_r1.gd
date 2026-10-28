extends SceneTree
func _initialize() -> void:
	call_deferred("run_checks")
func tap(action: StringName) -> void:
	var event := InputEventAction.new()
	event.action = action
	event.pressed = true
	Input.parse_input_event(event)
	await process_frame
	await process_frame
	event = InputEventAction.new()
	event.action = action
	event.pressed = false
	Input.parse_input_event(event)
	await process_frame
func run_checks() -> void:
	var room = load("res://scenes/dev/room1_door_sensor_review_r1.tscn").instantiate()
	root.add_child(room)
	for i in 20: await physics_frame
	assert(room.review_ui.is_dialogue_open() and room.input_locked)
	assert(room.review_ui.dialogue_text.text == "あ……頭、痛い……。")
	await tap(&"dialogue_advance")
	assert(room.review_ui.dialogue_text.text == "ここは……どこ？")
	await tap(&"dialogue_advance")
	assert(not room.review_ui.is_dialogue_open() and not room.input_locked)
	room._start_opening_dialogue()
	assert(not room.review_ui.is_dialogue_open())
	room.test_mode = true
	room.chip_enabled = false
	room.teleport_player(Vector3(10.5, 0.05, -7.7))
	await create_timer(0.5).timeout
	room.test_input = Vector2(0, -1)
	await create_timer(1.0).timeout
	var blocked_z: float = room.player.global_position.z
	assert(room.door_occupied and is_zero_approx(room.door_fraction) and blocked_z > -9.32)
	room.test_input = Vector2.ZERO
	room.chip_enabled = true
	await create_timer(0.7).timeout
	assert(room.scan_line.visible and room.scan_time > 0.0 and is_zero_approx(room.door_fraction))
	await create_timer(1.3).timeout
	assert(room.scan_complete and not room.scan_line.visible and room.door_fraction > 0.0 and room.door_fraction < 0.5)
	await create_timer(3.0).timeout
	assert(room.door_fraction > 0.99)
	assert(room.door_mesh.global_position.distance_to(room.door_body.global_position) < 0.001)
	assert(room.get_node("BlackDoorway") != null)
	room.test_input = Vector2(0, -1)
	await create_timer(0.6).timeout
	room.test_input = Vector2.ZERO
	assert(room.player.global_position.z > -9.4 and room._can_use_exit())
	await tap(&"interact")
	assert(room.is_inside_tree() and room.review_ui._message_active)
	room.review_ui.hide_text()
	room.chip_enabled = false
	await create_timer(0.4).timeout
	assert(room.door_occupied and room.door_fraction > 0.99)
	room.teleport_player(Vector3(10.5, 0.05, -5.5))
	await create_timer(4.3).timeout
	assert(not room.door_occupied and is_zero_approx(room.door_fraction))
	room.teleport_player(Vector3(3.525, 0.05, -5.9))
	await create_timer(0.5).timeout
	assert(room.player_near)
	assert(room.standard.screen_name == "グラン" and room.standard._screen_name_label.text == "NAME: グラン")
	var camera_before: Transform3D = room.get_node("ReviewCamera").global_transform
	await tap(&"interact")
	assert(room.review_ui.is_dialogue_open() and room.input_locked)
	assert(room.review_ui.detail_overlay.visible)
	assert(room.review_ui.detail_texture_rect.texture.resource_path == "res://assets/art/cryopod_standard_v8/cryopod_standard_v8_display.png")
	assert(room.review_ui.detail_texture_rect.material == null)
	assert(room.get_node("ReviewCamera").global_transform.is_equal_approx(camera_before))
	assert(room.review_ui.dialogue_text.text == "情報パネル……？")
	await tap(&"dialogue_advance")
	assert(room.review_ui.dialogue_text.text == "グラン……私の名前、みたい。")
	await tap(&"dialogue_advance")
	assert(not room.review_ui.is_dialogue_open() and not room.input_locked)
	assert(not room.review_ui.detail_overlay.visible)
	room.standard.set_screen_powered(false)
	await tap(&"interact")
	assert(not room.review_ui.is_dialogue_open() and room.review_ui._message_active)
	room.review_ui.hide_text()
	await create_timer(2.8).timeout
	print("PASS: opening dialogue, scan-before-open, slow door, blocked exit and own-pod dialogue")
	quit()

