extends Control

# Temporary development target. The final flow will be:
# title -> opening/wake-up sequence -> first cryogenic room -> player control.
# Replace only this path after the formal opening scene is created.
const TEMPORARY_START_SCENE_PATH := "res://scenes/dev/prototype_room_a.tscn"
const WINDOWED_SIZE := Vector2i(1280, 720)
const DISPLAY_MODE_WINDOWED := 0
const DISPLAY_MODE_FULLSCREEN := 1

@onready var main_menu: VBoxContainer = $CenterContainer/MainMenu
@onready var settings_menu: VBoxContainer = $CenterContainer/SettingsMenu
@onready var start_button: Button = $CenterContainer/MainMenu/StartButton
@onready var settings_button: Button = $CenterContainer/MainMenu/SettingsButton
@onready var exit_button: Button = $CenterContainer/MainMenu/ExitButton
@onready var hint_check_box: CheckBox = $CenterContainer/SettingsMenu/SettingsGrid/HintCheckBox
@onready var display_mode_option: OptionButton = $CenterContainer/SettingsMenu/SettingsGrid/DisplayModeOption
@onready var back_button: Button = $CenterContainer/SettingsMenu/BackButton


func _ready() -> void:
	start_button.pressed.connect(_on_start_button_pressed)
	settings_button.pressed.connect(_on_settings_button_pressed)
	exit_button.pressed.connect(_on_exit_button_pressed)
	back_button.pressed.connect(_on_back_button_pressed)

	hint_check_box.set_pressed_no_signal(GameState.interaction_hints_enabled)
	display_mode_option.clear()
	display_mode_option.add_item("ウィンドウ", DISPLAY_MODE_WINDOWED)
	display_mode_option.add_item("フルスクリーン", DISPLAY_MODE_FULLSCREEN)
	display_mode_option.select(_get_current_display_mode_index())

	hint_check_box.toggled.connect(_on_hint_check_box_toggled)
	display_mode_option.item_selected.connect(_on_display_mode_selected)
	start_button.grab_focus()


func _unhandled_input(event: InputEvent) -> void:
	if settings_menu.visible and event.is_action_pressed("ui_cancel"):
		_show_main_menu()
		get_viewport().set_input_as_handled()


func _on_start_button_pressed() -> void:
	GameState.reset_demo_state()
	get_tree().change_scene_to_file(TEMPORARY_START_SCENE_PATH)


func _on_settings_button_pressed() -> void:
	main_menu.hide()
	settings_menu.show()
	hint_check_box.grab_focus()


func _on_exit_button_pressed() -> void:
	get_tree().quit()


func _on_hint_check_box_toggled(button_pressed: bool) -> void:
	GameState.interaction_hints_enabled = button_pressed


func _on_display_mode_selected(index: int) -> void:
	if index == DISPLAY_MODE_FULLSCREEN:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
		return

	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	call_deferred("_restore_windowed_size")


func _restore_windowed_size() -> void:
	DisplayServer.window_set_size(WINDOWED_SIZE)


func _get_current_display_mode_index() -> int:
	var current_mode := DisplayServer.window_get_mode()
	if current_mode == DisplayServer.WINDOW_MODE_FULLSCREEN or current_mode == DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN:
		return DISPLAY_MODE_FULLSCREEN
	return DISPLAY_MODE_WINDOWED


func _on_back_button_pressed() -> void:
	_show_main_menu()


func _show_main_menu() -> void:
	settings_menu.hide()
	main_menu.show()
	settings_button.grab_focus()
