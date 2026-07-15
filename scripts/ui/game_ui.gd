extends CanvasLayer

@onready var text_box = $TextBox
@onready var text_label = $TextBox/TextLabel

@onready var pause_button = $PauseButton
@onready var pause_overlay = $PauseOverlay
@onready var pause_menu = $PauseMenu
@onready var resume_button = $PauseMenu/ResumeButton
@onready var settings_button = $PauseMenu/SettingsButton
@onready var title_button = $PauseMenu/TitleButton

@onready var settings_panel = $SettingsPanel
@onready var hint_check_box = $SettingsPanel/HintCheckBox
@onready var volume_slider = $SettingsPanel/VolumeSlider
@onready var language_option = $SettingsPanel/LanguageOption
@onready var back_button = $SettingsPanel/BackButton

var fade_tween: Tween
var is_paused = false
var show_hint = true
var _message_version := 0
var _message_active := false
var _prompt_texts: Dictionary = {}
var _prompt_order: Array[int] = []


func _ready():
	pause_button.pressed.connect(_on_pause_button_pressed)
	resume_button.pressed.connect(_on_resume_button_pressed)
	settings_button.pressed.connect(_on_settings_button_pressed)
	title_button.pressed.connect(_on_title_button_pressed)

	hint_check_box.toggled.connect(_on_hint_check_box_toggled)
	volume_slider.value_changed.connect(_on_volume_slider_value_changed)
	language_option.item_selected.connect(_on_language_option_item_selected)
	back_button.pressed.connect(_on_back_button_pressed)

	text_box.visible = false
	pause_overlay.visible = false
	pause_menu.visible = false
	settings_panel.visible = false

	show_hint = GameState.interaction_hints_enabled
	hint_check_box.set_pressed_no_signal(show_hint)

	volume_slider.min_value = 0
	volume_slider.max_value = 100
	volume_slider.value = 80

	language_option.clear()
	language_option.add_item("日本語")
	language_option.add_item("中文")
	language_option.add_item("English")
	language_option.select(0)


func _process(_delta: float) -> void:
	if Input.is_action_just_pressed("pause"):
		toggle_pause()


func show_text(text: String, duration: float = 2.5) -> void:
	_message_version += 1
	var version := _message_version
	_message_active = true
	_stop_fade()
	_display_text(text)

	await get_tree().create_timer(duration).timeout
	if version != _message_version:
		return
	await _fade_out_message(version)


# Each interaction owns its prompt. Leaving one Area does not clear another Area's prompt.
func show_prompt(source: Node, text: String) -> void:
	var source_id := source.get_instance_id()
	_prompt_texts[source_id] = text
	_prompt_order.erase(source_id)
	_prompt_order.append(source_id)
	if not _message_active:
		_refresh_prompt()


func hide_prompt(source: Node) -> void:
	var source_id := source.get_instance_id()
	_prompt_texts.erase(source_id)
	_prompt_order.erase(source_id)
	if not _message_active:
		_refresh_prompt()


func hide_text() -> void:
	_message_version += 1
	_message_active = false
	_stop_fade()
	_refresh_prompt()


func _fade_out_message(version: int) -> void:
	_stop_fade()
	fade_tween = create_tween()
	fade_tween.tween_property(text_box, "modulate:a", 0.0, 0.5)
	await fade_tween.finished

	if version != _message_version:
		return
	_message_active = false
	fade_tween = null
	text_box.modulate.a = 1.0
	_refresh_prompt()


func _display_text(text: String) -> void:
	text_label.text = text
	text_box.visible = true
	text_box.modulate.a = 1.0


func _refresh_prompt() -> void:
	if _message_active:
		return

	while not _prompt_order.is_empty() and not _prompt_texts.has(_prompt_order.back()):
		_prompt_order.pop_back()

	if not show_hint or _prompt_order.is_empty():
		text_box.visible = false
		text_box.modulate.a = 1.0
		return

	_display_text(str(_prompt_texts[_prompt_order.back()]))


func _stop_fade() -> void:
	if fade_tween != null and is_instance_valid(fade_tween):
		fade_tween.kill()
	fade_tween = null


func toggle_pause() -> void:
	is_paused = !is_paused
	get_tree().paused = is_paused

	pause_overlay.visible = is_paused
	pause_menu.visible = is_paused
	settings_panel.visible = false

	if is_paused:
		pause_button.text = "▶"
	else:
		pause_button.text = "Ⅱ"


func _on_pause_button_pressed() -> void:
	toggle_pause()


func _on_resume_button_pressed() -> void:
	if is_paused:
		toggle_pause()


func _on_settings_button_pressed() -> void:
	pause_menu.visible = false
	settings_panel.visible = true


func _on_title_button_pressed() -> void:
	get_tree().paused = false
	is_paused = false
	get_tree().change_scene_to_file("res://scenes/core/title_screen.tscn")


func _on_back_button_pressed() -> void:
	settings_panel.visible = false
	pause_menu.visible = true


func _on_hint_check_box_toggled(button_pressed: bool):
	show_hint = button_pressed
	GameState.interaction_hints_enabled = button_pressed
	if not _message_active:
		_refresh_prompt()


func _on_volume_slider_value_changed(value: float):
	print("BGM Volume placeholder (not connected): ", value)


func _on_language_option_item_selected(index: int):
	var selected_language = language_option.get_item_text(index)
	print("Language placeholder (not connected): ", selected_language)
