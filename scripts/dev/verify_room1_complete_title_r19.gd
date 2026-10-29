extends SceneTree

const TITLE_SCENE := "res://scenes/core/title_screen.tscn"
const FORMAL_ROOM_SCENE := "res://scenes/areas/military_facility/cryo_room_4f_01_3d.tscn"


func _initialize() -> void:
	call_deferred("run_checks")


func _frames(count: int) -> void:
	for _frame in count:
		await process_frame


func _physics_frames(count: int) -> void:
	for _frame in count:
		await physics_frame


func tap(action: StringName) -> void:
	var event := InputEventAction.new()
	event.action = action
	event.pressed = true
	Input.parse_input_event(event)
	await _frames(2)
	event = InputEventAction.new()
	event.action = action
	event.pressed = false
	Input.parse_input_event(event)
	await _frames(1)


func hold(action: StringName, frames: int) -> void:
	var event := InputEventAction.new()
	event.action = action
	event.pressed = true
	Input.parse_input_event(event)
	await _physics_frames(frames)
	event = InputEventAction.new()
	event.action = action
	event.pressed = false
	Input.parse_input_event(event)
	await _physics_frames(2)


func review_key(key: Key) -> void:
	var event := InputEventKey.new()
	event.pressed = true
	event.keycode = key
	event.physical_keycode = key
	Input.parse_input_event(event)
	await _frames(2)
	event = InputEventKey.new()
	event.pressed = false
	event.keycode = key
	event.physical_keycode = key
	Input.parse_input_event(event)
	await _frames(1)


func run_checks() -> void:
	assert(change_scene_to_file(TITLE_SCENE) == OK)
	await _frames(2)
	var title = current_scene
	assert(title.name == "TitleScreen")
	# The formal route must retain the pre-existing settings and hint toggle UI.
	title.settings_button.pressed.emit()
	assert(title.settings_menu.visible and not title.main_menu.visible)
	title.hint_check_box.button_pressed = false
	assert(not root.get_node("GameState").interaction_hints_enabled)
	title.back_button.pressed.emit()
	assert(title.main_menu.visible and not title.settings_menu.visible)

	title.start_button.pressed.emit()
	await _physics_frames(30)
	# The inherited opener is deferred from _ready, so include an idle frame
	# before asserting the dialogue UI rather than relying on physics timing.
	await _frames(2)
	var room = current_scene
	assert(room.scene_file_path == FORMAL_ROOM_SCENE)
	assert(bool(root.get_node("GameState").get_flag(&"room1_play_mode", false)))
	assert(not room.info.get_parent().visible)
	assert(room.review_ui.is_dialogue_open() and room.input_locked)

	# The inherited opening dialogue still uses Enter/dialogue_advance and releases input.
	await tap(&"dialogue_advance")
	await tap(&"dialogue_advance")
	assert(not room.review_ui.is_dialogue_open() and not room.input_locked)

	# The controller reads physical WASD state.  In headless CI its explicit
	# test vector exercises the same movement branch without claiming that an
	# InputEventAction mutates OS physical-key state.
	var start_position: Vector3 = room.player.global_position
	room.test_mode = true
	room.test_input = Vector2.RIGHT
	await _physics_frames(12)
	room.test_input = Vector2.ZERO
	room.test_mode = false
	assert(room.player.global_position.distance_to(start_position) > 0.02)

	# The existing P12 information-panel interaction remains reachable with E.
	room.teleport_player(Vector3(3.525, 0.05, -5.9))
	await _physics_frames(12)
	assert(room.player_near)
	await tap(&"interact")
	assert(room.review_ui.is_dialogue_open())
	await tap(&"dialogue_advance")
	await tap(&"dialogue_advance")
	assert(not room.review_ui.is_dialogue_open())

	# Escape/pause must still work in the formal scene.
	await tap(&"pause")
	assert(paused and room.review_ui.pause_menu.visible)
	room.review_ui.resume_button.pressed.emit()
	await _frames(2)
	assert(not paused and not room.review_ui.pause_menu.visible)

	# r19 inherits review shortcuts.  The formal wrapper must make all of these no-ops.
	var glow_before: Variant = room.get("door_glow_on")
	for key in [KEY_F1, KEY_F2, KEY_F3, KEY_F4, KEY_P, KEY_K, KEY_O, KEY_G]:
		await review_key(key)
		assert(current_scene == room)
		assert(not room.review_ui.is_modal_open())
		assert(not room.info.get_parent().visible)
	assert(room.get("door_glow_on") == glow_before)

	# Direct scene execution (F6) must receive the same play-mode guard.
	root.get_node("GameState").reset_demo_state()
	assert(change_scene_to_file(FORMAL_ROOM_SCENE) == OK)
	await _physics_frames(20)
	await _frames(2)
	room = current_scene
	assert(bool(root.get_node("GameState").get_flag(&"room1_play_mode", false)))
	assert(not room.info.get_parent().visible)

	print("PASS: r19 title route, F6 play mode, opening, movement, P12 interaction, pause, and review-key isolation")
	quit()
