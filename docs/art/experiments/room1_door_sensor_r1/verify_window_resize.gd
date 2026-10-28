extends SceneTree

func _initialize() -> void:
	call_deferred("run_checks")

func verify_size(size: Vector2i, label: String) -> void:
	DisplayServer.window_set_size(size)
	for i in 30: await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	var actual: Vector2i = DisplayServer.window_get_size()
	assert(actual == size)
	assert(absf(float(image.get_width()) / image.get_height() - 16.0 / 9.0) < 0.01)
	var fit := minf(size.x / 1280.0, size.y / 720.0)
	assert(absf(image.get_width() - 1280.0 * fit) <= 2.0)
	assert(absf(image.get_height() - 720.0 * fit) <= 2.0)
	assert(image.save_png("res://docs/art/experiments/room1_door_sensor_r1/evidence/resize_" + label + ".png") == OK)
	print(label, ": window=", actual, ", game=", image.get_size())

func run_checks() -> void:
	assert(not DisplayServer.window_get_flag(DisplayServer.WINDOW_FLAG_RESIZE_DISABLED))
	assert(change_scene_to_file("res://scenes/core/title_screen.tscn") == OK)
	for i in 20: await process_frame
	await verify_size(Vector2i(960, 540), "title_small")
	current_scene.start_button.pressed.emit()
	for i in 40: await process_frame
	assert(current_scene.review_ui.is_dialogue_open())
	await verify_size(Vector2i(1600, 900), "room_large")
	await verify_size(Vector2i(1024, 768), "room_letterbox")
	assert(current_scene.review_ui.dialogue_panel.visible)
	DisplayServer.window_set_size(Vector2i(1280, 720))
	print("PASS: resizable window, proportional title, room and dialogue")
	quit()

