extends SceneTree

func _initialize() -> void:
	call_deferred("run_checks")

func run_checks() -> void:
	var room = load("res://scenes/dev/room1_door_embedded_review_r2.tscn").instantiate()
	root.add_child(room)
	for i in 20:
		await physics_frame
	assert(room.embedded_door_root != null)
	assert(room.door_mesh.name == "EmbeddedDoorSlab")
	assert(room.door_body.name == "EmbeddedDoorBodyR2")
	assert(not room.original_door_mesh.visible)
	assert(room.original_door_body.collision_layer == 0)
	assert(room.embedded_door_root.get_node("EmbeddedDoorSlab/InsetFace") != null)
	assert(room.door_mesh.global_position.distance_to(room.door_body.global_position) < 0.001)
	room.review_ui.close_dialogue()
	var toggle := InputEventKey.new()
	toggle.physical_keycode = KEY_L
	toggle.pressed = true
	room._unhandled_key_input(toggle)
	await process_frame
	assert(not room.strip_on)
	room._unhandled_key_input(toggle)
	await process_frame
	assert(room.strip_on)
	room.test_mode = true
	room.chip_enabled = true
	room.teleport_player(Vector3(10.5, 0.05, -7.7))
	await create_timer(2.0).timeout
	assert(room.scan_complete and room.door_fraction > 0.0)
	var start_x: float = room.door_closed_position.x
	await create_timer(3.0).timeout
	assert(room.door_fraction > 0.99)
	assert(is_equal_approx(room.door_mesh.global_position.x, start_x + room.OPEN_DISTANCE))
	assert(room.door_mesh.global_position.distance_to(room.door_body.global_position) < 0.001)
	room.teleport_player(Vector3(10.5, 0.05, -5.5))
	await create_timer(4.3).timeout
	assert(is_zero_approx(room.door_fraction))
	assert(is_equal_approx(room.door_mesh.global_position.x, start_x))
	print("PASS: r2 embedded door replaces hidden placeholder; recognition, slide, collision reference and close cycle verified")
	quit()
