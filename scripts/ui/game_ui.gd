extends CanvasLayer

const EXPRESSION_IDS := [
	&"neutral",
	&"confused",
	&"wary",
	&"deadpan",
	&"surprised",
	&"sad",
	&"bitter_smile",
]

@onready var text_box: Panel = $TextBox
@onready var text_label: Label = $TextBox/TextLabel
@onready var interaction_name_label: Label = $InteractionNameLabel

@onready var detail_overlay: Control = $DetailOverlay
@onready var detail_texture_rect: TextureRect = $DetailOverlay/DetailTexture
@onready var dialogue_panel: Panel = $DialoguePanel
@onready var portrait_texture: TextureRect = $DialoguePanel/MarginContainer/HBoxContainer/PortraitFrame/PortraitTexture
@onready var dialogue_text: Label = $DialoguePanel/MarginContainer/HBoxContainer/TextArea/DialogueText

@onready var pause_button: Button = $PauseButton
@onready var pause_overlay: ColorRect = $PauseOverlay
@onready var pause_menu: Panel = $PauseMenu
@onready var resume_button: Button = $PauseMenu/ResumeButton
@onready var settings_button: Button = $PauseMenu/SettingsButton
@onready var title_button: Button = $PauseMenu/TitleButton

@onready var settings_panel: Panel = $SettingsPanel
@onready var hint_check_box: CheckBox = $SettingsPanel/HintCheckBox
@onready var volume_slider: HSlider = $SettingsPanel/VolumeSlider
@onready var language_option: OptionButton = $SettingsPanel/LanguageOption
@onready var back_button: Button = $SettingsPanel/BackButton

var fade_tween: Tween
var is_paused := false
var show_hint := true
var _message_version := 0
var _message_active := false
var _interaction_targets: Dictionary = {}
var _interaction_order: Array[int] = []

var _dialogue_open := false
var _dialogue_pages: Array[String] = []
var _dialogue_expression_ids: Array[StringName] = []
var _dialogue_page_index := 0
var _player: Node
var _expression_textures: Dictionary = {}
var _warned_expression_ids: Dictionary = {}


func _ready() -> void:
	pause_button.pressed.connect(_on_pause_button_pressed)
	resume_button.pressed.connect(_on_resume_button_pressed)
	settings_button.pressed.connect(_on_settings_button_pressed)
	title_button.pressed.connect(_on_title_button_pressed)

	hint_check_box.toggled.connect(_on_hint_check_box_toggled)
	volume_slider.value_changed.connect(_on_volume_slider_value_changed)
	language_option.item_selected.connect(_on_language_option_item_selected)
	back_button.pressed.connect(_on_back_button_pressed)

	text_box.visible = false
	interaction_name_label.visible = false
	detail_overlay.visible = false
	dialogue_panel.visible = false
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

	_player = get_tree().get_first_node_in_group("player")
	for expression_id in EXPRESSION_IDS:
		_expression_textures[expression_id] = portrait_texture.texture
	_refresh_interaction_name()


func _process(_delta: float) -> void:
	_update_interaction_name_position()


func _unhandled_input(event: InputEvent) -> void:
	if is_dialogue_open():
		if event.is_action_pressed("pause"):
			close_dialogue()
			get_viewport().set_input_as_handled()
		elif event.is_action_pressed("dialogue_advance"):
			_advance_dialogue()
			get_viewport().set_input_as_handled()
		return

	if not event.is_action_pressed("pause"):
		return

	if is_paused and settings_panel.visible:
		_show_pause_menu()
	else:
		toggle_pause()
	get_viewport().set_input_as_handled()


func start_dialogue(pages: Array[String], expression_ids: Array[StringName] = []) -> void:
	_open_dialogue(null, pages, expression_ids)


func start_detail_dialogue(
	detail_texture: Texture2D,
	pages: Array[String],
	expression_ids: Array[StringName] = []
) -> void:
	_open_dialogue(detail_texture, pages, expression_ids)


func close_dialogue() -> void:
	if not _dialogue_open:
		return

	_dialogue_open = false
	_dialogue_pages.clear()
	_dialogue_expression_ids.clear()
	_dialogue_page_index = 0
	dialogue_panel.visible = false
	detail_overlay.visible = false
	detail_texture_rect.texture = null
	pause_button.visible = true
	_set_player_input_locked(false)
	_refresh_interaction_name()


func is_dialogue_open() -> bool:
	return _dialogue_open


func is_modal_open() -> bool:
	return _dialogue_open or is_paused


func can_accept_world_interaction() -> bool:
	return not is_modal_open() and not get_tree().paused


func show_text(text: String, duration: float = 2.5) -> void:
	_message_version += 1
	var version := _message_version
	_message_active = true
	_stop_fade()
	_refresh_interaction_name()
	if not is_modal_open():
		_display_text(text)

	await get_tree().create_timer(duration).timeout
	if version != _message_version:
		return
	await _fade_out_message(version)


func show_interaction_name(
	source: Node,
	display_name: String,
	position_reference: Node2D,
	label_offset: Vector2
) -> void:
	var source_id := source.get_instance_id()
	_interaction_targets[source_id] = {
		"source": source,
		"display_name": display_name,
		"position_reference": position_reference,
		"label_offset": label_offset,
	}
	_interaction_order.erase(source_id)
	_interaction_order.append(source_id)
	_refresh_interaction_name()


func hide_interaction_name(source: Node) -> void:
	var source_id := source.get_instance_id()
	_interaction_targets.erase(source_id)
	_interaction_order.erase(source_id)
	_refresh_interaction_name()


func hide_text() -> void:
	_message_version += 1
	_message_active = false
	_stop_fade()
	_refresh_interaction_name()


func _open_dialogue(
	detail_texture: Texture2D,
	pages: Array[String],
	expression_ids: Array[StringName]
) -> void:
	if pages.is_empty():
		return
	if _dialogue_open:
		close_dialogue()

	_cancel_temporary_text()
	_dialogue_pages.append_array(pages)
	_dialogue_expression_ids.append_array(expression_ids)
	_dialogue_page_index = 0
	_dialogue_open = true

	detail_texture_rect.texture = detail_texture
	detail_overlay.visible = detail_texture != null
	dialogue_panel.visible = true
	pause_button.visible = false
	_set_player_input_locked(true)
	_refresh_interaction_name()
	_show_dialogue_page()


func _advance_dialogue() -> void:
	_dialogue_page_index += 1
	if _dialogue_page_index >= _dialogue_pages.size():
		close_dialogue()
		return
	_show_dialogue_page()


func _show_dialogue_page() -> void:
	dialogue_text.text = _dialogue_pages[_dialogue_page_index]
	var expression_id: StringName = &"neutral"
	if _dialogue_page_index < _dialogue_expression_ids.size():
		expression_id = _dialogue_expression_ids[_dialogue_page_index]
		if expression_id.is_empty():
			expression_id = &"neutral"
	_apply_expression(expression_id)


func _apply_expression(expression_id: StringName) -> void:
	var resolved_id := expression_id
	if not _expression_textures.has(resolved_id):
		if not _warned_expression_ids.has(resolved_id):
			push_warning("Unknown dialogue expression '%s'; using neutral." % resolved_id)
			_warned_expression_ids[resolved_id] = true
		resolved_id = &"neutral"
	portrait_texture.texture = _expression_textures[resolved_id]


func _cancel_temporary_text() -> void:
	_message_version += 1
	_message_active = false
	_stop_fade()
	text_box.visible = false
	text_box.modulate.a = 1.0
	_refresh_interaction_name()


func _set_player_input_locked(locked: bool) -> void:
	if _player == null or not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player")
	if _player == null:
		push_warning("GameUI could not find Player for dialogue input locking.")
		return
	if not _player.has_method("set_input_locked"):
		push_warning("Player does not implement set_input_locked().")
		return
	_player.call("set_input_locked", locked)


func _fade_out_message(version: int) -> void:
	_stop_fade()
	if not text_box.visible:
		_message_active = false
		_refresh_interaction_name()
		return

	fade_tween = create_tween()
	fade_tween.tween_property(text_box, "modulate:a", 0.0, 0.5)
	await fade_tween.finished

	if version != _message_version:
		return
	_message_active = false
	fade_tween = null
	text_box.modulate.a = 1.0
	_refresh_interaction_name()


func _display_text(text: String) -> void:
	text_label.text = text
	text_box.visible = true
	text_box.modulate.a = 1.0


func _refresh_interaction_name() -> void:
	while not _interaction_order.is_empty():
		var source_id: int = _interaction_order.back()
		if not _interaction_targets.has(source_id):
			_interaction_order.pop_back()
			continue
		var target: Dictionary = _interaction_targets[source_id]
		var source: Node = target.get("source")
		var position_reference: Node2D = target.get("position_reference")
		if is_instance_valid(source) and is_instance_valid(position_reference):
			break
		_interaction_targets.erase(source_id)
		_interaction_order.pop_back()

	if is_modal_open() or _message_active or not show_hint or _interaction_order.is_empty():
		interaction_name_label.visible = false
		return

	var current_target: Dictionary = _interaction_targets[_interaction_order.back()]
	var current_name := str(current_target.get("display_name", ""))
	if current_name.is_empty():
		interaction_name_label.visible = false
		return

	interaction_name_label.text = current_name
	interaction_name_label.reset_size()
	interaction_name_label.visible = true
	_update_interaction_name_position()


func _update_interaction_name_position() -> void:
	if not interaction_name_label.visible or _interaction_order.is_empty():
		return
	var source_id: int = _interaction_order.back()
	if not _interaction_targets.has(source_id):
		_refresh_interaction_name()
		return
	var target: Dictionary = _interaction_targets[source_id]
	var position_reference: Node2D = target.get("position_reference")
	if not is_instance_valid(position_reference):
		_refresh_interaction_name()
		return

	var screen_position: Vector2 = get_viewport().get_canvas_transform() * position_reference.global_position
	var label_offset: Vector2 = target.get("label_offset", Vector2.ZERO)
	var viewport_size := get_viewport().get_visible_rect().size
	var label_position := screen_position + label_offset - interaction_name_label.size * 0.5
	label_position.x = clampf(label_position.x, 0.0, maxf(0.0, viewport_size.x - interaction_name_label.size.x))
	label_position.y = maxf(0.0, label_position.y)
	interaction_name_label.position = label_position


func _stop_fade() -> void:
	if fade_tween != null and is_instance_valid(fade_tween):
		fade_tween.kill()
	fade_tween = null


func toggle_pause() -> void:
	if is_dialogue_open():
		return

	is_paused = not is_paused
	get_tree().paused = is_paused
	pause_overlay.visible = is_paused
	pause_menu.visible = is_paused
	settings_panel.visible = false

	if is_paused:
		pause_button.text = "▶"
		resume_button.grab_focus()
	else:
		pause_button.text = "Ⅱ"
	_refresh_interaction_name()


func _show_pause_menu() -> void:
	settings_panel.visible = false
	pause_menu.visible = true
	settings_button.grab_focus()
	_refresh_interaction_name()


func _on_pause_button_pressed() -> void:
	if not is_dialogue_open():
		toggle_pause()


func _on_resume_button_pressed() -> void:
	if is_paused:
		toggle_pause()


func _on_settings_button_pressed() -> void:
	pause_menu.visible = false
	settings_panel.visible = true
	hint_check_box.grab_focus()
	_refresh_interaction_name()


func _on_title_button_pressed() -> void:
	get_tree().paused = false
	is_paused = false
	get_tree().change_scene_to_file("res://scenes/core/title_screen.tscn")


func _on_back_button_pressed() -> void:
	_show_pause_menu()


func _on_hint_check_box_toggled(button_pressed: bool) -> void:
	show_hint = button_pressed
	GameState.interaction_hints_enabled = button_pressed
	_refresh_interaction_name()


func _on_volume_slider_value_changed(value: float) -> void:
	print("BGM Volume placeholder (not connected): ", value)


func _on_language_option_item_selected(index: int) -> void:
	var selected_language := language_option.get_item_text(index)
	print("Language placeholder (not connected): ", selected_language)
