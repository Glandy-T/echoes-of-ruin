extends SceneTree
func _initialize() -> void:
	call_deferred("capture")
func shot(name: String) -> void:
	for i in 15: await process_frame
	await RenderingServer.frame_post_draw
	var path := "res://docs/art/experiments/room1_door_sensor_r1/evidence/" + name + ".png"
	if root.get_texture().get_image().save_png(path) != OK:
		push_error("Could not write " + path)
		quit(1)
func capture() -> void:
	var room = load("res://scenes/dev/room1_door_sensor_review_r1.tscn").instantiate()
	root.add_child(room)
	for i in 30: await process_frame
	room.info.get_parent().visible = false
	room.review_ui.pause_button.visible = false
	assert(room.review_ui.is_dialogue_open())
	await shot("opening_1")
	room.review_ui._advance_dialogue()
	await shot("opening_2")
	room.review_ui.close_dialogue()
	room.chip_enabled = false
	room.teleport_player(Vector3(10.5, 0.05, -7.7))
	await create_timer(0.5).timeout
	await shot("closed")
	room.chip_enabled = true
	await create_timer(0.7).timeout
	await shot("scan")
	await create_timer(4.4).timeout
	await shot("open")
	room.teleport_player(Vector3(3.525, 0.05, -5.9))
	await create_timer(0.5).timeout
	var event := InputEventAction.new()
	event.action = &"interact"
	event.pressed = true
	Input.parse_input_event(event)
	for i in 10: await process_frame
	assert(room.review_ui.is_dialogue_open())
	await shot("own_pod_dialogue")
	room.review_ui._advance_dialogue()
	await shot("own_pod_dialogue_2")
	var panel_image: Image = room.standard.get_screen_overlay_texture().get_image()
	assert(panel_image.save_png("res://docs/art/experiments/room1_door_sensor_r1/evidence/pod_panel_text.png") == OK)
	print("Saved door and dialogue gameplay views")
	quit()

