extends SceneTree

func _initialize() -> void:
	call_deferred("capture")

func shot(name: String) -> void:
	for i in 12: await process_frame
	await RenderingServer.frame_post_draw
	var path := "res://docs/art/experiments/room1_door_sensor_r1/evidence/" + name + ".png"
	assert(root.get_texture().get_image().save_png(path) == OK)

func capture() -> void:
	assert(change_scene_to_file("res://scenes/core/title_screen.tscn") == OK)
	for i in 20: await process_frame
	await shot("title")
	var title = current_scene
	title.settings_button.pressed.emit()
	await shot("title_settings")
	title._on_display_mode_selected(1)
	for i in 10: await process_frame
	assert(DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN)
	title._on_display_mode_selected(0)
	for i in 10: await process_frame
	assert(DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_WINDOWED)
	title.back_button.pressed.emit()
	title.start_button.pressed.emit()
	for i in 40: await process_frame
	var room = current_scene
	assert(room.review_ui.is_dialogue_open())
	room.review_ui.close_dialogue()
	room.review_ui.toggle_pause()
	await shot("pause_menu")
	room.review_ui.settings_button.pressed.emit()
	await shot("pause_settings")
	room.review_ui.toggle_pause()
	print("Saved title and pause views; fullscreen and windowed modes checked")
	quit()

