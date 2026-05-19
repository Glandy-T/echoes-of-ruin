extends Control

func _ready():
	$StartButton.pressed.connect(_on_start_button_pressed)

func _on_start_button_pressed():
	GameState.next_spawn_name = "StartSpawn"

	GameState.main_terminal_used = false
	GameState.main_door_opened = false

	get_tree().change_scene_to_file("res://Main.tscn")
