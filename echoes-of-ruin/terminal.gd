extends Area2D

@export var door_path: NodePath
@onready var door = get_node(door_path)
@onready var main = get_parent()

var player_near = false
var used = false


func _ready():
	used = GameState.main_terminal_used


func _process(_delta):
	if player_near and Input.is_action_just_pressed("interact"):
		if used:
			main.show_message("端末はすでに認証済みです。")
			return

		used = true
		GameState.main_terminal_used = true

		main.show_message("端末を起動した。生体反応を確認。認証完了。")
		door.unlock_and_open()


func _on_body_entered(body):
	if body.name == "Player":
		player_near = true
		main.show_prompt("Eキーで調べる")


func _on_body_exited(body):
	if body.name == "Player":
		player_near = false
		main.hide_message()
