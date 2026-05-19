extends Area2D

var player_near = false
@onready var main = get_parent()

func _process(_delta):
	if player_near and Input.is_action_just_pressed("interact"):
		GameState.next_spawn_name = "DoorSpawn"
		get_tree().change_scene_to_file("res://Main.tscn")

func _on_body_entered(body):
	if body.name == "Player":
		player_near = true
		main.show_prompt("Eキーで戻る")

func _on_body_exited(body):
	if body.name == "Player":
		player_near = false
		main.hide_message()
