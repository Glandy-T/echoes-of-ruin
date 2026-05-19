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

	hint_check_box.button_pressed = true

	volume_slider.min_value = 0
	volume_slider.max_value = 100
	volume_slider.value = 80

	language_option.clear()
	language_option.add_item("日本語")
	language_option.add_item("中文")
	language_option.add_item("English")
	language_option.select(0)


func _process(_delta):
	if Input.is_action_just_pressed("pause"):
		toggle_pause()


func show_text(text: String, duration: float = 2.5):
	if fade_tween:
		fade_tween.kill()

	text_label.text = text
	text_box.visible = true
	text_box.modulate.a = 1.0

	await get_tree().create_timer(duration).timeout
	fade_out()


func show_prompt(text: String):
	if not show_hint:
		return

	if fade_tween:
		fade_tween.kill()

	text_label.text = text
	text_box.visible = true
	text_box.modulate.a = 1.0


func fade_out():
	if fade_tween:
		fade_tween.kill()

	fade_tween = create_tween()
	fade_tween.tween_property(text_box, "modulate:a", 0.0, 0.5)

	await fade_tween.finished
	text_box.visible = false
	text_box.modulate.a = 1.0


func hide_text():
	if fade_tween:
		fade_tween.kill()

	text_box.visible = false
	text_box.modulate.a = 1.0


func toggle_pause():
	is_paused = !is_paused
	get_tree().paused = is_paused

	pause_overlay.visible = is_paused
	pause_menu.visible = is_paused
	settings_panel.visible = false

	if is_paused:
		pause_button.text = "▶"
	else:
		pause_button.text = "Ⅱ"


func _on_pause_button_pressed():
	toggle_pause()


func _on_resume_button_pressed():
	if is_paused:
		toggle_pause()


func _on_settings_button_pressed():
	pause_menu.visible = false
	settings_panel.visible = true


func _on_title_button_pressed():
	get_tree().paused = false
	is_paused = false
	get_tree().change_scene_to_file("res://TitleScreen.tscn")


func _on_back_button_pressed():
	settings_panel.visible = false
	pause_menu.visible = true


func _on_hint_check_box_toggled(button_pressed: bool):
	show_hint = button_pressed

	if not show_hint:
		hide_text()


func _on_volume_slider_value_changed(value: float):
	print("BGM Volume: ", value)


func _on_language_option_item_selected(index: int):
	var selected_language = language_option.get_item_text(index)
	print("Language selected: ", selected_language)
