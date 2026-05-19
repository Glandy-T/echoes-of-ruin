extends Node2D

@onready var ui = $UI
@onready var player = $Player

func _ready():
	var spawn = get_node_or_null(GameState.next_spawn_name)
	if spawn:
		player.global_position = spawn.global_position

func show_message(text: String, duration: float = 2.5):
	ui.show_text(text, duration)

func show_prompt(text: String):
	ui.show_prompt(text)

func hide_message():
	ui.hide_text()
