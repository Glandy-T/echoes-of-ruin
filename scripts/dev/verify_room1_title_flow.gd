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
	assert(change_scene_to_file("res://scenes/core/title_screen.tscn") == OK)
	await process_frame
	await process_frame
	var title = current_scene
	assert(title.name == "TitleScreen")
	title.settings_button.pressed.emit()
	assert(title.settings_menu.visible and not title.main_menu.visible)
	title.hint_check_box.button_pressed = false
	assert(not root.get_node("GameState").interaction_hints_enabled)
	title.back_button.pressed.emit()
	assert(title.main_menu.visible and not title.settings_menu.visible)
	title.start_button.pressed.emit()
	for i in 30: await physics_frame
	var room = current_scene
	assert(room.scene_file_path == "res://scenes/areas/military_facility/cryo_room_4f_01_3d.tscn")
	assert(room.review_ui.is_dialogue_open() and room.input_locked)
	assert(not room.info.get_parent().visible)
	assert(not room.review_ui.show_hint)
	await tap(&"dialogue_advance")
	await tap(&"dialogue_advance")
	assert(not room.review_ui.is_dialogue_open() and not room.input_locked)
	room.teleport_player(Vector3(3.525, 0.05, -5.9))
	for i in 12: await physics_frame
	assert(room.player_near and not room.review_ui.interaction_name_label.visible)
	await tap(&"pause")
	assert(paused and room.review_ui.pause_menu.visible)
	room.review_ui.settings_button.pressed.emit()
	assert(room.review_ui.settings_panel.visible)
	room.review_ui.hint_check_box.button_pressed = true
	assert(root.get_node("GameState").interaction_hints_enabled)
	room.review_ui.back_button.pressed.emit()
	room.review_ui.resume_button.pressed.emit()
	await process_frame
	assert(not paused and room.review_ui.interaction_name_label.visible)
	await tap(&"pause")
	assert(paused)
	room.review_ui.title_button.pressed.emit()
	await process_frame
	await process_frame
	assert(not paused and current_scene.name == "TitleScreen")
	assert(current_scene.hint_check_box.button_pressed)
	current_scene.start_button.pressed.emit()
	for i in 20: await physics_frame
	assert(current_scene.review_ui.is_dialogue_open())
	print("PASS: title settings, start, opening, hints, pause, settings, resume, return to title, restart")
	quit()
